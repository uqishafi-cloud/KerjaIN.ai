import os
import sqlite3
import pandas as pd
from uuid import uuid4
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "jobs.jsonl")
DB_PATH = os.path.join(BASE_DIR, "indonesian_jobs.db")

def process():
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not all([qdrant_url, qdrant_api_key]):
        print("[ERROR] Kredensial tidak lengkap. Periksa QDRANT_URL dan QDRANT_API_KEY di file .env")
        return

    if not os.path.exists(DATASET_PATH):
        print(f"[ERROR] File dataset tidak ditemukan di: {DATASET_PATH}")
        return

    # 1. Simpan ke SQLite
    print("[INFO] Membaca dan memproses dataset...")
    df = pd.read_json(DATASET_PATH, lines=True)
    df['id'] = [str(uuid4()) for _ in range(len(df))]
    
    print(f"[INFO] Menyimpan data terstruktur ke SQLite: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    sql_cols = ['id', 'job_title', 'company_name', 'location', 'work_type', 'salary', '_scrape_timestamp']
    df[sql_cols].to_sql('jobs', conn, if_exists='replace', index=False)
    conn.close()
    
    # 2. Persiapan RAG (Chunking)
    print("[INFO] Melakukan proses pemotongan teks (chunking)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = []

    for _, row in df.iterrows():
        content = f"Job: {row['job_title']}\nCo: {row['company_name']}\nDesc: {row['job_description']}"
        for chunk in text_splitter.split_text(content):
            docs.append(Document(
                page_content=chunk, 
                metadata={"job_id": row['id'], "title": row['job_title']}
            ))

    # 3. Kirim ke Qdrant Cloud
    print("[INFO] Menghubungkan dan mengunggah data ke Qdrant Cloud...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    QdrantVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name="indonesian_jobs",
        force_recreate=True 
    )
    
    print("[SUCCESS] Seluruh proses selesai. Database SQLite dan Qdrant Cloud sudah siap.")

if __name__ == "__main__":
    try:
        process()
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")