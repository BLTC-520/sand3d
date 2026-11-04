# Fewer tokens for the same object

The token figure, part by part. Every program is counted the same way: o200k_base tokens, code
only (docstrings and comments are not counted). A ratio is the other program's tokens over sand3d's.

| compared with | who wrote it | n | median ratio | |
|---|---|---|---:|---|
| Blender Python | written by an LLM | 30 CAD parts | **4.0×** | 9 of 30 build the right part |
| CadQuery | the dataset's own programs (Zero-To-CAD) | 17 CAD parts | **2.3×** | synthetic programs, generated for the dataset |
| FeatureScript (Onshape) | the dataset's own programs (CADFS) | 13 CAD parts | **6.0×** | real designs from public Onshape documents |
| Articraft's Python SDK | the dataset's own programs | 12 articulated objects | **2.0×** | 5 of 12 also use CadQuery; they also declare masses and inertias |

Who wrote what:

- **sand3d**: the programs of this repo, written for it; each matches its reference mesh (the CAD model's,
  or the articulated object's), the CAD parts at an F-score of 0.95 at 2 % of the diagonal.
- **Blender Python**: written by an LLM from the CAD part's source; *right part* means it runs and its mesh
  matches the CAD model's.
- **CadQuery, FeatureScript**: the program the CAD dataset ships for the part. Zero-To-CAD-1m (Apache-2.0) is
  synthetic CadQuery; CADFS (CC BY 4.0) holds real Onshape designs in FeatureScript.
- **Articraft**: the program Articraft-10K (CC BY 4.0) ships for the object, written with its own Python SDK
  (meshes, joints, materials, masses), its tests left out; five also build shapes with CadQuery.

Not compared: objects that come as meshes (Objaverse-type assets): no program exists to set beside sand3d's;
the articulated objects in Blender Python: none was written; the CADFS parts in CadQuery: their source is
FeatureScript.

## 30 CAD parts

| part | source | sand3d | Blender Python | right part | ratio | source program | ratio |
|---|---|---:|---:|:---:|---:|---|---:|
| a block with a side window open at its bottom, two rib slots under its +Y edge and a hole drilled on that edge | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `d9657ce8-4340-baf8-564c-24ef95b451b9` | 330 | 862 | yes | 2.6× | CadQuery 502 | 1.5× |
| a quarter-torus pipe elbow, its inlet chamfered, a hole drilled into the inlet, every edge softened | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `b8c707fe-e962-4eb1-8bc9-3465761f23b4` | 221 | 1084 | no | 4.9× | CadQuery 557 | 2.5× |
| a ring notched round its outside, the notches only through its lower half, their four vertical edges chamfered | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `0d84288b-5014-5b32-4355-9452883f472d` | 339 | 996 | no | 2.9× | CadQuery 415 | 1.2× |
| an L bracket: a bar and a flange, and on top a rib following their L, grown 2 mm all round | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `524d6a9e-b1a8-7a81-3809-d7eea0424235` | 181 | 525 | no | 2.9× | CadQuery 412 | 2.3× |
| a block drawn in inches' worth of millimetres, then scaled by 2.54 | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00400706` | 110 | 336 | yes | 3.1× | FeatureScript 682 | 6.2× |
| a large turned body: one outline revolved about a line of its own | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00421068` | 927 | 1817 | no | 2.0× | FeatureScript 4531 | 4.9× |
| a round flange with four holes on a square, its top edge rounded | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `b88686f2-ac53-4a3f-cb64-13d4b758199d` | 141 | 1068 | no | 7.6× | CadQuery 814 | 5.8× |
| a small hexagon with a wing on each side, one the mirror image of the other, their vertical edges rounded | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `825dca76-e226-7c8f-a08f-59371e559adf` | 217 | 1355 | no | 6.2× | CadQuery 283 | 1.3× |
| a long rod, a rounded-triangle collar at its end, three pins standing on the collar, their tips cut to points | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00878117` | 385 | 1630 | yes | 4.2× | FeatureScript 2633 | 6.8× |
| a thin tube along Y, its outer rims rounded, a pin hole through its wall near one end, that hole's outer mouth chamfered | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `b7779e11-5886-fad1-7792-b970ba0f615e` | 233 | 1193 | no | 5.1× | CadQuery 479 | 2.1× |
| a square frame with a rounded window, two holes on its middle line, four drilled holes at its corners and a blind hole driven into its -Y side along its top edge | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00305103` | 228 | 1048 | yes | 4.6× | FeatureScript 2944 | 12.9× |
| a closed round box, hollow inside, a slot through its +X side, a boss floating in the hollow and a forest of thin rods standing through it, top to bottom | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `960d943d-5d36-c68d-54e6-e4271e4d24ec` | 319 | 892 | no | 2.8× | CadQuery 537 | 1.7× |
| a bored disc, every edge chamfered | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `2bc02539-1e01-57fc-1095-3a4475a6b63e` | 94 | 1421 | no | 15.1× | CadQuery 339 | 3.6× |
| an elliptical plate, its top edge rounded right through its thickness, the word "Rato" standing on it | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00466650` | 290 | 808 | no | 2.8× | FeatureScript 844 | 2.9× |
| a bored disc, its top edge cut back by a long, shallow chamfer, both edges of the chamfer rounded | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00211684` | 117 | 623 | no | 5.3× | FeatureScript 1157 | 9.9× |
| a fork-like bracket: a T-shaped band with two legs, turned 40° about a far axis, and above it a notched plate, 25.4 thick | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00456559` | 338 | 1003 | no | 3.0× | FeatureScript 1967 | 5.8× |
| half a turned ring, a small rib under it, an insert pin sticking out of its end | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `6cc4cc5c-a504-8b54-5276-08afe080f807` | 241 | 981 | no | 4.1× | CadQuery 357 | 1.5× |
| a small drafted block, its bottom edges chamfered | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `9728290b-d7bb-40ed-164a-ec6cf0f5447d` | 158 | 665 | yes | 4.2× | CadQuery 529 | 3.3× |
| a block with two holes off-centre, its vertical corners rounded and its top edges chamfered, holes included | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `de5f2cdc-c1cf-076a-d8ea-e33766888363` | 151 | 1454 | yes | 9.6× | CadQuery 410 | 2.7× |
| a hub eaten from below by a wide cone, the cone's edges rounded; eight holes round its top, a slot in its rim, six ribs half sunk in its side | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `2e1049b3-4bf1-6706-a401-6b8a76ffc082` | 317 | 944 | no | 3.0× | CadQuery 436 | 1.4× |
| a block with a flange on each end | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `66f91767-51e3-c565-9b80-c45836127ee7` | 115 | 890 | yes | 7.7× | CadQuery 374 | 3.3× |
| a large panel, mirror-symmetric about Y = 0, its two top corners cut, two tall slots near each side | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00298573` | 237 | 498 | no | 2.1× | FeatureScript 1340 | 5.7× |
| a tube with a long rounded slot right through it, across its axis | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00115460` | 254 | 655 | no | 2.6× | FeatureScript 990 | 3.9× |
| a thin disc with twelve small notches round its rim | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00374959` | 151 | 742 | no | 4.9× | FeatureScript 1083 | 7.2× |
| a tall cover lofted through six rectangles that narrow and turn as they rise, rib grooves cut into its foot, its top and bottom edges rounded | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `5ad9d45b-ea4f-8079-1186-76e3b8d6a1b1` | 259 | 1129 | no | 4.4× | CadQuery 639 | 2.5× |
| a wall flange: a coned cup for a hub, a flange round it, a hole through the cup's point, its top edges chamfered and a ring of small knurls standing on its rim | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `8719a024-46f7-2edf-2d5b-96f11059d3db` | 233 | 1146 | no | 4.9× | CadQuery 906 | 3.9× |
| an L bracket filled out by a gusset into a pentagon, its corners rounded, one countersunk hole near its inside corner | [Zero-To-CAD-1m](https://huggingface.co/datasets/ADSKAILab/Zero-To-CAD-1m) `116f16d9-515f-52a8-74cb-ee98471dea71` | 284 | 975 | no | 3.4× | CadQuery 553 | 1.9× |
| a turned part: a flanged base and a tall thin sleeve rising from it | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00577926` | 154 | 616 | yes | 4.0× | FeatureScript 927 | 6.0× |
| a tube standing at one end of a plate whose other end is square, a rib along the plate's middle, cut back on a slant | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00638437` | 357 | 1093 | yes | 3.1× | FeatureScript 1718 | 4.8× |
| a square nut: a bored square block, the corners of both faces turned off by a 30° cone, a V-notch across its top | [CADFS](https://huggingface.co/datasets/VladPyatov/CADFS) `00266126` | 315 | 742 | no | 2.4× | FeatureScript 2762 | 8.8× |

## 12 articulated objects

| object | source | sand3d | Articraft program | ratio | uses CadQuery |
|---|---|---:|---:|---:|:---:|
| a front-loading washing machine: a door on a hinge, an endless drum, a detergent drawer, an endless dial | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_a-front-loading-washing-machine-with-a-white-rec_20260513_002941_547341_050bf63f` | 742 | 1538 | 2.1× | yes |
| a double-leaf garden gate: two leaves on hinges, a mirror pair, and a drop bolt sliding down the right leaf into a socket in the foundation | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_garden_gate_30e6e784533b4583ac23a37b85f64c86` | 1232 | 2850 | 2.3× | no |
| a compact refrigerator: two doors on one hinge line, opening by negative angles, and a thermostat dial turning in a control housing fixed under the divider | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_refrigerator_with_hinged_doors_eafdd7d9813b42fa80e8e2e8ff778665` | 1541 | 3264 | 2.1× | no |
| a compact keyboard: forty keys on plungers, a trackpoint on two crossed pivots, a media wheel on a fixed shaft | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_keyboard_33e6828d32c148999830f99c31995d49` | 1628 | 3258 | 2.0× | no |
| a skateboard: two trucks steering on 45° kingpins, four endless wheels on the trucks | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_skateboard_b74cde82df474176b7005c584ba8eb13` | 705 | 1505 | 2.1× | yes |
| a floor task lamp: a head that swivels on the column, an arm that lifts on the head's yoke, a shade that tilts at the arm's tip — a revolute chain three deep | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_articulated_task_lamp_e3b37e132fda4a8b848be4c5ba370d7e` | 1319 | 2191 | 1.7× | no |
| an XYZ Cartesian stage: an X carriage on the base's rails, a Y stage on the carriage, a column welded to the Y stage, and a table sliding up the column | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_xyz_cartesian_stage_9569f7654fbc435db20ac8bc588765a1` | 1271 | 2113 | 1.7× | no |
| a device on a tripod head: a pan, a tilt, a clamp that slides and its screw knob, two lock knobs; the legs and the device are fixed | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_tripodmounted_device_a0b63454b90945138129d93d176264fc` | 3016 | 4192 | 1.4× | yes |
| compact theatre binoculars: two housings on a central hinge, a focus wheel that turns a full turn either way, two eyecups that twist | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_binoculars_fc9fc306c6f8437683635fccb0369257` | 1467 | 2917 | 2.0× | no |
| a compact pickup tailgate: a gate on a lower hinge, two latch knobs and a work-stop bar that folds up from the gate's top edge | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_pickup_tailgate_be20bae3a83e40c386c21adab290f72d` | 1808 | 3690 | 2.0× | no |
| a rugged screw-cap bottle: a cap that turns and lifts on the neck | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_screwcap_bottle_aa1625790e9e4236941bc4c2650955de` | 1313 | 2520 | 1.9× | yes |
| a bevel-to-spur transfer: an endless vertical input shaft drives, through an 18/18 bevel pair, a horizontal transfer shaft, which drives a parallel output shaft through an 18/24 spur pair | [Articraft-10K](https://huggingface.co/datasets/camvsl/Articraft-10K) `rec_gear_assemblies_65e1d6ce16ad4dd58dffa5c555c5680b` | 1775 | 2675 | 1.5× | yes |
