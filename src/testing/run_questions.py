# src/testing/run_questions.py
# Part 4: ask the assistant a bunch of questions and save the results
# (not called test_... on purpose, so pytest doesn't run it - it needs the real API)
# The API must be running first:  uvicorn main:app
# Then run from the project folder:  python src/testing/run_questions.py

import sys
import requests

url = "http://127.0.0.1:8000/ask"
# you can give a different url, e.g.  python src/testing/run_questions.py http://127.0.0.1:8001/ask
if len(sys.argv) > 1:
    url = sys.argv[1]

questions = [
    "What is the attendance requirement?",
    "How much are the bootcamp fees?",
    "When does the bootcamp start?",
    "What time are the live classes?",
    "What are the minimum laptop requirements?",
    "How is the final grade calculated?",
    "Where are the recorded lectures posted?",
    "Who is the lead instructor?",
    "How do I get XP points on Discord?",
    "What is the capital of France?",
]

results = []
for q in questions:
    print("Asking: " + q)
    try:
        r = requests.post(url, json={"question": q})
        data = r.json()
        results.append({"question": q, "answer": data.get("answer", ""), "source": data.get("source", "")})
    except:
        print("ERROR: is the API running?")
        results.append({"question": q, "answer": "ERROR", "source": ""})

# save the results to a markdown file
f = open("test_results.md", "w", encoding="utf-8")
f.write("# Test Results\n\n")
n = 1
for r in results:
    f.write("## Test " + str(n) + "\n\n")
    f.write("**Question:** " + r["question"] + "\n\n")
    f.write("**Source/Page:** " + r["source"] + "\n\n")
    f.write("**Answer:** " + r["answer"] + "\n\n")
    f.write("---\n\n")
    n = n + 1
f.close()
print("Saved to test_results.md")
