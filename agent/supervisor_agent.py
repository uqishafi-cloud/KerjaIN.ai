from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from agent.state import GraphState
from agent.sql_agent import sql_agent_node
from agent.rag_agent import rag_agent_node
from agent.consultant_agent import consultant_node

def supervisor_node(state: GraphState):
    user_msg = state["messages"][-1].content.lower()
    
    if state.get("cv_context"):
        return {"next_route": "consultant_agent"}
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    intent_prompt = f"""
    Tentukan tujuan pertanyaan ini: 'sql' atau 'rag'.
    - 'sql': Jika terkait data terstruktur (gaji spesifik, lokasi, tipe kerja WFO/WFH, jumlah data, statistik).
    - 'rag': Jika terkait data deskriptif (tugas, kualifikasi, skill, konsultasi umum).
    Pertanyaan: {user_msg}
    Jawab dengan satu kata saja (sql atau rag).
    """
    intent = llm.invoke(intent_prompt).content.strip().lower()
    
    return {"next_route": "sql_agent" if "sql" in intent else "rag_agent"}

workflow = StateGraph(GraphState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("sql_agent", sql_agent_node)
workflow.add_node("rag_agent", rag_agent_node)
workflow.add_node("consultant_agent", consultant_node)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor", 
    lambda x: x["next_route"],
    {"sql_agent": "sql_agent", "rag_agent": "rag_agent", "consultant_agent": "consultant_agent", "consultant_agent": "sql_agent", "consultant_agent": "rag_agent"}
)
workflow.add_edge("sql_agent", END)
workflow.add_edge("rag_agent", END)
workflow.add_edge("consultant_agent", END)

kerjain_agent = workflow.compile()