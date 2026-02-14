"""Generate OpenAPI Specification

This script generates the OpenAPI spec from the FastAPI app.
"""

import json
from pathlib import Path

from app.main import app


def generate_openapi_spec():
    """Generate and save OpenAPI specification"""

    # Get OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Save to file
    output_dir = Path(__file__).parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "openapi.json"

    with open(output_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✅ OpenAPI specification generated: {output_file}")
    print(f"📊 Endpoints: {len([p for p in openapi_schema.get('paths', {}).values()])}")
    print(f"🏷️  Tags: {', '.join([t['name'] for t in openapi_schema.get('tags', [])])}")

    # Also create YAML version
    try:
        import yaml
        output_file_yaml = output_dir / "openapi.yaml"
        with open(output_file_yaml, "w") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)
        print(f"✅ YAML version: {output_file_yaml}")
    except ImportError:
        print("ℹ️  Install PyYAML to generate YAML version: pip install pyyaml")


if __name__ == "__main__":
    generate_openapi_spec()
