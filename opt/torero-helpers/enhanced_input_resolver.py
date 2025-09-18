"""Enhanced input resolver with custom path support."""

from pathlib import Path
from typing import Optional, Dict
import os

class EnhancedPathResolver:
    """Resolves input file paths with support for multiple base directories."""

    # Define path shortcuts
    PATH_SHORTCUTS = {
        "@": "/home/admin/data",                                            # Default data directory
        "@data": "/home/admin/data",                                        # Explicit data directory
        "@inputs": "/home/admin/data/inputs",                               # Direct to inputs
        "@states": "/home/admin/data/states",                               # Direct to states
        "@configs": "/home/admin/data/configs",                             # Direct to configs
        "@repo": "/home/admin/repos",                                       # Repository directory
        "@temp": "/tmp",                                                    # Temporary files
        "@project": os.environ.get("PROJECT_DIR", "/home/admin/project"),   # Project-specific
        "@workspace": os.environ.get("WORKSPACE", "/home/admin/workspace"), # Workspace
    }

    @classmethod
    def resolve_path(cls, input_path: str) -> Path:
        """Resolve a path string to an absolute Path object.

        Args:
            input_path: Path string that may contain shortcuts

        Returns:
            Resolved absolute Path object

        Examples:
            "@/inputs/vpc.yaml"          -> /home/admin/data/inputs/vpc.yaml
            "@inputs/vpc.yaml"           -> /home/admin/data/inputs/vpc.yaml
            "@repo/showtime/config.yaml" -> /home/admin/repos/showtime/config.yaml
            "@temp/dynamic.tfvars"       -> /tmp/dynamic.tfvars
            "/absolute/path/file.yaml"   -> /absolute/path/file.yaml
            "./relative/file.yaml"       -> <cwd>/relative/file.yaml
        """

        # Handle shortcuts
        if input_path.startswith("@"):
            # Check for specific shortcuts
            for shortcut, base_path in cls.PATH_SHORTCUTS.items():
                if input_path.startswith(shortcut + "/"):
                    # Replace shortcut with base path
                    relative_part = input_path[len(shortcut) + 1:]
                    return Path(base_path) / relative_part
                elif input_path == shortcut:
                    # Just the shortcut itself
                    return Path(base_path)

            # Default @ handling (backward compatibility)
            if input_path.startswith("@/"):
                return Path("/home/admin/data") / input_path[2:]
            else:
                # @filename.yaml -> /home/admin/data/filename.yaml
                return Path("/home/admin/data") / input_path[1:]

        # Handle environment variable expansion
        if "$" in input_path:
            input_path = os.path.expandvars(input_path)

        # Handle home directory expansion
        if input_path.startswith("~"):
            return Path(input_path).expanduser().resolve()

        # Handle absolute and relative paths
        path = Path(input_path)
        if path.is_absolute():
            return path
        else:
            # Relative to current working directory
            return Path.cwd() / path

    @classmethod
    def add_custom_shortcut(cls, shortcut: str, base_path: str):
        """Add a custom path shortcut.

        Args:
            shortcut: The shortcut string (should start with @)
            base_path: The base path it resolves to
        """
        if not shortcut.startswith("@"):
            shortcut = "@" + shortcut
        cls.PATH_SHORTCUTS[shortcut] = base_path


# Example usage functions
def demonstrate_path_resolution():
    """Show examples of path resolution."""

    examples = [
        "@inputs/vpc.yaml",
        "@states/terraform.tfstate",
        "@repo/showtime/config.yaml",
        "@temp/generated.tfvars",
        "@project/settings.yaml",
        "/absolute/path/to/file.yaml",
        "./relative/path/file.json",
        "~/user/configs/personal.yaml",
        "$HOME/configs/env.tfvars",
    ]

    resolver = EnhancedPathResolver()

    print("Path Resolution Examples:")
    print("-" * 60)

    for example in examples:
        resolved = resolver.resolve_path(example)
        print(f"{example:<35} -> {resolved}")

    # Add custom shortcut
    resolver.add_custom_shortcut("@custom", "/opt/custom/configs")
    custom_path = resolver.resolve_path("@custom/special.yaml")
    print(f"{'@custom/special.yaml':<35} -> {custom_path}")


if __name__ == "__main__":
    demonstrate_path_resolution()