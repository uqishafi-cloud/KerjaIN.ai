import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.messages import AIMessage
from agent.state import GraphState

def consultant_node(state: GraphState):
    print("[LOG] Consultant Agent aktif.")
    cv_text = state.get("cv_context", "")
    user_role = state.get("user_role", "jobseeker")
    
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name="indonesian_jobs", 
        embedding=OpenAIEmbeddings(model="text-embedding-3-small")
    )
    
    matched_jobs = vector_store.similarity_search(cv_text, k=3)
    job_context = "\n".join([j.page_content for j in matched_jobs])
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    if user_role == "hr":
        prompt = f"Kamu adalah asisten HR. Evaluasi CV kandidat ini terhadap lowongan berikut:\n{job_context}\nTeks CV:\n{cv_text}\nApakah kandidat ini layak untuk direkrut?"
    else:
        prompt = f"Kamu adalah Konsultan Karir. Teks CV User:\n{cv_text}\nLowongan yang tersedia:\n{job_context}\nBerikan rekomendasi lowongan yang cocok dan saran skill yang perlu ditingkatkan."
        
    res = llm.invoke(prompt)
    return {"messages": [AIMessage(content=res.content)]}