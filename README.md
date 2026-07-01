# BoneForge B4Artists

A **Bforartists-exclusive** build of **BoneForge** — a modular rigging and animation
extension. This build runs **only in [Bforartists](https://www.bforartists.de/)**
(the Blender fork). In standard Blender it will not load: it registers a single
notice with a "Get Bforartists" button and nothing else.

| | |
|---|---|
| **Tool** | BoneForge BFA |
| **Version** | 8.5.0 |
| **Host** | Bforartists 4.0+ (tested through 5.2) — **not** standard Blender |
| **Category** | Rigging / Animation |
| **License** | GPL v2.0 or later |

> This tool was built with heavy AI assistance and is under active bug-fixing.
> If you hit an issue, a screenshot or a note about what you were doing helps a
> lot — please open an [issue](../../issues).

## What it does

BoneForge is a universal rig UI plus a full rigging/animation toolkit, organized
into feature packages you can toggle on and off per-project:

- **Rig UI & viewport** — bone-collection panel, visibility bookmarks, hotkey popup.
- **Animation** — pose library, graph & viewport tools, Rigify enhancement,
  corrective shape keys, tween machine, animation layers.
- **Weights & deform** — weight mirror / transfer / table, deform-bone control,
  delta mush, proximity wrap, custom shape library.
- **Advanced rigging** — rig validator, space switching, spline IK, ribbons,
  chain dynamics, viseme rig, SDK driver builder, rig notes.
- **Auto-rigging & control-rig engine** — a control-rig construction engine
  (dual IK/FK chains with blend drivers, pole targets, stretch, foot-roll,
  deform tagging, widgets / colours / bone-collections); smart landmark
  detection from mesh geometry with confidence states; modular presets (human,
  quadruped, tail, spline) and a face rig (eyes, lids, brows, jaw, soft + sticky
  lips); retargeting with original source maps, rest-pose correction, per-bone
  tweaks and batch; mannequin, skin pipeline, quick-human flow.
- **Animator control layer** — IK/FK switch + snap, frame-range bake, pole /
  pin, foot-roll, global rig scale with protected locks, per-character state.
- **Control picker / rig UI** — clickable control layout mapped to pose bones,
  selection sets + mirror, layout import/export as JSON, layout editor, inline
  IK/FK, popup picker.
- **Game export profiles** — validated profiles (Unreal, Unity, VRChat, Godot,
  generic FBX/GLB) with explicit (never silent) fixes, action filtering, root
  motion, keyframe interpolation, and shape-key validation.
- **Bone merge** — three-stage bone-merge workspace.
- **VRChat** — CATS-style cleanup, clothing merge, hair physbones, naming
  detector, performance ranking, FBX export.
- **I/O hub & bridges** — VRM (VRoid / VTuber), MMD (PMX / VMD), FBX, glTF,
  game-ready export.

Disabling a tool actually unregisters its classes (a functional hide, not a
poll trick), so each package pays its cost only when you turn it on.

## Download & install

The ready-to-install add-on lives in [`releases/`](releases/):

- `BoneForge-BFA-8.5.0.zip`

To install in **Bforartists**:

1. **Edit → Preferences → Add-ons → Install from Disk…**
2. Pick `BoneForge-BFA-8.5.0.zip`.
3. Enable the add-on by ticking its checkbox.
4. Open the **N-panel** in the 3D Viewport — BoneForge adds a **Rig Builder**
   tab; Properties → Object Data gains a mirror panel for the active armature.

You don't need to unzip anything by hand — Bforartists installs directly from
the `.zip`.

## B4Artists Exclusive Feature Set

The B4Artists package is the exclusive build. The open Blender package remains
the non-exclusive standard-Blender build focused on CATS, Material Combiner, and
basic BoneForge/Mixamo-style avatar helpers.

| Area | Open Blender BoneForge | BoneForge B4Artists Exclusive |
|---|---|---|
| Host support | Standard Blender | Bforartists |
| Repository | `Axleonex/BoneForge_ALTERNATIVE_CATS_for_5.0_Blender` | `Axleonex/BoneForge_B4Artists` |
| Release zip | `BoneForge-8.5.0.zip` | `BoneForge-BFA-8.5.0.zip` |
| CATS avatar cleanup | Included | Included |
| Material Atlas Combiner | Included | Included |
| Selectable materials and textures | Included | Included |
| Atlas UV0 export default | Included | Included |
| Basic BoneForge and Mixamo-style avatar helpers | Included | Included |
| Production control-rig construction | Not included | Included |
| Smart landmark / joint detection suite | Not included | Included |
| Animator control layer | Not included | Included |
| Control Picker / rig UI | Not included | Included |
| Advanced retargeting core and source maps | Not included | Included |
| Profile-driven game export | Not included | Included |
| B4Artists-exclusive release gate | Not included | Included |

## Browse the source

The unpacked, readable source is in [`boneforge/`](boneforge/) so you can read it
on GitHub without downloading anything. The source folder and the `releases/`
zip contain the same code; the zip is just packaged for one-click install.

## Documentation

Manuals are in [`docs/`](docs/):

- [`docs/BoneForge_Documentation.pdf`](docs/BoneForge_Documentation.pdf) — user manual (PDF)
- [`docs/BoneForge_Documentation.md`](docs/BoneForge_Documentation.md) — same manual in Markdown
- [`docs/BoneForge_BFA_Rigging_Suite.md`](docs/BoneForge_BFA_Rigging_Suite.md) — the 8.4.x production rigging suite (engine, detection, face, control layer, retarget, export, picker)

## Requirements

- **Bforartists 4.0+**. Not compatible with standard Blender.

## License

Released under the **GNU General Public License v2.0 or later** — see
[`LICENSE`](LICENSE).
