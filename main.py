import os
from dotenv import load_dotenv
load_dotenv()
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import PyPDF2, docx, io, uvicorn
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agent.supervisor_agent import kerjain_agent

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
        raw_text = ""
        
        # File Teks (PDF/DOCX)
        if filename.endswith(".pdf"):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            raw_text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
            
        elif filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            raw_text = "\n".join([p.text for p in doc.paragraphs])
            
        # File Gambar
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            print("[INFO] Menggunakan GPT-4o-mini Vision untuk membaca gambar...")
            base64_image = base64.b64encode(content).decode("utf-8")
            llm_vision = ChatOpenAI(model="gpt-4o-mini", max_tokens=1500)
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Baca seluruh teks dalam gambar CV ini dengan sangat teliti. Pertahankan format aslinya (Pendidikan, Pengalaman, Skill)."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
            response = llm_vision.invoke([message])
            raw_text = response.content

        if not raw_text.strip():
            raise ValueError("Tidak ada teks yang dapat diekstrak.")
            
        return {"cv_text": raw_text.strip()}
        
    except Exception as e:
        print(f"[ERROR] Ekstraksi CV gagal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    inputs = {
        "messages": [HumanMessage(content=req.message)],
        "cv_context": req.cv_text,
        "user_role": req.role
    }
    result = kerjain_agent.invoke(inputs)
    return {"reply": result["messages"][-1].content}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)