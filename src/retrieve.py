# src/retrieve.py
# This is the "brain". It finds the right chunks and asks the LLM (Claude, ChatGPT or Gemini) to answer.

import os
import chromadb
from sentence_transformers import SentenceTransformer
import anthropic
import openai
from google import genai
from dotenv import load_dotenv

# read LLM_PROVIDER and the api keys from the .env file
load_dotenv()

# load the model and database when the file is imported so we only do it once
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="vectorstore")


def get_collection():
    try:
        collection = chroma_client.get_collection("handbook")
        return collection
    except:
        print("ERROR: no collection, did you run src/ingest.py?")
        return None


def search_handbook(question, collection, model, chroma_client, n):
    # TODO: chroma_client is not needed here but i pass it just in case
    # 1. turn the question into an embedding
    question_embedding = model.encode([question])[0].tolist()
    # 2. search the database
    results = collection.query(query_embeddings=[question_embedding], n_results=n)
    # 3. put the results in a nicer list
    found = []
    for i in range(len(results["documents"][0])):
        found.append({
            "text": results["documents"][0][i],
            "page": results["metadatas"][0][i]["page"],
            "distance": results["distances"][0][i],
        })
    return found


def is_answer_found(chunks):
    # check if the chunks are good enough to answer the question
    # smaller distance = more similar
    found = False
    if len(chunks) > 0:
        if chunks[0]["distance"] < 1.5:
            found = True
        else:
            if len(chunks) > 1:
                if chunks[1]["distance"] < 1.5:
                    found = True
                else:
                    found = False
            else:
                found = False
    else:
        found = False
    if found == True:
        return True
    else:
        return False


def build_prompt(question, chunks):
    context = ""
    for c in chunks:
        context = context + "[Page " + str(c["page"]) + "]\n" + c["text"] + "\n\n"
    prompt = "Here is some information from the bootcamp handbook:\n\n" + context
    prompt = prompt + "Question: " + question + "\n\n"
    prompt = prompt + "Answer the question using ONLY the information above. "
    prompt = prompt + "If the answer is not in the information, reply with exactly: I could not find that information in the handbook."
    return prompt


def ask_llm(prompt):
    # which llm to use comes from LLM_PROVIDER in the .env file (claude, openai or gemini)
    provider = os.environ.get("LLM_PROVIDER")
    if provider == None or provider == "":
        provider = "claude"
    provider = provider.lower().strip()

    if provider == "claude":
        return ask_claude(prompt)
    elif provider == "openai":
        return ask_openai(prompt)
    elif provider == "gemini":
        return ask_gemini(prompt)
    else:
        print("ERROR: unknown LLM_PROVIDER " + provider + " (use claude, openai or gemini)")
        return None


def ask_claude(prompt):
    # if there is no api key we cant call claude, so just return None
    if os.environ.get("ANTHROPIC_API_KEY") == None or os.environ.get("ANTHROPIC_API_KEY") == "":
        print("WARNING: no ANTHROPIC_API_KEY set")
        return None
    model_name = os.environ.get("LLM_MODEL")
    if model_name == None or model_name == "":
        model_name = "claude-opus-5-5"
    try:
        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model=model_name,
            max_tokens=1000,
            system="You are a helpful assistant for students of the ZAIO bootcamp. Keep answers short.",
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "low"},
            # if claude refuses for safety reasons the api tries another model for us
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            return None
        answer = ""
        for block in response.content:
            if block.type == "text":
                answer = answer + block.text
        return answer
    except Exception as e:
        print("ERROR calling claude: " + str(e))
        return None


def ask_openai(prompt):
    # same as ask_claude but for chatgpt
    if os.environ.get("OPENAI_API_KEY") == None or os.environ.get("OPENAI_API_KEY") == "":
        print("WARNING: no OPENAI_API_KEY set")
        return None
    model_name = os.environ.get("LLM_MODEL")
    if model_name == None or model_name == "":
        model_name = "gpt-5-nano"
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for students of the ZAIO bootcamp. Keep answers short."},
                {"role": "user", "content": prompt},
            ],
        )
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        print("ERROR calling openai: " + str(e))
        return None


def ask_gemini(prompt):
    # same as ask_claude but for gemini
    if os.environ.get("GEMINI_API_KEY") == None or os.environ.get("GEMINI_API_KEY") == "":
        print("WARNING: no GEMINI_API_KEY set")
        return None
    model_name = os.environ.get("LLM_MODEL")
    if model_name == None or model_name == "":
        model_name = "gemini-3.8-flash"
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"system_instruction": "You are a helpful assistant for students of the ZAIO bootcamp. Keep answers short."},
        )
        answer = response.text
        return answer
    except Exception as e:
        print("ERROR calling gemini: " + str(e))
        return None


def answer_question(question):
    collection = get_collection()
    if collection == None:
        return {"answer": "Error: database not ready", "source": ""}

    chunks = search_handbook(question, collection, model, chroma_client, 3)

    if is_answer_found(chunks) == False:
        return {"answer": "I could not find that information in the handbook.", "source": "Not found"}

    prompt = build_prompt(question, chunks)
    answer = ask_llm(prompt)

    if answer == None:
        # no llm, so just give back the best chunk as the answer
        answer = chunks[0]["text"].strip()

    if "I could not find that information in the handbook" in answer:
        return {"answer": "I could not find that information in the handbook.", "source": "Not found"}

    source = "Page " + str(chunks[0]["page"])
    return {"answer": answer, "source": source}
