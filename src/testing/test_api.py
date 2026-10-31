# tests for the API in main.py
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def fake_answer(question):
    return {"answer": "fake answer", "source": "Page 1"}


def test_ask_works(monkeypatch):
    monkeypatch.setattr(main, "answer_question", fake_answer)
    response = client.post("/ask", json={"question": "What is the attendance requirement?"})
    assert response.status_code == 200
    assert response.json() == {"answer": "fake answer", "source": "Page 1"}


def test_ask_missing_question():
    response = client.post("/ask", json={"hello": "world"})
    assert response.status_code == 400
    assert response.json()["error"] == "Missing question"


def test_ask_empty_question():
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 400


def test_ask_question_not_text():
    response = client.post("/ask", json={"question": 123})
    assert response.status_code == 400


def test_ask_bad_json():
    response = client.post("/ask", content="this is not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid JSON"


def test_ask_json_list():
    response = client.post("/ask", json=["question"])
    assert response.status_code == 400


def test_ask_server_error(monkeypatch):
    def broken(question):
        raise Exception("boom")
    monkeypatch.setattr(main, "answer_question", broken)
    response = client.post("/ask", json={"question": "hi"})
    assert response.status_code == 500
    assert "error" in response.json()


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Handbook Assistant" in response.text
