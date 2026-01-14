#!/usr/bin/env python3
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path):
    with path.open() as f:
        return yaml.safe_load(f)


def validate_schema(data: dict, schema: dict):
    missing = []
    for key in schema.get("required", []):
        if key not in data:
            missing.append(key)
    return missing


def main():
    if len(sys.argv) != 3:
        print("Usage: validate.py <schema.yml> <config.yml>")
        return 2

    schema_path = Path(sys.argv[1])
    config_path = Path(sys.argv[2])

    schema = load_yaml(schema_path)
    config = load_yaml(config_path)

    if not isinstance(schema, dict) or not isinstance(config, dict):
        print("Invalid schema or config format.")
        return 2

    missing = validate_schema(config, schema)
    if missing:
        print(f"Missing required sections: {', '.join(missing)}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
