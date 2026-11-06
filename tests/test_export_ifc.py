"""`export` to .ifc: the part tree as an IFC4 project, at the current pose, in metres.

The file is read back with a parser of its own, here: IFC is a STEP physical file, and
the suite takes nothing beyond bpy. What is checked is what a reader needs — the spatial
structure above the parts, a proxy per mesh and an assembly per group, the breps in
metres and Z up still facing out, the look on each one, and the ids unique and well
formed — and that `.rvt`, which only Revit writes, names this format instead.
"""
import re
import tempfile
import unittest
from pathlib import Path

import sand3d as s3d
from sand3d import _core
from sand3d.ifcfile import _B64

ENTITY = re.compile(r"^#(\d+)=([A-Z0-9]+)\((.*)\);$", re.M)


def split(text):
    """`text` at its top-level commas: nested lists and quoted strings stay whole."""
    out, depth, cur, i = [], 0, [], 0
    while i < len(text):
        ch = text[i]
        if ch == "'":                                   # a string: '' inside it is one quote
            cur.append(ch)
            i += 1
            while i < len(text):
                cur.append(text[i])
                if text[i] == "'":
                    if text[i + 1:i + 2] == "'":
                        cur.append(text[i + 1])
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if ch in "()":
            depth += 1 if ch == "(" else -1
        if ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    out.append("".join(cur))
    return out


def unquote(s):
    """An IFC string back to text: '' back to one quote, `\\X2\\…\\X0\\` back to its
    characters."""
    s, out, i = s[1:-1], [], 0
    while i < len(s):
        if s.startswith("\\X2\\", i):
            end = s.index("\\X0\\", i)
            digits = s[i + 4:end]
            units = [int(digits[k:k + 4], 16) for k in range(0, len(digits), 4)]
            out.append(b"".join(u.to_bytes(2, "big") for u in units).decode("utf-16-be"))
            i = end + 4
        elif s.startswith("''", i) or s.startswith("\\\\", i):
            out.append(s[i])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


class Ifc:
    """A parsed IFC file: its entities by reference, and the parts with their geometry."""

    def __init__(self, path):
        self.text = Path(path).read_text()
        self.head, _, body = self.text.partition("DATA;")
        self.by_ref, self.of_kind = {}, {}
        for ref, kind, args in ENTITY.findall(body):
            entity = (kind, split(args))
            self.by_ref["#" + ref] = entity
            self.of_kind.setdefault(kind, []).append(("#" + ref, entity[1]))

    def kind(self, name):
        return self.of_kind.get(name, [])

    def name(self, ref):
        return unquote(self.by_ref[ref][1][2])

    def guids(self):
        """Every id the file roots an entity on, in the order written."""
        return [unquote(args[0]) for _, (kind, args) in sorted(self.by_ref.items(), key=lambda kv: int(kv[0][1:]))
                if args and args[0].startswith("'") and len(unquote(args[0])) == 22
                and kind.startswith(("IFCREL", "IFCPROJECT", "IFCSITE", "IFCBUILDING", "IFCELEMENT"))]

    def shell(self, ref):
        """The points and the triangles of a product's faceted brep."""
        shape = self.by_ref[ref][1][6]
        rep = split(self.by_ref[shape][1][2][1:-1])[0]
        kind, args = self.by_ref[rep]
        assert kind == "IFCSHAPEREPRESENTATION", kind
        assert unquote(args[1]) == "Body" and unquote(args[2]) == "Brep", args[1:3]
        brep = split(args[3][1:-1])[0]
        closed = self.by_ref[brep][1][0]
        assert self.by_ref[closed][0] == "IFCCLOSEDSHELL"
        tris = []
        for face in split(self.by_ref[closed][1][0][1:-1]):
            bound = split(self.by_ref[face][1][0][1:-1])[0]
            bkind, bargs = self.by_ref[bound]
            assert bkind == "IFCFACEOUTERBOUND" and bargs[1] == ".T."
            loop = self.by_ref[bargs[0]]
            assert loop[0] == "IFCPOLYLOOP"
            tris.append([tuple(float(c) for c in split(self.by_ref[p][1][0][1:-1]))
                         for p in split(loop[1][0][1:-1])])
        return tris

    def parts(self):
        """name -> its triangles, for every proxy in the file."""
        return {self.name(ref): self.shell(ref) for ref, _ in self.kind("IFCBUILDINGELEMENTPROXY")}

    def label(self, ref, i=2):
        """The string at `i` of an entity: a product's name is its third, a style's first."""
        return unquote(self.by_ref[ref][1][i])

    def refs(self, args, i):
        """The references in the list at `i`."""
        return split(args[i][1:-1])

    def aggregates(self):
        """A parent reference -> what it aggregates, by name — keyed by reference, because
        a project and the root assembly under it go by the same name."""
        return {args[4]: [self.name(k) for k in self.refs(args, 5)]
                for _, args in self.kind("IFCRELAGGREGATES")}

    def under(self, ref):
        """What `ref` aggregates, by name."""
        return sorted(self.aggregates().get(ref, []))

    def only(self, kind):
        """The one entity of `kind`: its reference."""
        got = self.kind(kind)
        assert len(got) == 1, f"{len(got)} {kind}"
        return got[0][0]


