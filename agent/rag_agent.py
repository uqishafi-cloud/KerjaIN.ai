import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_core.messages import AIMessage
from agent.state import GraphState

def rag_agent_node(state: GraphState):
    print("[LOG] RAG Agent aktif.")
    recent_messages = state["messages"][-6:]
    history_text = "\n".join([f"{'User' if m.type == 'human' else 'Agent'}: {m.content}" for m in recent_messages])
    latest_user_msg = state["messages"][-1].content

    client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    vector_store = QdrantVectorStore(
        client=client, 
        collection_name="indonesian_jobs", 
        embedding=OpenAIEmbeddings(model="text-embedding-3-small")
    )
    
    docs = vector_store.similarity_search(latest_user_msg, k=4)
    context = "\n".join([d.page_content for d in docs])
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = f"""
    Gunakan informasi lowongan berikut untuk menjawab pertanyaan User.
    
    Konteks Lowongan dari Database:
    {context}
    
    Histori Percakapan Terakhir:
    {history_text}
    
    Berdasarkan konteks lowongan dan histori obrolan di atas, 
    berikan jawaban yang relevan dan nyambung dengan pertanyaan paling akhir dari User.
    """
    
    response = llm.invoke(prompt)

    return {"messages": [AIMessage(content=response.content)]}