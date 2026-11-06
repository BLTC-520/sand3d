"""IFC4: the part tree under a root as an IFC project, at the current pose, in metres.

`export(root, "x.ifc")` writes IFC4 as a STEP physical file (ISO 10303-21, ISO 16739) —
the open standard Revit, ArchiCAD, Tekla and Solibri open and link, and the only one
that carries a part tree together with its geometry and what each part is made of.
Revit's own `.rvt` is written by Revit alone, so `export` names this file for it.

The tree: an `IfcProject`, with the `IfcSite`, `IfcBuilding` and `IfcBuildingStorey`
every reader expects to find above a product, and under the storey the root — an
`IfcElementAssembly` where it groups anything, each group under it another, every mesh
an `IfcBuildingElementProxy`, the generic product a reader shows as a solid of its own.
Groups nest through `IfcRelAggregates`; only the root sits in the storey, through
`IfcRelContainedInSpatialStructure`, as IFC wants an aggregated part placed once.

The geometry: an `IfcFacetedBrep` per mesh, in a `Body` shape representation — Blender's
triangles in one `IfcClosedShell`, each an `IfcFace` over an `IfcPolyLoop`, the points
shared inside the mesh (a reader that fans a concave face itself gets it wrong, so the
faces are the triangles). World coordinates, at the current pose, in metres, Z up. Every
placement is the identity and the pose is baked into the points: a mirror image has no
`IfcAxis2Placement3D` — IFC frames are right-handed — and the OBJ and the STL bake it
the same way.

What `material` set: an `IfcMaterial` named after the preset, associated with the parts
wearing it, and an `IfcSurfaceStyle` on the brep carrying the colour, the transparency
and a reflectance method read off the look — `.METAL.` for a metal, `.GLASS.` for
something transmissive. One of each per distinct look, in the order met.

IFC has one number for how far through a surface a reader sees, where the look has two,
so the clearer of them wins: `1 - opacity`, or most of `transmission`. Multiplying them
as the GLB and the USDA do would put plain `glass` at 1, and a reader draws nothing at
all at 1 — while `opacity=0` still does mean invisible, as `material` says it does.

No joint: IFC says no mechanism, so the file is the pose it was written at — the URDF
and the USDA carry the joints. No timestamp either, and the ids are digests of the
names rather than chance, so two runs of a program write the same bytes, as they do for
every other format sand3d writes.
"""
import hashlib
import os

from . import _core, materials
from .meshfile import _triangles
from .urdf import _Names, _clean

#: The alphabet of an IfcGloballyUniqueId, in IFC's order.
_B64 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"

#: How a look's reflectance reads in IFC, by what sets it apart.
_METHOD = (("transmission", ".GLASS."), ("metallic", ".METAL."), ("sheen", ".MATT."), ("coat", ".PHONG."))


def _guid(key):
    """`key` as an `IfcGloballyUniqueId`: IFC's 22-character compression of a UUID — one
    byte in the first two characters, then three in every four. A digest of the key, not
    chance, so a program that is run twice writes the same file twice; every caller spells
    its own kind into the key, because two entities with one id is not a valid file."""
    b = bytearray(hashlib.sha256(key.encode()).digest()[:16])
    b[6] = (b[6] & 0x0F) | 0x40                 # what a reader decompresses is a version-4 UUID
    b[8] = (b[8] & 0x3F) | 0x80
    out = [_B64[b[0] >> 6], _B64[b[0] & 63]]
    for i in range(1, 16, 3):
        n = (b[i] << 16) | (b[i + 1] << 8) | b[i + 2]
        out += [_B64[(n >> 6 * k) & 63] for k in (3, 2, 1, 0)]
    return "'" + "".join(out) + "'"


def _real(v):
    """A number as a STEP REAL, which always carries a point: `0.`, not `0`, and
    `1.E-5`, not `1e-05`."""
    s = f"{_clean(v):.9g}"
    if "e" in s:
        mantissa, exponent = s.split("e")
        return f"{mantissa if '.' in mantissa else mantissa + '.'}E{int(exponent)}"
    return s if "." in s else s + "."


