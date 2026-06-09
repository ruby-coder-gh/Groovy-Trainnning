"""
📄 File Reader Tool (Stretch Goal)

Allows the agent to read files from the local filesystem.

Includes safety restrictions to prevent reading sensitive files.
"""

import os
from pathlib import Path
from typing import Optional, List

# Directories that are OFF-LIMITS for reading
BLOCKED_PATHS = [
    "/etc",
    "/sys",
    "/proc",
    "/dev",
    "/var/root",
    os.path.expanduser("~/.ssh"),
    os.path.expanduser("~/.aws"),
    os.path.expanduser("~/.config"),
    os.path.expanduser("~/.gnupg"),
    "/usr/share",
    "/opt",
]

# File extensions that are allowed to be read
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".csv", ".tsv", ".xml", ".html", ".css", ".scss",
    ".sh", ".bash", ".zsh", ".env.example",
    ".sql", ".rb", ".go", ".rs", ".java", ".kt",
    ".c", ".cpp", ".h", ".hpp",
    ".log", ".out",
    ".yml", ".yaml",
    ".cfg", ".conf",
}


def read_file(path: str, max_lines: int = 100) -> str:
    """
    Read the contents of a file from the local filesystem.

    Args:
        path: Absolute or relative path to the file
        max_lines: Maximum number of lines to read (default 100, max 500)

    Returns:
        File contents as a string
    """
    try:
        # Resolve absolute path (handles symlinks like /etc -> /private/etc on macOS)
        full_path = Path(path).resolve()
        full_str = str(full_path)

        # Check if file exists
        if not full_path.exists():
            return f"❌ File not found: {path}"
        if not full_path.is_file():
            return f"❌ Not a file: {path}"

        # Security: check blocked paths (check both resolved path and original)
        check_paths = [full_str, str(Path(path).resolve())]
        for p in check_paths:
            for blocked in BLOCKED_PATHS:
                resolved_blocked = str(Path(blocked).resolve())
                if p.startswith(blocked) or p.startswith(resolved_blocked):
                    return f"❌ Access denied: cannot read files in {blocked}"

        # Security: check file extension
        ext = full_path.suffix.lower()
        # Reject hidden files (starting with dot) that have no recognized extension
        name = full_path.name
        if name.startswith(".") and ext not in ALLOWED_EXTENSIONS:
            return (
                f"❌ Cannot read hidden/system file '{name}'. "
                f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        if ext and ext not in ALLOWED_EXTENSIONS:
            return (
                f"❌ Cannot read .{ext} files. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Check file size (max 1MB)
        size_kb = full_path.stat().st_size / 1024
        if size_kb > 1024:
            return f"❌ File too large: {size_kb:.1f} KB (max 1024 KB)"

        # Read file
        max_lines = min(max_lines, 500)
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... (truncated at {max_lines} lines, file continues)")
                    break
                lines.append(line.rstrip())

        content = "\n".join(lines)
        total_lines = sum(1 for _ in open(full_path, "rb"))

        header = f"📄 {full_path.name} ({size_kb:.1f} KB, {total_lines} lines)"
        if total_lines > max_lines:
            header += f" [showing first {max_lines}]"

        return header + "\n" + "-" * 40 + "\n" + content

    except PermissionError:
        return f"❌ Permission denied: {path}"
    except UnicodeDecodeError:
        return f"❌ Cannot read binary file: {path}"
    except Exception as e:
        return f"❌ Error reading file '{path}': {e}"


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "read_file",
    "description": "Read the contents of a text file from the local filesystem (max 500 lines, 1MB). Cannot read system files or binary files.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file (absolute or relative to project root)",
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read (1–500, default 100)",
                "default": 100,
            },
        },
        "required": ["path"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("📄 File Reader Tool Test")
    print("-" * 40)

    # Read this file
    result = read_file(__file__, max_lines=20)
    print(result)

    print("\n--- Attempt blocked path ---")
    print(read_file("/etc/passwd"))

    print("\n--- Attempt wrong extension ---")
    print(read_file("/Users/nikunjvaghasiya/Groovy Training/.DS_Store"))
