# tests for src/ingest.py
from src.ingest import fix_spaced_text, split_into_chunks, extract_text, load_pdf


def test_fix_spaced_text():
    text = "W e l c o m e  t o  Z A I O"
    assert fix_spaced_text(text) == "Welcome to ZAIO"


def test_fix_spaced_text_many_lines():
    text = "H e l l o  w o r l d\nB y e"
    assert fix_spaced_text(text) == "Hello world\nBye"


def test_split_into_chunks_small_page():
    pages = [{"page": 1, "text": "This is a small page with some text in it."}]
    chunks = split_into_chunks(pages)
    assert len(chunks) == 1
    assert chunks[0]["page"] == 1


def test_split_into_chunks_big_page():
    pages = [{"page": 5, "text": "a" * 1200}]
    chunks = split_into_chunks(pages)
    # 1200 chars, chunk 500, step 400 -> starts at 0, 400, 800
    assert len(chunks) == 3
    for c in chunks:
        assert c["page"] == 5
        assert len(c["text"]) <= 500


def test_split_into_chunks_skips_empty():
    pages = [{"page": 1, "text": "   "}]
    chunks = split_into_chunks(pages)
    assert len(chunks) == 0


def test_load_pdf_missing_file():
    assert load_pdf("this_file_does_not_exist.pdf") == None


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


def test_extract_text_fixes_spaced_pages():
    pages = [FakePage("F e e s  a r e  h i g h"), FakePage("Normal text here")]
    result = extract_text(pages)
    assert result[0] == {"page": 1, "text": "Fees are high"}
    assert result[1] == {"page": 2, "text": "Normal text here"}


def test_extract_text_none_page():
    result = extract_text([FakePage(None)])
    assert result[0]["text"] == ""