def _text(s):
    """`s` as a STEP string: single-quoted, its own quotes and backslashes doubled, and
    anything outside printable ASCII in IFC's `\\X2\\` escape — a part is named by the
    program, in whatever script it likes."""
    out, run = [], []

    def flush():
        if run:
            out.append("\\X2\\" + "".join(f"{u:04X}" for u in run) + "\\X0\\")
            run.clear()

    for ch in s:
        if 0x20 <= ord(ch) <= 0x7E:
            flush()
            out.append("''" if ch == "'" else "\\\\" if ch == "\\" else ch)
        else:
            raw = ch.encode("utf-16-be")
            run.extend(int.from_bytes(raw[i:i + 2], "big") for i in range(0, len(raw), 2))
    flush()
    return "'" + "".join(out) + "'"


def _refs(items):
    return "(" + ",".join(items) + ")"


class _Step:
    """The DATA section: an entity to a line, numbered as it is written."""

    def __init__(self):
        self.lines = []

    def __call__(self, kind, *args):
        ref = len(self.lines) + 1
        self.lines.append(f"#{ref}={kind}({','.join(args)});")
        return f"#{ref}"


def write_ifc(root, path):
    from . import __version__
    step = _Step()
    names = _Names()
    title = _core.given_name(root)

    org = step("IFCORGANIZATION", "$", _text("sand3d"), "$", "$", "$")
    who = step("IFCPERSONANDORGANIZATION", step("IFCPERSON", "$", "$", _text("sand3d"),
                                                "$", "$", "$", "$", "$"), org, "$")
    app = step("IFCAPPLICATION", org, _text(__version__), _text("sand3d"), _text("sand3d"))
    owner = step("IFCOWNERHISTORY", who, app, "$", ".ADDED.", "$", "$", "$", "0")

    units = step("IFCUNITASSIGNMENT", _refs([
        step("IFCSIUNIT", "*", ".LENGTHUNIT.", "$", ".METRE."),
        step("IFCSIUNIT", "*", ".AREAUNIT.", "$", ".SQUARE_METRE."),
        step("IFCSIUNIT", "*", ".VOLUMEUNIT.", "$", ".CUBIC_METRE."),
        step("IFCSIUNIT", "*", ".PLANEANGLEUNIT.", "$", ".RADIAN."),
    ]))

    here = step("IFCAXIS2PLACEMENT3D", step("IFCCARTESIANPOINT", "(0.,0.,0.)"), "$", "$")
    model = step("IFCGEOMETRICREPRESENTATIONCONTEXT", "$", _text("Model"), "3", _real(1e-5), here, "$")
    body = step("IFCGEOMETRICREPRESENTATIONSUBCONTEXT", _text("Body"), _text("Model"),
                "*", "*", "*", "*", model, "$", ".MODEL_VIEW.", "$")

    def placed(under):
        return step("IFCLOCALPLACEMENT", under, here)

    at_site = placed("$")
    at_building = placed(at_site)
    at_storey = placed(at_building)

    def spatial(kind, name, at, *tail):
        return step(kind, _guid(f"{kind}:{title}"), owner, _text(name), "$", "$", at, "$", "$", ".ELEMENT.", *tail)

    site = spatial("IFCSITE", "Site", at_site, "$", "$", "$", "$", "$")
    building = spatial("IFCBUILDING", "Building", at_building, "$", "$", "$")
    storey = spatial("IFCBUILDINGSTOREY", "Storey", at_storey, "0.")
    project = step("IFCPROJECT", _guid(f"project:{title}"), owner, _text(title), "$", "$", "$", "$",
                   _refs([model]), units)

    looks, wearers, under = {}, {}, {}

    def style(tag):
        """The `IfcSurfaceStyle` of a look, and its `IfcMaterial`: one of each per look."""
        if tag not in looks:
            v = materials.look(tag)
            rgb = materials._linear(v["color"])[:3]
            colour = step("IFCCOLOURRGB", "$", *(_real(c) for c in rgb))
            clear = max(1 - v["opacity"], 0.85 * v["transmission"])
            method = next((m for key, m in _METHOD if v[key]), ".NOTDEFINED.")
            shading = step("IFCSURFACESTYLERENDERING", colour, _real(clear), colour, "$", "$", "$", "$",
                           f"IFCSPECULARROUGHNESS({_real(v['roughness'])})", method)
            name = materials._name(tag)
            looks[tag] = (step("IFCSURFACESTYLE", _text(name), ".BOTH.", _refs([shading])),
                          step("IFCMATERIAL", _text(name), "$", "$"))
        return looks[tag]

    def product(ob, kind, *tail):
        """`ob` as an IFC product of `kind`: its brep where it is a mesh, its look on both
        the geometry (a style) and the product (a material), and its reference."""
        name = names.unique("element", _core.given_name(ob))
        tag = materials._nearest(ob)
        shape = "$"
        if ob.type == "MESH":
            verts, tris = _triangles(ob, y_up=False)
            points = [step("IFCCARTESIANPOINT", "(" + ",".join(_real(c) for c in v) + ")") for v in verts]
            faces = [step("IFCFACE", _refs([step("IFCFACEOUTERBOUND",
                                                 step("IFCPOLYLOOP", _refs([points[i] for i in t])), ".T.")]))
                     for t in tris]
            brep = step("IFCFACETEDBREP", step("IFCCLOSEDSHELL", _refs(faces)))
            shape = step("IFCPRODUCTDEFINITIONSHAPE", "$", "$", _refs([
                step("IFCSHAPEREPRESENTATION", body, _text("Body"), _text("Brep"), _refs([brep]))]))
            if tag is not None:
                step("IFCSTYLEDITEM", brep, _refs([style(tag)[0]]), "$")
        ref = step(kind, _guid(f"element:{name}"), owner, _text(name), "$", "$", placed(at_storey), shape, "$", *tail)
        if tag is not None:
            wearers.setdefault(tag, []).append(ref)
        return ref

    def walk(ob, top=False):
        """`ob` as a product — a mesh a proxy, anything that groups an assembly — and its
        children under it; nothing, where nothing under it has geometry."""
        kids = [r for r in (walk(c) for c in sorted(ob.children, key=lambda c: c.name)) if r is not None]
        if ob.type == "MESH":
            ref = product(ob, "IFCBUILDINGELEMENTPROXY", ".ELEMENT.")
        elif kids or top:
            ref = product(ob, "IFCELEMENTASSEMBLY", ".FACTORY.", ".NOTDEFINED.")
        else:
            return None
        if kids:
            under[ref] = kids
        return ref

    top = walk(root, top=True)

    def rel(kind, key, *tail):
        return step(kind, _guid(key), owner, "$", "$", *tail)

    rel("IFCRELAGGREGATES", f"aggregates:project:{title}", project, _refs([site]))
    rel("IFCRELAGGREGATES", f"aggregates:site:{title}", site, _refs([building]))
    rel("IFCRELAGGREGATES", f"aggregates:building:{title}", building, _refs([storey]))
    rel("IFCRELCONTAINEDINSPATIALSTRUCTURE", f"contains:storey:{title}", _refs([top]), storey)
    for parent, kids in under.items():
        rel("IFCRELAGGREGATES", f"aggregates:parts:{parent}", parent, _refs(kids))
    for tag, parts in wearers.items():
        rel("IFCRELASSOCIATESMATERIAL", f"material:{materials._name(tag)}", _refs(parts), looks[tag][1])

    path = os.fspath(path)
    head = [
        "ISO-10303-21;",
        "HEADER;",
        "FILE_DESCRIPTION(('ViewDefinition [DesignTransferView_V1.0]'),'2;1');",
        f"FILE_NAME({_text(os.path.basename(path))},'1970-01-01T00:00:00',({_text('sand3d')}),"
        f"({_text('sand3d')}),{_text('sand3d ' + __version__)},{_text('sand3d')},'');",
        "FILE_SCHEMA(('IFC4'));",
        "ENDSEC;",
        "DATA;",
    ]
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(head + step.lines + ["ENDSEC;", "END-ISO-10303-21;"]) + "\n")
    return path
