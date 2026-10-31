# tests for src/retrieve.py
import src.retrieve as rag
from src.retrieve import is_answer_found, build_prompt


def test_is_answer_found_good_chunk():
    chunks = [{"text": "x", "page": 1, "distance": 0.5}]
    assert is_answer_found(chunks) == True


def test_is_answer_found_bad_chunks():
    chunks = [{"text": "x", "page": 1, "distance": 1.9}, {"text": "y", "page": 2, "distance": 1.8}]
    assert is_answer_found(chunks) == False


def test_is_answer_found_second_chunk_good():
    chunks = [{"text": "x", "page": 1, "distance": 1.9}, {"text": "y", "page": 2, "distance": 0.9}]
    assert is_answer_found(chunks) == True


def test_is_answer_found_empty():
    assert is_answer_found([]) == False


def test_build_prompt_has_question_and_pages():
    chunks = [{"text": "Fees are R 38,950", "page": 16, "distance": 0.4}]
    prompt = build_prompt("How much are the fees?", chunks)
    assert "How much are the fees?" in prompt
    assert "[Page 16]" in prompt
    assert "Fees are R 38,950" in prompt


def test_answer_question_not_found(monkeypatch):
    monkeypatch.setattr(rag, "get_collection", lambda: "fake")
    monkeypatch.setattr(rag, "search_handbook", lambda q, c, m, cc, n: [{"text": "x", "page": 1, "distance": 1.9}])
    result = rag.answer_question("What is the capital of France?")
    assert result["answer"] == "I could not find that information in the handbook."
    assert result["source"] == "Not found"


def test_answer_question_uses_llm(monkeypatch):
    monkeypatch.setattr(rag, "get_collection", lambda: "fake")
    monkeypatch.setattr(rag, "search_handbook", lambda q, c, m, cc, n: [{"text": "Fees are R 38,950", "page": 16, "distance": 0.4}])
    monkeypatch.setattr(rag, "ask_llm", lambda prompt: "The fees are R 38,950.")
    result = rag.answer_question("How much are the fees?")
    assert result == {"answer": "The fees are R 38,950.", "source": "Page 16"}


def test_answer_question_no_llm_uses_chunk(monkeypatch):
    monkeypatch.setattr(rag, "get_collection", lambda: "fake")
    monkeypatch.setattr(rag, "search_handbook", lambda q, c, m, cc, n: [{"text": " Fees are R 38,950 ", "page": 16, "distance": 0.4}])
    monkeypatch.setattr(rag, "ask_llm", lambda prompt: None)
    result = rag.answer_question("How much are the fees?")
    assert result == {"answer": "Fees are R 38,950", "source": "Page 16"}


def test_answer_question_llm_says_not_found(monkeypatch):
    monkeypatch.setattr(rag, "get_collection", lambda: "fake")
    monkeypatch.setattr(rag, "search_handbook", lambda q, c, m, cc, n: [{"text": "abc", "page": 3, "distance": 0.4}])
    monkeypatch.setattr(rag, "ask_llm", lambda prompt: "I could not find that information in the handbook.")
    result = rag.answer_question("Who won the world cup?")
    assert result["source"] == "Not found"


def test_answer_question_no_database(monkeypatch):
    monkeypatch.setattr(rag, "get_collection", lambda: None)
    result = rag.answer_question("anything")
    assert "Error" in result["answer"]
