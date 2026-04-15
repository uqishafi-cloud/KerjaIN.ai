import sqlite3
import os
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from agent.state import GraphState

def sql_agent_node(state: GraphState):
    print("[LOG] SQL Agent aktif.")
    user_msg = state["messages"][-1].content
    user_role = state.get("user_role", "jobseeker")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "indonesian_jobs.db")
    
    recent_messages = state["messages"][-6:]
    history_text = "\n".join([f"{'User' if m.type == 'human' else 'Agent'}: {m.content}" for m in recent_messages])
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    system_prompt = f"""
    Kamu adalah Database Expert untuk aplikasi KerjaIN.ai.
    Skema tabel 'jobs': id, job_title, company_name, location, work_type, salary, _scrape_timestamp.
    
    Aturan Ketat:
    1. Hanya berikan query SELECT. Dilarang keras melakukan operasi manipulasi data lainnya.
    2. Role pengguna saat ini adalah: '{user_role}'.
    3. Keluarkan HANYA query SQL murni tanpa format markdown (tanpa ```sql).
    
    Berikut adalah histori percakapan terakhir untuk memahami konteks pertanyaan User:
    {history_text}
    
    Buatlah Query SQL berdasarkan histori di atas.
    """
    
    query = llm.invoke([("system", system_prompt), ("human", user_msg)]).content.strip()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        result_text = f"Data mentah: {str(rows)}"
    except Exception as e:
        result_text = f"Terjadi kesalahan query: {str(e)}"

    final_prompt = f"""
    Histori Obrolan:
    {history_text}
    
    Hasil pencarian database terbaru: {result_text}
    
    Tugasmu: Rangkum hasil database ini dengan bahasa natural untuk membalas pesan terakhir User ({user_role}).
    """
    final_answer = llm.invoke(final_prompt).content
    
    return {"messages": [AIMessage(content=final_answer)]}