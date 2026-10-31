# src/ingest.py
# This file reads the handbook PDF and puts it into the vector database
# Run it ONCE before starting the API, from the project folder:  python src/ingest.py
#
# Steps:
# 1. load the pdf
# 2. get the text out
# 3. cut the text into chunks
# 4. make embeddings
# 5. save them in chromadb (the vectorstore folder)

import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb


def load_pdf(path):
    # open the pdf and get every page
    if os.path.exists(path) == False:
        print("ERROR: file not found")
        return None
    reader = PdfReader(path)
    pages = reader.pages
    return pages


def fix_spaced_text(text):
    # the handbook pdf comes out like "W e l c o m e  t o" (letters with spaces)
    # so i split on the double space to get the words and then remove the single spaces
    # took me a long time to figure this out lol
    lines = text.split("\n")
    new_lines = []
    for line in lines:
        words = line.split("  ")
        new_words = []
        for w in words:
            w = w.replace(" ", "")
            if w != "":
                new_words.append(w)
        new_line = " ".join(new_words)
        new_lines.append(new_line)
    result = "\n".join(new_lines)
    return result


def extract_text(pages):
    # make a list of {"page": number, "text": text}
    all_pages = []
    i = 0
    for page in pages:
        i = i + 1
        text = page.extract_text()
        if text == None:
            text = ""
        # check if the text is the spaced out kind
        # (if lots of the characters are spaces it is probably spaced out)
        spaces = 0
        for ch in text:
            if ch == " ":
                spaces = spaces + 1
        if len(text) > 0:
            if spaces / len(text) > 0.3:
                text = fix_spaced_text(text)
            else:
                text = text
        # remove weird characters
        text = text.replace("�", "'")
        text = text.replace("\t", " ")
        all_pages.append({"page": i, "text": text})
    return all_pages


def split_into_chunks(all_pages):
    # cut every page into chunks of 500 characters with 100 overlap
    # the overlap is so we dont cut a sentence in half and lose it
    chunks = []
    for p in all_pages:
        text = p["text"]
        page_number = p["page"]
        start = 0
        while start < len(text):
            end = start + 500
            chunk = text[start:end]
            if len(chunk.strip()) > 20:
                chunks.append({"text": chunk, "page": page_number})
            start = start + 500 - 100
    return chunks


def make_embeddings(chunks, model):
    texts = []
    for c in chunks:
        texts.append(c["text"])
    embeddings = model.encode(texts)
    return embeddings


def save_to_chroma(chunks, embeddings, chroma_client, model, pdf_path):
    # TODO: model and pdf_path are not used here, remove later?
    # delete the old collection first so we dont get duplicates when running twice
    try:
        chroma_client.delete_collection("handbook")
    except:
        pass
    collection = chroma_client.create_collection("handbook")

    ids = []
    documents = []
    metadatas = []
    vectors = []
    for i in range(len(chunks)):
        ids.append("chunk_" + str(i))
        documents.append(chunks[i]["text"])
        metadatas.append({"page": chunks[i]["page"]})
        vectors.append(embeddings[i].tolist())

    collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=vectors)
    return collection


def run_ingest(pdf_path="data/March 2026 Fullstack AI Engineer Bootcamp handbook.pdf", db_path="vectorstore"):
    print("Loading pdf...")
    pages = load_pdf(pdf_path)
    if pages == None:
        return 0
    print("Pages: " + str(len(pages)))

    print("Extracting text...")
    all_pages = extract_text(pages)

    print("Splitting into chunks...")
    chunks = split_into_chunks(all_pages)
    print("Chunks: " + str(len(chunks)))

    print("Making embeddings (this can take a minute the first time)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = make_embeddings(chunks, model)

    print("Saving to chromadb...")
    chroma_client = chromadb.PersistentClient(path=db_path)
    save_to_chroma(chunks, embeddings, chroma_client, model, pdf_path)

    print("Done!")
    return len(chunks)


if __name__ == "__main__":
    run_ingest()
