import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.messages import AIMessage
from agent.state import GraphState

def rag_agent_node(state: GraphState):
    print("[LOG] RAG Agent aktif.")
    user_msg = state["messages"][-1].content
    
    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name="indonesian_jobs", 
        embedding=OpenAIEmbeddings(model="text-embedding-3-small")
    )
    
    docs = vector_store.similarity_search(user_msg, k=4)
    context = "\n".join([d.page_content for d in docs])
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = f"Gunakan informasi lowongan berikut untuk menjawab pertanyaan.\n\nKonteks Lowongan:\n{context}\n\nPertanyaan: {user_msg}"
    response = llm.invoke(prompt)
    
    return {"messages": [AIMessage(content=response.content)]}