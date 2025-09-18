"""unified input resolver for torero services."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class UnifiedInputResolver:
    """resolves inputs from multiple sources into CLI arguments."""

    def __init__(self, executor):
        self.executor = executor
        self.input_manager = ServiceInputManager()

    def resolve_inputs(
        self,
        service_name: str,
        service_type: str,
        user_inputs: Dict = None,
        input_file: str = None
    ) -> Dict[str, Any]:
        """resolve inputs from all sources.

        Priority order: User inputs > File inputs > Manifest defaults > Service defaults
        """
        resolved = {}

        # 1. load service defaults
        manifest = self.input_manager.discover_inputs(service_name)
        if manifest:
            resolved.update(self.extract_defaults(manifest))

        # 2. load from input file if provided
        if input_file:
            file_inputs = self.load_input_file(input_file)
            if file_inputs:
                resolved = self.merge_inputs(resolved, file_inputs)

        # 3. apply user-provided inputs (highest priority)
        if user_inputs:
            resolved = self.merge_inputs(resolved, user_inputs)

        # 4. validate resolved inputs
        valid, errors = self.input_manager.validate_inputs(service_name, resolved)
        if not valid:
            raise ValueError(f"input validation failed: {', '.join(errors)}")

        return resolved

    def extract_defaults(self, manifest: Dict) -> Dict:
        """extract default values from manifest."""
        defaults = {
            "variables": {},
            "secrets": [],
            "files": {}
        }

        # extract variable defaults
        for var_def in manifest.get("inputs", {}).get("variables", []):
            if "default" in var_def:
                defaults["variables"][var_def["name"]] = var_def["default"]

        # extract file defaults
        for file_def in manifest.get("inputs", {}).get("files", []):
            if "default" in file_def:
                defaults["files"][file_def["name"]] = file_def["default"]

        return defaults

    def load_input_file(self, input_file: str) -> Optional[Dict]:
        """load inputs from a file."""
        path = Path(input_file)

        # handle @ notation for relative paths
        if input_file.startswith("@"):
            path = Path("/home/admin/data") / input_file[1:]

        if not path.exists():
            logger.warning(f"input file not found: {path}")
            return None

        try:
            # determine file format from extension
            suffix = path.suffix.lower()

            if suffix in [".yaml", ".yml"]:
                with open(path, 'r') as f:
                    return yaml.safe_load(f)

            elif suffix == ".json":
                with open(path, 'r') as f:
                    return json.load(f)

            elif suffix == ".tfvars":
                # parse terraform variable file
                return self.parse_tfvars(path)

            elif suffix == ".toml":
                # parse TOML file (for Python services)
                try:
                    import toml
                    with open(path, 'r') as f:
                        return toml.load(f)
                except ImportError:
                    logger.warning("toml library not available, cannot parse .toml files")
                    return None

            else:
                logger.warning(f"unsupported input file format: {suffix}")
                return None

        except Exception as e:
            logger.error(f"failed to load input file {path}: {e}")
            return None

    def parse_tfvars(self, path: Path) -> Dict:
        """parse terraform variable file format."""
        variables = {}
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    variables[key] = value

        return {"variables": variables}

    def merge_inputs(self, base: Dict, override: Dict) -> Dict:
        """merge two input dictionaries, with override taking precedence."""
        merged = base.copy()

        # merge variables
        if "variables" in override:
            if "variables" not in merged:
                merged["variables"] = {}
            merged["variables"].update(override["variables"])

        # merge secrets (append unique)
        if "secrets" in override:
            if "secrets" not in merged:
                merged["secrets"] = []
            for secret in override["secrets"]:
                if secret not in merged["secrets"]:
                    merged["secrets"].append(secret)

        # merge files
        if "files" in override:
            if "files" not in merged:
                merged["files"] = {}
            merged["files"].update(override["files"])

        return merged

    def to_cli_args(self, service_type: str, resolved_inputs: Dict, operation: str = None) -> List[str]:
        """convert resolved inputs to CLI arguments.

        Note: torero uses --set for all service types, not native flags like --var
        """
        args = []

        if service_type == "ansible-playbook":
            # convert to --set format for variables
            for key, value in resolved_inputs.get("variables", {}).items():
                if isinstance(value, (dict, list)):
                    # complex values need JSON encoding
                    args.extend(["--set", f"{key}={json.dumps(value)}"])
                else:
                    args.extend(["--set", f"{key}={value}"])

            # add inventory if specified
            if "inventory" in resolved_inputs.get("files", {}):
                args.extend(["--inventory", resolved_inputs["files"]["inventory"]])

        elif service_type == "opentofu-plan":
            # convert to --set format (torero uses --set, not --var)
            for key, value in resolved_inputs.get("variables", {}).items():
                args.extend(["--set", f"{key}={value}"])

            # add var file if specified
            if "var_file" in resolved_inputs.get("files", {}):
                args.extend(["--var-file", resolved_inputs["files"]["var_file"]])

            # add state file if specified
            if "state_file" in resolved_inputs.get("files", {}):
                args.extend(["--state", resolved_inputs["files"]["state_file"]])

        elif service_type == "python-script":
            # convert to --set format for environment variables
            for key, value in resolved_inputs.get("variables", {}).items():
                args.extend(["--set", f"{key}={value}"])

        # add secrets using --set-secret
        for secret in resolved_inputs.get("secrets", []):
            args.extend(["--set-secret", secret])

        return args


class ServiceInputManager:
    """manages service input manifests - simplified version for MCP."""

    def __init__(self):
        self.manifest_dir = Path("/home/admin/data/schemas")

    def discover_inputs(self, service_name: str) -> Optional[Dict]:
        """discover inputs from manifest file."""
        manifest_path = self.manifest_dir / f"{service_name}.yaml"
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"failed to load manifest {manifest_path}: {e}")
        return None

    def validate_inputs(self, service_name: str, inputs: Dict) -> tuple[bool, List[str]]:
        """validate inputs against service manifest."""
        manifest = self.discover_inputs(service_name)
        if not manifest:
            return True, []  # no manifest, skip validation

        errors = []

        # validate required variables
        for input_def in manifest.get("inputs", {}).get("variables", []):
            if input_def.get("required") and input_def["name"] not in inputs.get("variables", {}):
                errors.append(f"required input '{input_def['name']}' is missing")

        # validate required secrets
        for secret_def in manifest.get("inputs", {}).get("secrets", []):
            if secret_def.get("required") and secret_def["name"] not in inputs.get("secrets", []):
                errors.append(f"required secret '{secret_def['name']}' is missing")

        return len(errors) == 0, errors