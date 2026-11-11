from pathlib import Path


def test_show_project_structure():

    project_root = Path(__file__).resolve().parent.parent

    print("\nPROJECT ROOT:", project_root)

    print("\nFOLDERS FOUND:")

    for item in project_root.iterdir():
        print(item.name)

    assert (project_root / "srs").is_dir()
    assert (project_root / "srs").is_dir()