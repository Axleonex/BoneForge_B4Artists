"""Control picker — per-character layout state, selection operator, panel."""
import bpy

from boneforge.control_ui import layout as _layout

_LAYOUT_PROP = "bf_picker_layout"     # per-armature JSON state (multi-rig safe)
_EDIT_PROP = "bf_picker_edit_layout"
_SNAP_PROP = "bf_picker_snap_grid"


# ── per-character layout state ────────────────────────────────

def collections_of(arm):
    return {c.name: [b.name for b in c.bones] for c in arm.data.collections}


def generate_layout(arm):
    return _layout.auto_generate_layout(collections_of(arm))


def get_layout(arm):
    raw = arm.get(_LAYOUT_PROP)
    if raw:
        try:
            return _layout.layout_from_json(raw)
        except Exception:
            return None
    return None


def set_layout(arm, layout):
    arm[_LAYOUT_PROP] = _layout.layout_to_json(layout)


def ensure_layout(arm):
    layout = get_layout(arm)
    if layout is None:
        layout = generate_layout(arm)
        set_layout(arm, layout)
    return layout


def edit_mode_enabled(arm):
    return bool(arm.get(_EDIT_PROP, False))


def set_edit_mode(arm, enabled):
    arm[_EDIT_PROP] = bool(enabled)


def snap_to_grid_enabled(arm):
    return bool(arm.get(_SNAP_PROP, True))


def set_snap_to_grid(arm, enabled):
    arm[_SNAP_PROP] = bool(enabled)


# ── selection (active bone always; viewport extend where possible) ──

def select_control_bones(arm, bone_names, extend=False, context=None):
    ctx = context or bpy.context
    if ctx.view_layer.objects.active is not arm:
        ctx.view_layer.objects.active = arm
    if ctx.mode != 'POSE':
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='POSE')
        except Exception:
            pass
    present = [n for n in bone_names if arm.data.bones.get(n) is not None]
    if not present:
        return 0
    # active bone — reliable in every context (incl. background)
    arm.data.bones.active = arm.data.bones[present[-1]]
    if not extend:
        try:
            bpy.ops.pose.select_all(action='DESELECT')
        except Exception:
            pass
    for n in present:                         # viewport highlight (interactive)
        try:
            bpy.ops.pose.select_pattern(pattern=n, case_sensitive=True,
                                        extend=True)
        except Exception:
            pass
    return len(present)


def _is_pickable_rig(obj):
    return obj is not None and obj.type == 'ARMATURE' and len(obj.data.collections)


# ── operators ─────────────────────────────────────────────────

class BF_OT_PickerSelect(bpy.types.Operator):
    """Select the bone driven by a picker control"""
    bl_idname = "boneforge.picker_select"
    bl_label = "Select Control"
    bl_options = {'REGISTER', 'UNDO'}

    bones: bpy.props.StringProperty()        # comma-separated bone names
    extend: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return _is_pickable_rig(context.active_object)

    def execute(self, context):
        names = [n for n in self.bones.split(",") if n]
        n = select_control_bones(context.active_object, names, self.extend,
                                 context)
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Selected %d control(s)" % n)
        return {'FINISHED'}


class BF_OT_PickerSelectGroup(bpy.types.Operator):
    """Select every control in a picker group"""
    bl_idname = "boneforge.picker_select_group"
    bl_label = "Select Group"
    bl_options = {'REGISTER', 'UNDO'}

    group: bpy.props.StringProperty()
    extend: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return _is_pickable_rig(context.active_object)

    def execute(self, context):
        arm = context.active_object
        layout = ensure_layout(arm)
        names = _layout.bones_in_group(layout, self.group)
        n = select_control_bones(arm, names, self.extend, context)
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Selected %d in %s" % (n, self.group))
        return {'FINISHED'}


