"""Run BoneForge BFA behavioural tests inside Bforartists (background).

Usage:
    bforartists --background --python tests/run_headless.py
Exits non-zero on failure so it can gate CI / a build loop.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))   # tests/
ROOT = os.path.dirname(HERE)                         # repo root
for p in (ROOT, HERE):                               # boneforge + test modules
    if p not in sys.path:
        sys.path.insert(0, p)


def main():
    import test_rig_build
    test_rig_build.run()
    print("\nALL IN-HOST RIG TESTS PASS")

    import test_control_layer
    test_control_layer.run()

    import test_face
    test_face.run()

    import test_retarget
    test_retarget.run()

    import test_picker
    test_picker.run()

    import test_detection
    test_detection.run()

    import test_export
    test_export.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
