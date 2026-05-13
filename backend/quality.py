import py_compile
from pathlib import Path


def main() -> None:
    for path in Path(".").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        py_compile.compile(str(path), doraise=True)
    print("Backend quality check passed.")


if __name__ == "__main__":
    main()
