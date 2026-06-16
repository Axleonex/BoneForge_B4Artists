"""BoneForge BFA — Control-Rig Construction Engine (Task 1, FOUNDATION).

Bforartists-exclusive. Turns a marker/preset description (:class:`RigSpec`)
into a production control rig: dual IK/FK limbs with pole targets and blend
drivers, an FK spine/neck/head, FK finger chains, and a driven foot-roll —
plus control widgets and bone-collection organisation.

Two layers, deliberately separated:

* ``compute_build_plan(spec)`` — **pure Python**, no ``bpy``. Produces a
  declarative :class:`~boneforge.autorig.components.BuildPlan`. This is what
  closes the production-rig gap (the old generator created a single IK
  constraint and no drivers) and it is unit-testable headlessly.
* ``apply_build_plan(plan, armature_obj)`` — realises the plan in Blender
  via ``core.rig_ops``. Imports ``bpy`` lazily.

Clean-room: rig topology, the IK/FK blend, and foot-roll are implemented
from first principles / public rigging references with BoneForge-native
bone names. No third-party rig source or asset is used. Runs only under
the Bforartists guard.
"""
from dataclasses import dataclass, field

from .components import BuildPlan, CollectionDef
from .components import spine as _spine
from .components import limb as _limb
from .components import digit as _digit
from .components import foot as _foot
from .components import tail as _tail
from .components import spline as _spline_chain
from .components import face as _face
from .components import validate_plan

# Collections in UI order.
_COLLECTION_ORDER = ["Root", "Controls", "FK", "IK", "Fingers", "Tail",
                     "Spline", "Face", "Deform", "MCH"]


@dataclass
class RigSpec:
    """Declarative description of the rig to build (preset + options)."""
    name: str = "BoneForge Rig"
    sides: tuple = ("L", "R")
    arms: bool = True
    legs: bool = True
    fingers: bool = True
    foot_roll: bool = True
    stretch: bool = True
    preset: str = "human"
    tail_segments: int = 0
    spline_chains: tuple = ()      # each: (name, count, attach_bone)
    face: bool = False             # add the facial rig (eyes/lids/brows/jaw/lips)
    muzzle: bool = False           # face muzzle (creatures)


def compute_build_plan(spec: RigSpec) -> BuildPlan:
    """Pure: build the full declarative plan for ``spec`` (no bpy)."""
    plan = BuildPlan()
    _spine.build_spine(plan)
    if spec.preset == "quadruped":
        # spine + four legs (front offset forward, back offset back) + tail
        for side in spec.sides:
            _limb.build_limb(plan, "leg", side, stretch=spec.stretch,
                             tag="front", y_offset=0.45)
            _limb.build_limb(plan, "leg", side, stretch=spec.stretch,
                             tag="back", y_offset=-0.35)
        if spec.tail_segments == 0:
            spec = RigSpec(**{**spec.__dict__, "tail_segments": 5})
    else:
        for side in spec.sides:
            if spec.arms:
                _limb.build_limb(plan, "arm", side, stretch=spec.stretch)
                if spec.fingers:
                    _digit.build_hand_digits(plan, side)
            if spec.legs:
                _limb.build_limb(plan, "leg", side, stretch=spec.stretch)
                if spec.foot_roll:
                    _foot.build_foot_roll(plan, side)
    # optional extras for any preset
    if spec.face:
        _face.build_face(plan, muzzle=spec.muzzle or spec.preset == "quadruped")
    if spec.tail_segments:
        _tail.build_tail(plan, spec.tail_segments)
    for sc in spec.spline_chains:
        name, count = sc[0], sc[1]
        attach = sc[2] if len(sc) > 2 else "chest"
        _spline_chain.build_spline_chain(plan, name, count, attach=attach)
    # register collections actually used, in canonical order
    used = {b.collection for b in plan.bones}
    for i, name in enumerate([c for c in _COLLECTION_ORDER if c in used]):
        plan.add_collection(name, ui_row=i)
    return plan


# ---------------------------------------------------------------- apply

