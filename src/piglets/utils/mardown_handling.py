from pathlib import Path

def read_markdown_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")
