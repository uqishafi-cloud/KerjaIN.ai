import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import PyPDF2, docx, pytesseract, io, uvicorn
from PIL import Image
from agent.supervisor_agent import kerjain_agent
from langchain_core.messages import HumanMessage

app = FastAPI(title="KerjaIN.ai API")

class ChatRequest(BaseModel):
    message: str
    cv_text: str = ""
    role: str = "jobseeker"

@app.post("/upload-cv")
async def process_cv(file: UploadFile = File(...)):
    filename = file.filename.lower()
    allowed_ext = (".pdf", ".docx", ".jpg", ".jpeg", ".png")
    
    if not filename.endswith(allowed_ext):
        raise HTTPException(status_code=400, detail="Format tidak didukung. Gunakan PDF, DOCX, atau JPG/PNG.")
    
    try:
        content = await file.read()
        extracted_text = ""
        
        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            extracted_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        elif filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            extracted_text = "\n".join([p.text for p in doc.paragraphs])
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            extracted_text = pytesseract.image_to_string(Image.open(io.BytesIO(content)))
            
        if not extracted_text.strip():
            raise ValueError("Tidak ada teks yang dapat diekstrak.")
            
        return {"cv_text": extracted_text.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    inputs = {
        "messages": [HumanMessage(content=req.message)],
        "cv_context": req.cv_text,
        "user_role": req.role
    }
    try:
        result = kerjain_agent.invoke(inputs)
        return {"reply": result["messages"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Terjadi kesalahan pada sistem agen.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)