def volume(tris):
    """Signed volume of closed triangles: positive when they face out."""
    total = 0.0
    for a, b, c in tris:
        total += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                  + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return total


def machine():
    s3d.empty_scene()
    cab = s3d.box("cab", 600, 600, 850)
    door = s3d.at(s3d.cylinder("door", 420, 30), on=cab.face("+X").move(z=400))
    s3d.joint("door_hinge", door, s3d.bbox(cab, "+X-Y"), axis="-Z", range=(0, 143))
    twin = s3d.transform(s3d.copy(door), mirror="y")
    return s3d.group("washer", cab, door, twin), cab, door, twin


def triangles(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


class ExportIfc(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def write(self, root, name="washer.ifc"):
        s3d.export(root, self.tmp / name)
        return Ifc(self.tmp / name)

    def test_the_header_names_ifc4_and_carries_no_clock(self):
        root, *_ = machine()
        ifc = self.write(root)
        self.assertTrue(ifc.text.startswith("ISO-10303-21;\n"))
        self.assertTrue(ifc.text.rstrip().endswith("END-ISO-10303-21;"))
        self.assertIn("FILE_SCHEMA(('IFC4'));", ifc.head)
        self.assertIn("'washer.ifc'", ifc.head)
        self.assertIn("'1970-01-01T00:00:00'", ifc.head)     # a fixed stamp: two runs, one file

    def test_the_spatial_structure_a_reader_expects(self):
        root, *_ = machine()
        ifc = self.write(root)
        for kind in ("IFCPROJECT", "IFCSITE", "IFCBUILDING", "IFCBUILDINGSTOREY", "IFCELEMENTASSEMBLY"):
            self.assertEqual(len(ifc.kind(kind)), 1, kind)
        self.assertEqual(ifc.name(ifc.kind("IFCPROJECT")[0][0]), "washer")
        units = [a[1] for _, a in ifc.kind("IFCSIUNIT")]
        self.assertEqual(units, [".LENGTHUNIT.", ".AREAUNIT.", ".VOLUMEUNIT.", ".PLANEANGLEUNIT."])
        self.assertEqual([a[3] for _, a in ifc.kind("IFCSIUNIT")][0], ".METRE.")
        # the project holds the site, the site the building, the building the storey
        self.assertEqual(ifc.under(ifc.only("IFCPROJECT")), ["Site"])
        self.assertEqual(ifc.under(ifc.only("IFCSITE")), ["Building"])
        self.assertEqual(ifc.under(ifc.only("IFCBUILDING")), ["Storey"])
        self.assertEqual(ifc.under(ifc.only("IFCBUILDINGSTOREY")), [])

    def test_every_mesh_is_a_proxy_under_the_root_assembly_in_the_storey(self):
        root, *_ = machine()
        ifc = self.write(root)
        self.assertEqual(sorted(ifc.parts()), ["cab", "door", "door_2"])
        assembly = ifc.only("IFCELEMENTASSEMBLY")
        self.assertEqual(ifc.name(assembly), "washer")
        self.assertEqual(ifc.under(assembly), ["cab", "door", "door_2"])
        # the assembly alone sits in the storey: IFC places an aggregated part once
        storey = ifc.kind("IFCRELCONTAINEDINSPATIALSTRUCTURE")
        self.assertEqual(len(storey), 1)
        self.assertEqual(ifc.refs(storey[0][1], 4), [assembly])
        self.assertEqual(storey[0][1][5], ifc.only("IFCBUILDINGSTOREY"))

    def test_a_group_under_a_group_is_an_assembly_under_an_assembly(self):
        s3d.empty_scene()
        inner = s3d.group("inner", s3d.box("a", 10, 10, 10), s3d.cylinder("b", 8, 4))
        root = s3d.group("outer", inner, s3d.box("c", 5, 5, 5))
        ifc = self.write(root, "nested.ifc")
        self.assertEqual(len(ifc.kind("IFCELEMENTASSEMBLY")), 2)
        self.assertEqual(sorted(ifc.parts()), ["a", "b", "c"])
        by_name = {ifc.name(ref): ref for ref, _ in ifc.kind("IFCELEMENTASSEMBLY")}
        self.assertEqual(ifc.under(by_name["outer"]), ["c", "inner"])
        self.assertEqual(ifc.under(by_name["inner"]), ["a", "b"])

    def test_the_breps_are_the_meshes_at_the_pose_in_metres_z_up_facing_out(self):
        root, cab, door, twin = machine()
        s3d.pose(door, 70)
        ifc = self.write(root)
        parts = ifc.parts()
        self.assertEqual(len(parts["cab"]), triangles(cab))
        for axis, lo, hi in ((0, -0.3, 0.3), (1, -0.3, 0.3), (2, 0.0, 0.85)):      # Z stays up
            corners = [c[axis] for tri in parts["cab"] for c in tri]
            self.assertAlmostEqual(min(corners), lo, places=6)
            self.assertAlmostEqual(max(corners), hi, places=6)
        m = _core.world(door)
        posed = [m @ v.co for v in door.data.vertices]                              # the current pose
        got = [c for tri in parts["door"] for c in tri]
        self.assertAlmostEqual(max(c[0] for c in got), max(p.x for p in posed) / 1000, places=6)
        self.assertAlmostEqual(max(c[1] for c in got), max(p.y for p in posed) / 1000, places=6)
        for name, tris in parts.items():
            self.assertGreater(volume(tris), 0, f"{name} faces in")                 # the mirror too

    def test_the_points_of_a_mesh_are_shared_not_repeated(self):
        s3d.empty_scene()
        box = s3d.box("b", 10, 10, 10)
        ifc = self.write(box, "box.ifc")
        self.assertEqual(len(ifc.kind("IFCCARTESIANPOINT")), len(box.data.vertices) + 1)   # + the origin
        self.assertEqual(len(ifc.kind("IFCFACE")), triangles(box))

    def test_the_unit_becomes_metres(self):
        s3d.empty_scene()
        s3d.units("cm")
        try:
            ifc = self.write(s3d.group("thing", s3d.box("b", 1, 1, 1)), "thing.ifc")
            xs = [c[0] for tri in ifc.parts()["b"] for c in tri]
            self.assertAlmostEqual(max(xs) - min(xs), 0.01, places=9)
        finally:
            s3d.empty_scene()
            s3d.units("mm")

    def test_a_mesh_root_needs_no_group(self):
        s3d.empty_scene()
        ifc = self.write(s3d.box("plate", 80, 40, 6), "plate.ifc")
        self.assertEqual(sorted(ifc.parts()), ["plate"])
        self.assertEqual(ifc.kind("IFCELEMENTASSEMBLY"), [])
        self.assertEqual(len(ifc.kind("IFCRELCONTAINEDINSPATIALSTRUCTURE")), 1)

    def test_the_looks_become_styles_and_materials(self):
        root, cab, door, twin = machine()
        s3d.material(cab, "brushed_steel")
        s3d.material(door, "glass")
        s3d.material(twin, "plastic", opacity=0.4)
        ifc = self.write(root)
        styles = {ifc.label(ref, 0): args for ref, args in ifc.kind("IFCSURFACESTYLE")}
        self.assertEqual(sorted(styles), ["brushed_steel", "glass", "plastic opacity=0.4"])
        self.assertEqual(sorted(ifc.label(r, 0) for r, _ in ifc.kind("IFCMATERIAL")), sorted(styles))
        shading = {name: ifc.by_ref[ifc.refs(args, 2)[0]][1] for name, args in styles.items()}
        self.assertEqual(shading["brushed_steel"][8], ".METAL.")
        self.assertEqual(shading["glass"][8], ".GLASS.")
        self.assertAlmostEqual(float(shading["brushed_steel"][1]), 0.0, places=6)
        self.assertAlmostEqual(float(shading["glass"][1]), 0.85, places=6)       # clear, never invisible
        self.assertAlmostEqual(float(shading["plastic opacity=0.4"][1]), 0.6, places=6)
        self.assertEqual(len(ifc.kind("IFCSTYLEDITEM")), 3)
        worn = {ifc.name(k) for _, args in ifc.kind("IFCRELASSOCIATESMATERIAL") for k in ifc.refs(args, 4)}
        self.assertEqual(worn, {"cab", "door", "door_2"})

    def test_a_part_with_no_look_carries_no_style(self):
        root, cab, *_ = machine()
        s3d.material(cab, "oak")
        ifc = self.write(root)
        self.assertEqual(len(ifc.kind("IFCSTYLEDITEM")), 1)
        self.assertEqual(len(ifc.kind("IFCSURFACESTYLE")), 1)

    def test_no_material_at_all_writes_no_style(self):
        root, *_ = machine()
        ifc = self.write(root)
        self.assertEqual(ifc.kind("IFCSTYLEDITEM"), [])
        self.assertEqual(ifc.kind("IFCSURFACESTYLE"), [])
        self.assertEqual(ifc.kind("IFCRELASSOCIATESMATERIAL"), [])

    def test_the_ids_are_unique_and_what_ifc_takes(self):
        root, cab, *_ = machine()
        s3d.material(cab, "oak")
        ifc = self.write(root)
        guids = ifc.guids()
        self.assertGreaterEqual(len(guids), 9)
        self.assertEqual(len(set(guids)), len(guids), "two entities share an id")
        for g in guids:
            self.assertEqual(len(g), 22)
            self.assertTrue(all(c in _B64 for c in g), g)
            self.assertLess(_B64.index(g[0]), 4, "the first character of an id holds two bits")

    def test_the_same_program_writes_the_same_file(self):
        """Nothing of the moment goes in: the same program, built again, writes the bytes
        again — what a dataset of programs and their exports needs."""
        written = []
        for run in ("a", "b"):
            root, cab, *_ = machine()
            s3d.material(cab, "brass")
            s3d.export(root, self.tmp / f"again_{run}.ifc")
            written.append((self.tmp / f"again_{run}.ifc").read_text().replace(f"again_{run}", "again"))
        self.assertEqual(written[0], written[1])

    def test_a_name_in_any_script_survives(self):
        s3d.empty_scene()
        root = s3d.group("bøx'ü", s3d.box("rød-1", 10, 10, 10))
        ifc = self.write(root, "unicode.ifc")
        self.assertIn("\\X2\\", ifc.text)                       # escaped, not written raw
        self.assertEqual(sorted(ifc.parts()), ["rød-1"])
        self.assertEqual(ifc.name(ifc.kind("IFCPROJECT")[0][0]), "bøx'ü")

    def test_revit_formats_name_ifc_instead(self):
        root, *_ = machine()
        for suffix in (".rvt", ".rfa", ".rte", ".rft"):
            with self.assertRaises(ValueError) as caught:
                s3d.export(root, self.tmp / f"x{suffix}")
            message = str(caught.exception)
            self.assertIn(suffix, message)
            self.assertIn("Revit", message)
            self.assertIn(".ifc", message)

    def test_a_format_sand3d_does_not_write_lists_ifc(self):
        root, *_ = machine()
        with self.assertRaises(ValueError) as caught:
            s3d.export(root, self.tmp / "x.3dm")
        self.assertIn(".ifc", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
