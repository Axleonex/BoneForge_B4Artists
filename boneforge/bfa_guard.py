"""BoneForge BFA — Bforartists environment guard.

This build of BoneForge is **exclusive to Bforartists** and refuses to
run inside standard Blender. The guard is multi-signal: any one of the
following marks the host as Bforartists, and an unmodified standard
Blender produces none of them.

Detection signals
-----------------
``bpy.app.bforartists_version``  Attribute compiled into Bforartists
                                 builds. Absent in standard Blender.
``bpy.app.binary_path``          Bforartists ships as ``bforartists``
                                 / ``bforartists.exe``.
``sys.executable``               The bundled Python lives inside the
                                 Bforartists install directory.
``bpy.utils.resource_path``      Bforartists keeps its own config /
                                 resource tree named ``bforartists``
                                 (separate from Blender's).

Lockout behaviour (standard Blender)
------------------------------------
``register_lockout()`` registers *only* a stub AddonPreferences box
and a "Get Bforartists" button — no panels, operators, properties, or
feature packages — plus a one-shot popup explaining the lock. Nothing
functional ever loads.

Defense in depth
----------------
This module is one layer of several. ``boneforge/__init__.py``,
``boneforge/core/__init__.py`` and ``boneforge/core/tool_registry.py``
each carry an *independent inline copy* of the detection logic, and
the entry point re-verifies on a timer after startup. Bypassing the
lock requires editing multiple files; editing or deleting this module
alone is not enough.
"""

import logging
import sys

logger = logging.getLogger(__name__)

# The add-on package id as Blender sees it (folder name of the
# installed add-on). AddonPreferences.bl_idname must match it.
_ADDON_ID = __package__ or "boneforge"

_DOWNLOAD_URL = "https://www.bforartists.de/download/"

LOCK_TITLE = "BoneForge BFA — Bforartists required"
LOCK_LINES = (
    "This build of BoneForge is exclusive to Bforartists.",
    "It will not run in standard Blender.",
    "Install it in Bforartists, or download Bforartists below.",
)


# -- Detection ----------------------------------------------------------

def detection_signals():
    """Return the list of Bforartists indicators found in this host.

    Empty list == standard Blender (or any non-Bforartists host).
    Every check is wrapped so an API difference can never raise out
    of the guard itself.
    """
    signals = []
    try:
        import bpy
    except ImportError:
        # Not running inside a Blender-derived host at all (unit
        # tests, linters). The guard has nothing to decide here.
        return signals

    app = bpy.app

    try:
        if getattr(app, "bforartists_version", None):
            signals.append("app.bforartists_version")
    except Exception:
        pass

    try:
        if "bforartists" in (getattr(app, "binary_path", "") or "").lower():
            signals.append("binary_path")
    except Exception:
        pass

    try:
        if "bforartists" in (sys.executable or "").lower():
            signals.append("sys.executable")
    except Exception:
        pass

    for resource_kind in ("USER", "LOCAL", "SYSTEM"):
        try:
            resource_dir = bpy.utils.resource_path(resource_kind) or ""
        except Exception:
            continue
        if "bforartists" in resource_dir.lower():
            signals.append("resource_path:%s" % resource_kind)

    return signals


def is_bforartists():
    """True when the running host is Bforartists."""
    return bool(detection_signals())


def require_bforartists(caller="boneforge"):
    """Raise ``RuntimeError`` unless running inside Bforartists.

    Inline re-checks in other modules use their own private copies of
    the detection; this helper exists for any future module that wants
    a guard without duplicating it.
    """
    if not is_bforartists():
        raise RuntimeError(
            "[%s] BoneForge BFA is exclusive to Bforartists and cannot "
            "run in standard Blender. Get Bforartists at %s"
            % (caller, _DOWNLOAD_URL)
        )


# -- Lockout stub UI (the only thing registered in standard Blender) ----

def _build_lockout_classes():
    """Create the stub classes lazily so this module can be imported
    outside Blender (tests) without touching ``bpy.types``."""
    import bpy

    class BONEFORGE_OT_get_bforartists(bpy.types.Operator):
        """Open the Bforartists download page"""
        bl_idname = "boneforge.get_bforartists"
        bl_label = "Get Bforartists"

        def execute(self, context):
            bpy.ops.wm.url_open(url=_DOWNLOAD_URL)
            return {'FINISHED'}

    class BoneForgeLockedPreferences(bpy.types.AddonPreferences):
        bl_idname = _ADDON_ID

        def draw(self, context):
            layout = self.layout
            box = layout.box()
            box.alert = True
            box.label(text=LOCK_TITLE, icon='ERROR')
            for line in LOCK_LINES:
                box.label(text=line)
            row = box.row()
            row.operator(
                BONEFORGE_OT_get_bforartists.bl_idname, icon='URL',
            )

    return (BONEFORGE_OT_get_bforartists, BoneForgeLockedPreferences)


_lockout_classes = ()


def _popup_draw(self, context):
    for line in LOCK_LINES:
        self.layout.label(text=line)


def _notify_locked():
    """One-shot timer callback: surface the lock in the UI."""
    try:
        import bpy
        window_manager = bpy.context.window_manager
        if window_manager is not None:
            window_manager.popup_menu(
                _popup_draw, title=LOCK_TITLE, icon='ERROR',
            )
    except Exception:
        # Headless / background mode has no UI — console log suffices.
        pass
    return None


def register_lockout():
    """Register the lockout stub. Called instead of the real add-on
    when the host is not Bforartists."""
    global _lockout_classes
    import bpy

    logger.error(
        "[BoneForge BFA] Host is not Bforartists — locking out. "
        "No BoneForge functionality has been registered. "
        "Signals found: %s", detection_signals() or "none",
    )

    _lockout_classes = _build_lockout_classes()
    for stub_class in _lockout_classes:
        try:
            bpy.utils.register_class(stub_class)
        except Exception:
            logger.exception(
                "[BoneForge BFA] lockout stub %s failed to register",
                stub_class.__name__,
            )

    try:
        bpy.app.timers.register(_notify_locked, first_interval=0.5)
    except Exception:
        pass


def unregister_lockout():
    """Tear the lockout stub back down."""
    global _lockout_classes
    import bpy

    for stub_class in reversed(_lockout_classes):
        try:
            bpy.utils.unregister_class(stub_class)
        except Exception:
            pass
    _lockout_classes = ()
