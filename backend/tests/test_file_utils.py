from backend.utils.file_utils import chunk_text, detect_language
from pathlib import Path


def test_chunk_text_basic():
    text = "\n".join([f"line {i}" for i in range(1, 21)])  # 20 lines
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) > 1
    for content, start, end in chunks:
        assert isinstance(content, str)
        assert start >= 1
        assert end >= start


def test_chunk_text_small_file():
    text = "just one line"
    chunks = chunk_text(text, chunk_size=50, overlap=5)
    assert len(chunks) == 1
    assert chunks[0][0] == "just one line"


def test_detect_language():
    assert detect_language(Path("foo.py")) == "python"
    assert detect_language(Path("bar.ts")) == "typescript"
    assert detect_language(Path("baz.unknown")) == "unknown"
