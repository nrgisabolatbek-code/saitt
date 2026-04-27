import os
import json
import uuid
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from google.cloud import vision
from google.oauth2 import service_account
from docx import Document

app = FastAPI()

# Файл тұрған папканы (root) анықтау - бұл Railway-де файлдарды табу үшін өте маңызды
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client():
    # Environment variable арқылы Google кілтін алу
    key_data = json.loads(os.environ["GOOGLE_KEY"])
    credentials = service_account.Credentials.from_service_account_info(key_data)
    return vision.ImageAnnotatorClient(credentials=credentials)

def run_ocr(image_bytes):
    client = get_client()
    image = vision.Image(content=image_bytes)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    text = response.full_text_annotation.text
    if not text.strip():
        return "Мәтін табылмады"
    return text

# Басты бет - index.html файлын оқу
@app.get("/", response_class=HTMLResponse)
def home():
    html_path = os.path.join(BASE_DIR, "index.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            content=f"<h1>index.html серверде табылмады</h1><p>Ізделінген жол: {html_path}</p>", 
            status_code=404
        )

# Мәтінді жай ғана JSON түрінде қайтару
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = run_ocr(contents)
        return {"text": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Мәтінді .docx файлына айналдырып жүктеу
@app.post("/upload-docx")
async def upload_docx(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = run_ocr(contents)

        # Уақытша файл атын жасау
        filename = f"ocr_result_{uuid.uuid4().hex[:8]}.docx"
        file_path = os.path.join(BASE_DIR, filename)

        doc = Document()
        doc.add_heading("Танылған мәтін", 0)
        doc.add_paragraph(text)
        doc.save(file_path)

        return FileResponse(
            path=file_path,
            filename="result.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Локальді тексеруге арналған (Railway-де start.sh немесе Start Command қолданылады)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
