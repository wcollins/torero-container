#!/usr/bin/env python3
"""
Generate OpenAPI schema file for torero API

This script generates the OpenAPI schema file that can be committed to the repository
for use by MCP servers, documentation generation, and client SDK generation.
"""

import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from torero_api.server import create_app

def generate_openapi_schema(output_path: str = "openapi.json"):
    """
    Generate the OpenAPI schema and save it to a file.
    
    Args:
        output_path: Path where the OpenAPI schema file should be saved
    """

    # Create the FastAPI app
    app = create_app()
    
    # Generate the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the schema to file with pretty formatting
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"OpenAPI schema generated successfully: {output_file}")
    print(f"Schema version: {openapi_schema['info']['version']}")
    
    # Generate .yaml too!
    try:
        import yaml
        yaml_path = output_file.with_suffix('.yaml')
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)
        print(f"YAML schema also generated: {yaml_path}")
    except ImportError:
        print("PyYAML not installed - skipping YAML generation")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate OpenAPI schema for torero API")
    parser.add_argument(
        "-o", "--output", 
        default="docs/openapi.json",
        help="Output path for the OpenAPI schema file (default: docs/openapi.json)"
    )
    
    args = parser.parse_args()
    generate_openapi_schema(args.output)