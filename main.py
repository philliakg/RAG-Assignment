# main.py
# The API. Start it from the project folder with:  uvicorn main:app --reload
# Then go to http://127.0.0.1:8000 or POST to http://127.0.0.1:8000/ask

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from src.retrieve import answer_question

app = FastAPI()


@app.get("/")
def home():
    # a very simple page so i can test in the browser
    html = """
    <html>
    <head><title>Handbook Assistant</title></head>
    <body style="font-family: Arial; background-color: #f0f0f0; padding: 20px;">
        <h1 style="color: #333;">ZAIO Handbook Assistant</h1>
        <p style="color:#555">Ask a question about the bootcamp handbook</p>
        <input id="q" style="width: 400px; padding: 8px;" placeholder="Type your question...">
        <button onclick="ask()" style="padding:8px 16px;background:#2b6cb0;color:white;border:none">Ask</button>
        <div id="answer" style="margin-top: 20px; background: white; padding: 15px; width: 500px"></div>
        <div id="source" style="margin-top:5px;color:gray;font-size:12px"></div>
        <script>
        function ask() {
            var q = document.getElementById("q").value;
            document.getElementById("answer").innerHTML = "Thinking...";
            fetch("/ask", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({question: q})
            })
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    document.getElementById("answer").innerHTML = "Error: " + data.error;
                    document.getElementById("source").innerHTML = "";
                } else {
                    document.getElementById("answer").innerHTML = data.answer;
                    document.getElementById("source").innerHTML = "Source: " + data.source;
                }
            });
        }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/ask")
async def ask(request: Request):
    # get the json from the request
    try:
        data = await request.json()
    except:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    if type(data) != dict:
        return JSONResponse(status_code=400, content={"error": "Invalid request"})

    if "question" not in data:
        return JSONResponse(status_code=400, content={"error": "Missing question"})

    question = data["question"]

    if type(question) != str:
        return JSONResponse(status_code=400, content={"error": "Question must be text"})

    if question.strip() == "":
        return JSONResponse(status_code=400, content={"error": "Question is empty"})

    try:
        result = answer_question(question)
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": "Something went wrong"})

    return result
