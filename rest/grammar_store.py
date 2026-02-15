import os
import glob


_RESOURCES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "resources"
)


def list_bundled() -> list[str]:
    """Return names (without extension) of bundled .bnf grammar files."""
    pattern = os.path.join(_RESOURCES_DIR, "*.bnf")
    return sorted(
        os.path.splitext(os.path.basename(f))[0]
        for f in glob.glob(pattern)
    )


def load_bundled(name: str) -> str:
    """Load raw text of a bundled grammar file by name."""
    path = os.path.join(_RESOURCES_DIR, f"{name}.bnf")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No bundled grammar named '{name}'")
    with open(path, "r") as f:
        return f.read()
