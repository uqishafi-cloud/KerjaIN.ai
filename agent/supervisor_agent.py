from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from agent.state import GraphState
from agent.sql_agent import sql_agent_node
from agent.rag_agent import rag_agent_node
from agent.consultant_agent import consultant_node

def supervisor_node(state: GraphState):
    messages = state["messages"]
    if len(messages) > 10: 
        return {"next_route": "FINISH"}
        
    if state.get("cv_context"):
        return {"next_route": "consultant_agent"}
    
    recent_messages = messages[-6:]
    history_text = ""
    for m in recent_messages:
        role = "User" if m.type == "human" else "Agent"
        history_text += f"{role}: {m.content}\n"
    
    if state.get("cv_context") and len(messages) <= 2:
        return {"next_route": "consultant_agent"}
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    intent_prompt = f"""
    Kamu adalah Supervisor Agent. Tugasmu adalah membaca histori percakapan dan menentukan langkah selanjutnya.
    
    Histori percakapan saat ini:
    {history_text}
    
    Evaluasi apa yang diminta oleh User pada pesan paling akhir, dan pertimbangkan konteks sebelumnya.
    Pilih SATU agent yang harus bekerja:
    1. 'sql': Jika User MEMBUTUHKAN data terstruktur (gaji spesifik, lokasi, tipe kerja WFO/WFH, jumlah data, statistik) dan belum dijawab.
    2. 'rag': Jika User MEMBUTUHKAN data deskriptif (tugas, kualifikasi, skill, konsultasi umum) dan belum dijawab.
    3. 'consultant': Jika User MEMBUTUHKAN evaluasi CV/karir pastikan terdapat data CV di histori "cv_context".
    4. 'FINISH': Jika jawaban dari Agent sebelumnya SUDAH LENGKAP dan menjawab pertanyaan terbaru User.
    
    Jawab dengan SATU KATA dari opsi di atas (sql, rag, consultant, atau FINISH).
    """
    intent = llm.invoke(intent_prompt).content.strip().lower()

    if "sql" in intent:
        next_route = "sql_agent"
    elif "rag" in intent:
        next_route = "rag_agent"
    elif "consultant" in intent:
        next_route = "consultant_agent"
    else:
        next_route = "FINISH"
        
    return {"next_route": next_route}

workflow = StateGraph(GraphState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sql_agent", sql_agent_node)
workflow.add_node("rag_agent", rag_agent_node)
workflow.add_node("consultant_agent", consultant_node)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor", 
    lambda x: x["next_route"],
    {"sql_agent": "sql_agent", 
     "rag_agent": "rag_agent", 
     "consultant_agent": "consultant_agent",
     "FINISH": END
     }
)
workflow.add_edge("sql_agent", "supervisor")
workflow.add_edge("rag_agent", "supervisor")
workflow.add_edge("consultant_agent", "supervisor")

kerjain_agent = workflow.compile()