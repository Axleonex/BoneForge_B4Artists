# BoneForge B4Artists Exclusive Build

This package is the B4Artists-exclusive BoneForge build. It is intended for
Bforartists users; standard Blender users should install the open Blender
BoneForge package instead.

The package includes internal runtime validation so the exclusive build remains
separate from the non-exclusive open Blender build. Implementation details are
intentionally not documented here.

## Build split

| Area | Open Blender BoneForge | BoneForge B4Artists Exclusive |
|---|---|---|
| Host support | Standard Blender | Bforartists |
| Repository | `Axleonex/BoneForge_ALTERNATIVE_CATS_for_5.0_Blender` | `Axleonex/BoneForge_B4Artists` |
| Release zip | `BoneForge-8.4.6.zip` | `BoneForge-BFA-8.4.6.zip` |
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

## Compatibility notes

- Package name remains `boneforge`; saved preferences and scene properties carry
  over from earlier BoneForge installs.
- `bl_info` name is "BoneForge BFA" so both builds are distinguishable in the
  add-on browser. Do not install both in the same host.