def apply_build_plan(plan, armature_obj, context=None):
    """Realise ``plan`` on an existing armature object (Blender side)."""
    import bpy
    from boneforge.core import rig_ops
    if context is None:
        context = bpy.context
    arm = armature_obj.data

    # 1) edit bones
    prev_active = context.view_layer.objects.active
    context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        ebs = arm.edit_bones
        for bd in plan.bones:
            eb = ebs.get(bd.name) or ebs.new(bd.name)
            eb.head = bd.head
            eb.tail = bd.tail
            eb.roll = bd.roll
            eb.use_deform = bd.deform
        # parent pass (all bones exist now)
        for bd in plan.bones:
            eb = ebs.get(bd.name)
            if bd.parent:
                eb.parent = ebs.get(bd.parent)
                eb.use_connect = bd.use_connect
    finally:
        bpy.ops.object.mode_set(mode='POSE')

    pbones = armature_obj.pose.bones

    # 1b) per-bone pose settings (native IK stretch on solved chains).
    # Always written (0.0 is the rigid default) so a chain bone is never
    # left with a stale stretch value from a previous build.
    for bd in plan.bones:
        pb = pbones.get(bd.name)
        if pb is not None:
            pb.ik_stretch = bd.ik_stretch

    # 2) custom properties
    for pd in plan.props:
        pb = pbones.get(pd.bone)
        if pb is not None:
            rig_ops.ensure_custom_prop(pb, pd.name, pd.default,
                                       pd.soft_min, pd.soft_max, pd.description)

    # 3) constraints
    for cd in plan.constraints:
        pb = pbones.get(cd.bone)
        if pb is None:
            continue
        if cd.type == 'IK':
            rig_ops.add_ik(
                pb, target=armature_obj, subtarget=cd.subtarget,
                chain_count=cd.params.get("chain_count", 2),
                pole_target=armature_obj,
                pole_subtarget=cd.params.get("pole_subtarget"),
                pole_angle=cd.params.get("pole_angle", 0.0),
                name=cd.name,
            )
        else:
            tgt = armature_obj if cd.target_self else None
            rig_ops.add_constraint(pb, cd.type, cd.name, target=tgt,
                                   subtarget=cd.subtarget, **cd.params)

    # 4) drivers
    for dd in plan.drivers:
        full_path = 'pose.bones["%s"].%s' % (dd.bone, dd.data_path_suffix)
        variables = []
        for v in dd.variables:
            spec = dict(v)
            spec["id"] = armature_obj
            variables.append(spec)
        rig_ops.add_driver(armature_obj, full_path, dd.index,
                           dd.expression, variables)

    # 5) collections + 6) widgets
    for cd in plan.collections:
        rig_ops.ensure_collection(arm, cd.name)
    for bd in plan.bones:
        rig_ops.assign_to_collection(arm, bd.name, bd.collection)
    try:
        from boneforge.weights import widgets as _widgets
        for wa in plan.widgets:
            pb = pbones.get(wa.bone)
            if pb is None:
                continue
            wobj = _widgets.ensure_widget_object(wa.widget, context)
            if wobj is not None:
                rig_ops.assign_widget(pb, wobj, wa.scale)
    except Exception:
        import traceback
        traceback.print_exc()

    context.view_layer.objects.active = prev_active
    return plan


def build_control_rig(armature_obj, spec=None, context=None):
    """Compute and apply a control rig on ``armature_obj``."""
    spec = spec or RigSpec()
    plan = compute_build_plan(spec)
    apply_build_plan(plan, armature_obj, context)
    return plan


# ----------------------------------------------------------- operator

def _register_classes():
    import bpy
    from boneforge import bfa_guard

    class BONEFORGE_OT_build_control_rig(bpy.types.Operator):
        """Build a BoneForge control rig on the active armature"""
        bl_idname = "boneforge.build_control_rig"
        bl_label = "Build Control Rig"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            obj = context.active_object
            return obj is not None and obj.type == 'ARMATURE'

        def execute(self, context):
            # Hard gate: never runs outside Bforartists, even via script.
            bfa_guard.require_bforartists("rig_build")
            try:
                build_control_rig(context.active_object, RigSpec(), context)
            except Exception as exc:
                self.report({'ERROR'}, "Rig build failed: %s" % exc)
                return {'CANCELLED'}
            self.report({'INFO'}, "BoneForge control rig built")
            return {'FINISHED'}

    return (BONEFORGE_OT_build_control_rig,)


_classes = ()


def register():
    import bpy
    global _classes
    _classes = _register_classes()
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
