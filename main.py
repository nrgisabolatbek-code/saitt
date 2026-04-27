from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from google.cloud import vision
from google.oauth2 import service_account
from docx import Document
import os
import json
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client():
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

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = run_ocr(contents)
        return {"text": text}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/upload-docx")
async def upload_docx(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        text = run_ocr(contents)

        filename = f"ocr_result_{uuid.uuid4().hex[:8]}.docx"

        doc = Document()
        doc.add_heading("Распознанный мәтін", 0)
        doc.add_paragraph(text)
        doc.save(filename)

        return FileResponse(
            path=filename,
            filename="result.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})