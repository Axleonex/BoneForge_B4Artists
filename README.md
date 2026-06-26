# BoneForge B4Artists

A **Bforartists-exclusive** build of **BoneForge** — a modular rigging and animation
extension. This build runs **only in [Bforartists](https://www.bforartists.de/)**
(the Blender fork). In standard Blender it will not load: it registers a single
notice with a "Get Bforartists" button and nothing else.

| | |
|---|---|
| **Tool** | BoneForge BFA |
| **Version** | 8.4.0 |
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

- `BoneForge-BFA-8.4.6.zip`

To install in **Bforartists**:

1. **Edit → Preferences → Add-ons → Install from Disk…**
2. Pick `BoneForge-BFA-8.4.6.zip`.
3. Enable the add-on by ticking its checkbox.
4. Open the **N-panel** in the 3D Viewport — BoneForge adds a **Rig Builder**
   tab; Properties → Object Data gains a mirror panel for the active armature.

You don't need to unzip anything by hand — Bforartists installs directly from
the `.zip`.

## Bforartists-only — how the lock works

This build refuses to run in standard Blender. The host is detected by several
independent signals; an unmodified standard Blender produces none of them:

| Signal | Source |
|---|---|
| `bpy.app.bforartists_version` | Attribute compiled into Bforartists builds |
| `bpy.app.binary_path` | Executable is `bforartists` / `bforartists.exe` |
| `sys.executable` | Bundled Python lives in the Bforartists install dir |
| `bpy.utils.resource_path()` | Bforartists' own `bforartists` config/resource tree |

The check is enforced in depth across four layers, so removing or editing any
single file is not enough to bypass it:

1. **Entry gate** — `boneforge/__init__.py` verifies the host before anything
   functional loads.
2. **Core gate** — `boneforge/core/__init__.py` independently raises in standard
   Blender.
3. **Registry gate** — `boneforge/core/tool_registry.py` refuses to hand out the
   tool registry, so no feature package can register or enable.
4. **Timer re-verify** — the entry point re-checks the host ~20 s after startup
   and every 10 minutes, swapping in the lockout notice if the check ever fails.

In standard Blender, only a stub preferences notice + a "Get Bforartists" button
are registered — no panels, operators, properties, or features. (As with any
Python add-on, this is a strong deterrent, not DRM.) Details:
[`boneforge/BFA_EXCLUSIVE.md`](boneforge/BFA_EXCLUSIVE.md). The lock is exercised
by [`test_bfa_lock.py`](test_bfa_lock.py) (run `python3 test_bfa_lock.py`).

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
