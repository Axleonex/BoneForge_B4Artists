# BoneForge B4Artists — Production Rigging Suite

This Bforartists-exclusive build adds a complete character-rigging workflow on
top of BoneForge. Every feature below is BoneForge-native and registers only
inside Bforartists. All bone names use the BoneForge convention `base-Side`
(hyphen side suffix, e.g. `upperarm.fk-L`, `roll_heel-L`).

Scope note: CATS, Material Combiner, and UVToolkit-derived Material Combiner
controls are shared with the open Blender build as of BoneForge 8.4.6. This
document covers what still remains B4Artists-exclusive: the production rigging
suite, host lockout, control rig builder, animator controls, control picker,
advanced retarget/export systems, and Bforartists-specific packaging.

## Control-Rig Construction Engine

The engine turns a marker/preset description (`RigSpec`) into a full control
rig — not a bare skeleton:

- **Dual IK/FK limbs** with a pole target and a per-limb IK/FK blend driver
  (`IK_FK-<limb>-<side>` on the hidden `properties` bone; 0 = FK, 1 = IK).
- **FK spine/neck/head**, FK finger chains, and a **driven foot-roll**
  (`foot_roll-<side>`, heel/ball limited rotation).
- **Native IK stretch** on the solved chain (graceful over-extension; the IK
  bends rather than collapsing).
- Control widgets, per-control colour, and bone-collection organisation
  (`Root`, `Controls`, `FK`, `IK`, `Fingers`, `Tail`, `Spline`, `Face`,
  `Deform`, `MCH`). Re-running the build is idempotent.

The build is split into a pure planning layer (`compute_build_plan`) and the
Blender realisation (`apply_build_plan`).

## Smart Landmark Detection

`Auto-Detect Joints` proposes body markers from the selected mesh:

1. A geometry kernel samples the evaluated (modifier-applied) mesh in world
   space and derives bounds, symmetry plane, extremities, and confidence-tagged
   body landmarks; intermediate joints (neck, elbows, hips, knees, toes, heels)
   are interpolated.
2. An optional **local** model is used only if present; missing model files
   simply fall back to geometry and never break registration.

Proposals carry a confidence and are **never auto-confirmed**. Use
**Accept High-Confidence** to confirm strong markers in bulk, **Reset
Low-Confidence** to clear weak ones for manual placement, and **Mirror
Confirmed Side** to copy one side to the other. Manual marker placement is
unchanged.

## Face Rig

Enable the face option to add eyes (aim via a look target), eyelids, brows,
a jaw with an open/close limit, and lips. The lower lip follows the jaw by a
**soft-lips** amount, reduced toward zero as **sticky-lips** rises so the lips
stay sealed while the jaw opens. An optional muzzle is available for creatures.

## Animator Control Layer

For generated rigs (sidebar → *Control Layer*):

- **IK/FK switch** with no-pop snapping, and a **frame-range bake** in either
  direction.
- **Pole follow**, **IK pin**, **lock-free** limb inheritance, foot-roll keying,
  and **global rig scale** that respects protected (locked) bones.
- Per-character control state, isolated per rig.

## Retargeting

Retarget motion from common source-skeleton families using BoneForge's original
mapping presets (`maps/`):

- Source bone names resolve through capture **namespaces** (`mocap:Hips` →
  `Hips`); unmatched bones are reported, never silently dropped.
- A **rest-orientation correction** re-expresses the source motion in each
  target bone's frame so the result matches the source rather than just sharing
  names.
- Per-bone tweaks (rotation multiplier + offset) and batch retargeting (one
  clean action per source clip).

## Game Export

`Export (Profile)` drives FBX/GLB export from a target profile (Unreal, Unity,
Godot, VRChat, generic FBX/GLB):

- A profile **rig-check** runs only that target's validation checks; fixes are
  explicit (e.g. *Apply Transforms*), never silent.
- **Deform-only** export strips the animator controls and keeps the deform
  skeleton; **action selection** (active / all / none) prevents corrupt takes;
  an optional **root-motion** bake includes the custom root.

## Control Picker / Rig UI

A graphical control picker (sidebar → *Control Picker*, or the popup):

- A clickable control layout **auto-generated** from a rig's bone collections,
  grouped and coloured per control type; **import/export** as BoneForge JSON.
- Selection by control, by group, **selection sets**, and side **mirror**
  (`-L` ⇄ `-R`). Inline IK/FK from the control layer.
- Per-character state, so multiple rigs in one scene keep independent layouts
  and selection sets.

---

*Clean-room provenance: all of the above is reimplemented from the public
Blender/Bforartists Python API and observable rigging behaviour. No third-party
add-on's source, assets, preset files, or naming scheme were consulted or
copied.*
