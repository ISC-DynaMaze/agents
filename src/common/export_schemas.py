import json
from pathlib import Path

from pydantic import BaseModel

from common.calibration import Calibration
from common.config import Config


def main():
    schemas_dir: Path = Path() / "src" / "common" / "schemas"
    schemas_dir.mkdir(exist_ok=True)
    exports: list[tuple[type[BaseModel], str]] = [
        (Config, "config"),
        (Calibration, "calibration"),
    ]

    for cls, name in exports:
        path: Path = schemas_dir / f"{name}.json"
        schema: str = json.dumps(cls.model_json_schema(), indent=4)
        path.write_text(schema)


if __name__ == "__main__":
    main()
