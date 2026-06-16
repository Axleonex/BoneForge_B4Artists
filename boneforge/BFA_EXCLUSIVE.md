# BoneForge BFA 8.3.1 — Bforartists-Exclusive Build

This build is functionally identical to BoneForge 8.3.1 but runs **only
in Bforartists**. In standard Blender it enables as an inert stub: a
preferences notice, an error popup, and a "Get Bforartists" button.
No panels, operators, properties, or feature packages are registered.

## How the host is detected

Any one of these marks the host as Bforartists; unmodified standard
Blender produces none:

| Signal | Source |
|---|---|
| `bpy.app.bforartists_version` | Attribute compiled into Bforartists builds |
| `bpy.app.binary_path` | Executable is `bforartists` / `bforartists.exe` |
| `sys.executable` | Bundled Python lives in the Bforartists install dir |
| `bpy.utils.resource_path()` | Bforartists' own `bforartists` config/resource tree |

## Defense-in-depth layers

1. **Entry gate** — `boneforge/__init__.py::register()` checks the host
   (its own inline copy AND `bfa_guard`) before anything loads.
2. **Core gate** — `core/__init__.py::_require_bfa_host()` raises in
   standard Blender; independent inline copy.
3. **Registry gate** — `core/tool_registry.py::get_registry()` refuses
   to hand out the tool registry in standard Blender, so no feature
   manifest can register or enable; independent inline copy (verdict
   cached per session so teardown always works).
4. **Timer re-verify** — 20 s after startup and every 10 min, the entry
   point re-checks the host; on failure it unloads everything and swaps
   in the lockout stub.

Bypassing the lock requires consistent edits to multiple files —
editing or deleting `bfa_guard.py` alone is not enough. (As with any
Python add-on, the lock is a strong deterrent, not DRM.)

## Compatibility notes

- Package name is still `boneforge`; manifest ids, operator/panel
  idnames, scene properties, and saved preferences carry over from
  standard BoneForge installs unchanged.
- `bl_info` name is "BoneForge BFA" so both builds are distinguishable
  in the add-on browser. Do not install both in the same host.