class BF_OT_PickerRegenerate(bpy.types.Operator):
    """Rebuild this rig's picker layout from its bone collections"""
    bl_idname = "boneforge.picker_regenerate"
    bl_label = "Auto-Generate Layout"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _is_pickable_rig(context.active_object)

    def execute(self, context):
        arm = context.active_object
        set_layout(arm, generate_layout(arm))
        if context.area:
            context.area.tag_redraw()
        self.report({'INFO'}, "Picker layout generated")
        return {'FINISHED'}


class BONEFORGE_PT_picker(bpy.types.Panel):
    """Graphical control picker for the active rig"""
    bl_idname = "BONEFORGE_PT_picker"
    bl_label = " "
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneForge"
    bl_parent_id = "BF_PT_sb_animate"
    bl_order = 50
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text="Control Picker")

    @classmethod
    def poll(cls, context):
        return _is_pickable_rig(context.active_object)

    def draw(self, context):
        from boneforge.i18n import T
        layout = self.layout
        arm = context.active_object
        data = get_layout(arm)
        if data is None:
            layout.operator("boneforge.picker_regenerate",
                            text=T("Generate Picker"), icon='RESTRICT_SELECT_OFF')
            return

        edit_mode = edit_mode_enabled(arm)
        snap = snap_to_grid_enabled(arm)
        edit_row = layout.row(align=True)
        op = edit_row.operator("boneforge.picker_toggle_edit",
                               text=T("Edit Layout"),
                               icon='EDITMODE_HLT',
                               depress=edit_mode)
        op.enabled = not edit_mode
        op = edit_row.operator("boneforge.picker_toggle_snap",
                               text=T("Snap"),
                               icon='SNAP_ON',
                               depress=snap)
        op.enabled = not snap

        # group controls by row/group
        groups = {}
        for c in data.get("controls", []):
            groups.setdefault(c.get("group", "Controls"), []).append(c)
        for group in _layout.PICKER_GROUPS:
            ctrls = groups.get(group)
            if not ctrls:
                continue
            box = layout.box()
            header = box.row()
            op = header.operator("boneforge.picker_select_group",
                                 text=group, icon='GROUP_BONE')
            op.group = group
            grid = box.grid_flow(columns=4, even_columns=True)
            for c in sorted(ctrls, key=lambda x: x["id"]):
                op = grid.operator("boneforge.picker_select",
                                   text=c.get("label") or c["id"].replace("-", " "))
                op.bones = c["bone"]
            if edit_mode:
                edit_col = box.column(align=True)
                for c in sorted(ctrls, key=lambda x: x["id"]):
                    row = edit_col.row(align=True)
                    row.label(text=c.get("label") or c["id"],
                              icon='RESTRICT_SELECT_OFF')
                    for icon, dx, dy in (
                        ('TRIA_LEFT', -0.25, 0.0),
                        ('TRIA_RIGHT', 0.25, 0.0),
                        ('TRIA_UP', 0.0, -0.25),
                        ('TRIA_DOWN', 0.0, 0.25),
                    ):
                        op = row.operator("boneforge.picker_move_control",
                                          text="", icon=icon)
                        op.control_id = c["id"]
                        op.dx = dx
                        op.dy = dy
                    op = row.operator("boneforge.picker_resize_control",
                                      text="", icon='ADD')
                    op.control_id = c["id"]
                    op.dw = 0.25
                    op.dh = 0.25
                    op = row.operator("boneforge.picker_resize_control",
                                      text="", icon='REMOVE')
                    op.control_id = c["id"]
                    op.dw = -0.25
                    op.dh = -0.25
                    op = row.operator("boneforge.picker_relabel_control",
                                      text="", icon='FONT_DATA')
                    op.control_id = c["id"]
                    op.label = c.get("label") or c["id"]
        layout.separator(factor=0.5)
        layout.operator("boneforge.picker_regenerate",
                        text="Rebuild Layout", icon='FILE_REFRESH')


classes = (
    BF_OT_PickerSelect,
    BF_OT_PickerSelectGroup,
    BF_OT_PickerRegenerate,
    BONEFORGE_PT_picker,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
