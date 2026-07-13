from pathlib import Path

# Extensions we attempt to read and index
SUPPORTED_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".cpp", ".c", ".h",
    ".cs", ".rb", ".php", ".swift", ".kt",
    ".scala", ".r", ".sh", ".yaml", ".yml",
    ".json", ".toml", ".md", ".sql", ".html", ".css",
}

# Directories to skip during traversal
IGNORED_DIRS: set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".idea", ".vscode", "coverage",
}


def is_supported_file(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
        and not any(part in IGNORED_DIRS for part in path.parts)
    )


def iter_source_files(root: Path):
    """Yield all supported source files under *root*, skipping ignored dirs."""
    for item in root.rglob("*"):
        if is_supported_file(item):
            yield item


def detect_language(path: Path) -> str:
    extension_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript", ".jsx": "javascript", ".java": "java",
        ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
        ".h": "c", ".cs": "csharp", ".rb": "ruby", ".php": "php",
        ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
        ".r": "r", ".sh": "bash", ".sql": "sql", ".md": "markdown",
        ".html": "html", ".css": "css", ".json": "json",
        ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    }
    return extension_map.get(path.suffix.lower(), "unknown")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[tuple[str, int, int]]:
    """Split *text* into overlapping chunks.

    Returns list of (chunk_content, start_line, end_line).
    """
    lines = text.splitlines()
    chunks: list[tuple[str, int, int]] = []
    i = 0
    while i < len(lines):
        end = min(i + chunk_size, len(lines))
        chunk_lines = lines[i:end]
        chunks.append(("\n".join(chunk_lines), i + 1, end))
        if end == len(lines):
            break
        i += chunk_size - overlap
    return chunks
