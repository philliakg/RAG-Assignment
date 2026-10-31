# tests for the LLM_PROVIDER setting and the API keys (authentication) in src/retrieve.py
# we never call the real Claude / ChatGPT / Gemini here, we use fake clients instead
import os
import src.retrieve as retrieve


# remembers what was sent to the fake llm so the tests can check it
last_call = {}


# ---------- fake claude ----------

class FakeBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class FakeResponse:
    def __init__(self, text, stop_reason):
        self.content = [FakeBlock(text)]
        self.stop_reason = stop_reason


class FakeMessages:
    def create(self, **kwargs):
        last_call.clear()
        last_call.update(kwargs)
        return FakeResponse("The fees are R 38,950.", "end_turn")


class FakeBeta:
    def __init__(self):
        self.messages = FakeMessages()


class FakeClient:
    def __init__(self):
        self.beta = FakeBeta()


class BadKeyMessages:
    def create(self, **kwargs):
        raise Exception("Error code: 401 - invalid x-api-key")


class BadKeyClient:
    def __init__(self):
        self.beta = FakeBeta()
        self.beta.messages = BadKeyMessages()


class RefusalMessages:
    def create(self, **kwargs):
        return FakeResponse("", "refusal")


class RefusalClient:
    def __init__(self):
        self.beta = FakeBeta()
        self.beta.messages = RefusalMessages()


# ---------- fake openai (chatgpt) ----------

class FakeOpenAIMessage:
    def __init__(self, text):
        self.content = text


class FakeOpenAIChoice:
    def __init__(self, text):
        self.message = FakeOpenAIMessage(text)


class FakeOpenAIResponse:
    def __init__(self, text):
        self.choices = [FakeOpenAIChoice(text)]


class FakeOpenAICompletions:
    def create(self, **kwargs):
        last_call.clear()
        last_call.update(kwargs)
        return FakeOpenAIResponse("ChatGPT says the fees are R 38,950.")


class FakeOpenAIChat:
    def __init__(self):
        self.completions = FakeOpenAICompletions()


class FakeOpenAIClient:
    def __init__(self):
        self.chat = FakeOpenAIChat()


# ---------- fake gemini ----------

class FakeGeminiResponse:
    def __init__(self, text):
        self.text = text


class FakeGeminiModels:
    def generate_content(self, **kwargs):
        last_call.clear()
        last_call.update(kwargs)
        return FakeGeminiResponse("Gemini says the fees are R 38,950.")


class FakeGeminiClient:
    def __init__(self):
        self.models = FakeGeminiModels()


def use_provider(monkeypatch, provider):
    # set the provider and make sure a model name from the real .env doesn't get in the way
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.delenv("LLM_MODEL", raising=False)


# ---------- claude tests ----------

def test_no_api_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "claude")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert retrieve.ask_llm("hello") == None


def test_empty_api_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    assert retrieve.ask_llm("hello") == None


def test_wrong_api_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-wrong")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", BadKeyClient)
    assert retrieve.ask_llm("hello") == None


def test_good_api_key_returns_answer(monkeypatch):
    use_provider(monkeypatch, "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", FakeClient)
    assert retrieve.ask_llm("How much are the fees?") == "The fees are R 38,950."
    assert last_call["model"] == "claude-opus-5-5"
    assert last_call["messages"][0]["content"] == "How much are the fees?"


def test_refusal_returns_none(monkeypatch):
    use_provider(monkeypatch, "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", RefusalClient)
    assert retrieve.ask_llm("hello") == None


def test_wrong_key_still_gives_handbook_answer(monkeypatch):
    # if the key is wrong the user should still get the handbook text back
    use_provider(monkeypatch, "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-wrong")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", BadKeyClient)
    monkeypatch.setattr(retrieve, "get_collection", lambda: "fake")
    monkeypatch.setattr(retrieve, "search_handbook", lambda q, c, m, cc, n: [{"text": "Total Fees: R 38,950", "page": 16, "distance": 0.4}])
    result = retrieve.answer_question("How much are the fees?")
    assert result == {"answer": "Total Fees: R 38,950", "source": "Page 16"}


# ---------- LLM_PROVIDER tests ----------

def test_default_provider_is_claude(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", FakeClient)
    assert retrieve.ask_llm("hi") == "The fees are R 38,950."


def test_provider_name_ignores_case_and_spaces(monkeypatch):
    use_provider(monkeypatch, "  Claude ")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", FakeClient)
    assert retrieve.ask_llm("hi") == "The fees are R 38,950."


def test_unknown_provider_returns_none(monkeypatch):
    use_provider(monkeypatch, "llama")
    assert retrieve.ask_llm("hi") == None


def test_llm_model_setting_changes_model(monkeypatch):
    use_provider(monkeypatch, "claude")
    monkeypatch.setenv("LLM_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(retrieve.anthropic, "Anthropic", FakeClient)
    retrieve.ask_llm("hi")
    assert last_call["model"] == "claude-sonnet-5-5"


# ---------- openai (chatgpt) tests ----------

def test_openai_no_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert retrieve.ask_llm("hello") == None


def test_openai_good_key_returns_answer(monkeypatch):
    use_provider(monkeypatch, "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(retrieve.openai, "OpenAI", FakeOpenAIClient)
    assert retrieve.ask_llm("How much are the fees?") == "ChatGPT says the fees are R 38,950."
    assert last_call["model"] == "gpt-5-nano"
    assert last_call["messages"][1]["content"] == "How much are the fees?"


def test_openai_wrong_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-wrong")
    def broken():
        raise Exception("Error code: 401 - Incorrect API key provided")
    monkeypatch.setattr(retrieve.openai, "OpenAI", broken)
    assert retrieve.ask_llm("hello") == None


# ---------- gemini tests ----------

def test_gemini_no_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert retrieve.ask_llm("hello") == None


def test_gemini_good_key_returns_answer(monkeypatch):
    use_provider(monkeypatch, "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(retrieve.genai, "Client", FakeGeminiClient)
    assert retrieve.ask_llm("How much are the fees?") == "Gemini says the fees are R 38,950."
    assert last_call["model"] == "gemini-3.8-flash"
    assert last_call["contents"] == "How much are the fees?"


def test_gemini_wrong_key_returns_none(monkeypatch):
    use_provider(monkeypatch, "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "wrong")
    def broken():
        raise Exception("400 INVALID_ARGUMENT. API key not valid")
    monkeypatch.setattr(retrieve.genai, "Client", broken)
    assert retrieve.ask_llm("hello") == None


# ---------- .env.example file ----------
# we test .env.example and not .env, because .env has the real keys and is not uploaded

def test_env_example_has_settings():
    # the .env.example file must be in the project folder and have all the setting names in it
    assert os.path.exists(".env.example")
    f = open(".env.example")
    text = f.read()
    f.close()
    assert "LLM_PROVIDER=" in text
    assert "ANTHROPIC_API_KEY=" in text
    assert "OPENAI_API_KEY=" in text
    assert "GEMINI_API_KEY=" in text


def test_env_example_has_no_real_keys():
    # make sure nobody pasted a real key into the example file by mistake
    f = open(".env.example")
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.startswith("ANTHROPIC_API_KEY=") or line.startswith("OPENAI_API_KEY=") or line.startswith("GEMINI_API_KEY="):
            value = line.split("=")[1].strip()
            assert value == ""
