from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "boneforge" / "vrchat" / "cats" / "material_atlas.py"
UV_PACKING = ROOT / "boneforge" / "vrchat" / "cats" / "uv_tools" / "packing.py"
SIDEBAR = ROOT / "boneforge" / "taskboard" / "sidebar.py"
CATS_PANEL = ROOT / "boneforge" / "vrchat" / "cats" / "cats_panel.py"
INIT = ROOT / "boneforge" / "__init__.py"


def test_material_atlas_has_selectable_sources():
    source = ATLAS.read_text(encoding="utf-8")

    assert "class BF_AtlasMaterialItem" in source
    assert "class BF_AtlasTextureItem" in source
    assert "class BF_UL_VRC_AtlasMaterials" in source
    assert "class BF_UL_VRC_AtlasTextures" in source
    assert "_populate_group_sources(group, objs)" in source
    assert "_group_enabled_material_count(group)" in source
    assert "_group_enabled_texture_count(group)" in source
    assert "def _route_source_image_nodes_to_uv" in source
    assert "def _route_vector_socket_to_uv" in source
    assert "upstream_input = getattr(link.from_node" in source
    assert 'uv.active_render = (uv.name == "atlas_uv")' in source


def test_material_atlas_has_quality_parity_wiring():
    source = ATLAS.read_text(encoding="utf-8")

    assert "from boneforge.vrchat.cats.material_atlas_quality import" in source
    assert "diagnostic_status: StringProperty" in source
    assert "role: EnumProperty" in source
    assert "size_override: BoolProperty" in source
    assert "packing_preset: EnumProperty" in source
    assert "bake_metallic: BoolProperty" in source
    assert "channel_pack_orm: BoolProperty" in source
    assert "build_multipass_output_plan(" in source
    assert "build_channel_pack_plan(" in source
    assert "Extra output planned" in source
    assert "BF_ATLAS_TARGET" in source


def test_material_atlas_avoids_object_select_all_poll_failure():
    source = ATLAS.read_text(encoding="utf-8")

    assert "bpy.ops.object.select_all(" not in source
    assert "def _deselect_all_objects_directly" in source
    assert "def _ensure_object_mode" in source
    assert "def _run_with_view3d_context" in source
    assert "Bake atlas texture" in source


def test_material_atlas_has_smart_combine_validation_guards():
    source = ATLAS.read_text(encoding="utf-8")

    assert "def _assign_single_atlas_material" in source
    assert "poly.material_index = 0" in source
    assert "def _validate_atlas_mesh" in source
    assert "_validate_atlas_mesh(joined, atlas_mat)" in source
    assert "Source textures forced to sample original UVs during bake" in source
    assert "Atlas mesh validated before originals are hidden" in source
    assert "boneforge_atlas_source_uv_routes" in source


def test_material_atlas_exports_atlas_uv_as_uv0_by_default():
    source = ATLAS.read_text(encoding="utf-8")

    assert "keep_source_uv_maps: BoolProperty" in source
    assert "default=False" in source
    assert "def _prepare_atlas_uv_for_export" in source
    assert 'if uv.name != "atlas_uv":' in source
    assert "mesh.uv_layers.remove(uv)" in source
    assert "mesh.uv_layers.active_index = index" in source
    assert "atlas_uv becomes UV0" in source
    assert "boneforge_atlas_uv0" in source


def test_material_atlas_has_bfa_uv_method_integration():
    source = ATLAS.read_text(encoding="utf-8")
    uv_source = UV_PACKING.read_text(encoding="utf-8")

    assert "from boneforge.vrchat.cats.uv_tools import" in source
    assert "apply_atlas_uv_method(context, joined, settings" in source
    assert "summarize_atlas_uv_result(uv_result)" in source
    assert "items=atlas_uv_method_items(include_advanced=True)" in source
    assert "uv_rotation_step" in source
    assert "BFA_RANDOM_ORIENTED" in uv_source
    assert "Advanced Variation" in uv_source


def test_taskboard_icons_are_valid_for_bforartists_52():
    source = SIDEBAR.read_text(encoding="utf-8")
    cats_panel = CATS_PANEL.read_text(encoding="utf-8")

    assert "SEQUENCE_COLOR_" not in source
    assert "SEQUENCE_COLOR_" not in cats_panel
    assert "STRIP_COLOR_01" in source
    assert "STRIP_COLOR_04" in source
    assert "STRIP_COLOR_05" in source
    assert "STRIP_COLOR_04" in cats_panel


def test_bfa_release_identity_and_lockout_files():
    init_source = INIT.read_text(encoding="utf-8")

    assert '"name": "BoneForge BFA"' in init_source
    assert '"version": (8, 4, 6)' in init_source
    assert (ROOT / "boneforge" / "bfa_guard.py").exists()
    assert (ROOT / "boneforge" / "BFA_EXCLUSIVE.md").exists()
    assert (ROOT / "releases" / "BoneForge-BFA-8.4.6.zip").exists()
