import os
import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse
from PIL import Image
import io

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# API кілтін баптау
genai.configure(api_key=os.environ.get("GOOGLE_KEY"))

@app.get("/", response_class=HTMLResponse)
def home():
    with open(os.path.join(BASE_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Gemini Pro Vision моделін қолдану
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(["Мына суреттегі мәтінді анықтап, тек мәтіннің өзін қайтар:", image])
        
        return {"text": response.text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
