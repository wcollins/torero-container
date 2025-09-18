"""input resolver for translating input files and variables to CLI arguments."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class InputResolver:
    """resolves inputs from files and converts to CLI arguments."""

    @staticmethod
    def resolve_path(path: str) -> Path:
        """resolve @ notation and relative paths."""
        if path.startswith('@'):

            # @ notation relative to /home/admin/data
            return Path('/home/admin/data') / path[1:]
        return Path(path).resolve()

    @staticmethod
    def parse_tfvars(content: str) -> Dict[str, Any]:
        """parse Terraform .tfvars format."""

        variables = {}
        lines = content.strip().split('\n')

        current_key = None
        current_value = []
        in_multiline = False

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' in line and not in_multiline:
                parts = line.split('=', 1)
                key = parts[0].strip()
                value = parts[1].strip()

                # handle multiline values (like objects/maps)
                if value.startswith('{') and not value.endswith('}'):
                    current_key = key
                    current_value = [value]
                    in_multiline = True
                else:
                    # simple value
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]  # remove quotes
                    variables[key] = value
            elif in_multiline:
                current_value.append(line)
                if line.endswith('}'):
                    # end of multiline value
                    variables[current_key] = ' '.join(current_value)
                    current_key = None
                    current_value = []
                    in_multiline = False

        return {'variables': variables}

    @classmethod
    def load_input_file(cls, file_path: str) -> Dict[str, Any]:
        """load and parse input file based on extension."""

        resolved_path = cls.resolve_path(file_path)

        if not resolved_path.exists():
            logger.error(f"input file not found: {resolved_path}")
            return {}

        suffix = resolved_path.suffix.lower()

        try:
            if suffix in ['.yaml', '.yml']:
                with open(resolved_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            elif suffix == '.json':
                with open(resolved_path, 'r') as f:
                    return json.load(f)
            elif suffix == '.tfvars':
                with open(resolved_path, 'r') as f:
                    return cls.parse_tfvars(f.read())
            else:
                logger.warning(f"unsupported input file format: {suffix}")
                return {}
        except Exception as e:
            logger.error(f"error parsing input file {resolved_path}: {e}")
            return {}

    @staticmethod
    def flatten_value(value: Any) -> str:
        """convert complex values to string format for CLI."""
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(',', ':'))
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif value is None:
            return ''
        else:
            return str(value)

    @classmethod
    def resolve_inputs(cls,
                      user_inputs: Optional[Dict] = None,
                      input_file: Optional[str] = None) -> Dict[str, Any]:

        """resolve inputs from all sources."""
        resolved = {}

        # load from input file if provided
        if input_file:
            file_inputs = cls.load_input_file(input_file)
            resolved.update(file_inputs)

        # apply user-provided inputs (highest priority)
        if user_inputs:

            # merge variables
            if 'variables' in user_inputs:
                if 'variables' not in resolved:
                    resolved['variables'] = {}
                resolved['variables'].update(user_inputs['variables'])

            # merge secrets
            if 'secrets' in user_inputs:
                resolved['secrets'] = user_inputs.get('secrets', [])

            # handle files
            if 'files' in user_inputs:
                resolved['files'] = user_inputs.get('files', {})

        return resolved

    @classmethod
    def to_cli_args(cls, service_type: str, inputs: Dict[str, Any]) -> List[str]:
        """convert resolved inputs to CLI arguments for torero."""
        args = []

        # handle variables - torero uses --set for ALL service types
        variables = inputs.get('variables', {})
        for key, value in variables.items():
            flat_value = cls.flatten_value(value)
            args.extend(['--set', f'{key}={flat_value}'])

        # handle secrets - torero uses --set-secret
        secrets = inputs.get('secrets', [])
        for secret in secrets:
            args.extend(['--set-secret', secret])

        # handle state file for opentofu
        if service_type == 'opentofu-plan' and 'files' in inputs:
            if 'state_file' in inputs['files']:
                state_path = cls.resolve_path(inputs['files']['state_file'])
                args.extend(['--state', f'@{state_path}'])

        return args