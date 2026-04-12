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
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    system_prompt = f"""
    Kamu adalah Database Expert untuk aplikasi KerjaIN.ai.
    Skema tabel 'jobs': id, job_title, company_name, location, work_type, salary, _scrape_timestamp.
    
    Aturan Ketat:
    1. Hanya berikan query SELECT. Dilarang keras melakukan operasi manipulasi data lainnya.
    2. Role pengguna saat ini adalah: '{user_role}'.
    3. Jika role 'jobseeker', HANYA berikan daftar lowongan yang relevan. Jangan berikan data statistik, agregat, atau rata-rata gaji kompetitor.
    4. Jika role 'hr', kamu diizinkan memberikan analisis statistik, agregat, atau rata-rata gaji.
    
    Keluarkan HANYA query SQL murni tanpa format markdown.
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

    final_answer = llm.invoke(f"Rangkum hasil database ini dengan bahasa natural untuk user ({user_role}): {result_text}").content
    return {"messages": [AIMessage(content=final_answer)]}