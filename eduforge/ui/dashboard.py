"""
EduForge — Streamlit UI Dashboard
A browser-based interface for teachers to:
  • Upload educational materials
  • Monitor ingestion status
  • Generate exams with custom configurations
  • View and export generated exams
  • Monitor training jobs

Run with: streamlit run ui/dashboard.py
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="EduForge — AI Exam Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session State Helpers ─────────────────────────────────────────────────────

def get_token() -> Optional[str]:
    return st.session_state.get("access_token")


def auth_header() -> Dict[str, str]:
    token = get_token()
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str, params: Optional[Dict] = None) -> Optional[Dict]:
    try:
        r = requests.get(f"{API_BASE}{path}", headers=auth_header(), params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        st.error(f"API error {r.status_code}: {r.text[:200]}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to EduForge API. Is it running?")
        return None


def api_post(path: str, data: Optional[Dict] = None, json_: Optional[Dict] = None, files=None) -> Optional[Dict]:
    try:
        r = requests.post(
            f"{API_BASE}{path}",
            headers=auth_header(),
            data=data,
            json=json_,
            files=files,
            timeout=60,
        )
        if r.status_code == 200:
            return r.json()
        st.error(f"API error {r.status_code}: {r.text[:300]}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to EduForge API.")
        return None


def api_delete(path: str) -> bool:
    try:
        r = requests.delete(f"{API_BASE}{path}", headers=auth_header(), timeout=15)
        return r.status_code == 200
    except Exception:
        return False


# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .status-badge {
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .status-ready    { background: #d4edda; color: #155724; }
    .status-pending  { background: #fff3cd; color: #856404; }
    .status-failed   { background: #f8d7da; color: #721c24; }
    .status-running  { background: #cce5ff; color: #004085; }
    .metric-card {
        background: #f8f9fa;
        padding: 16px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Auth Page ─────────────────────────────────────────────────────────────────

def page_auth():
    st.title("🎓 EduForge — AI Exam Generator")
    st.markdown("*Powered by Transformers · ChromaDB · MLflow*")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            try:
                r = requests.post(
                    f"{API_BASE}/auth/login",
                    data={"username": username, "password": password},
                    timeout=10,
                )
                if r.status_code == 200:
                    st.session_state["access_token"] = r.json()["access_token"]
                    st.session_state["username"] = username
                    st.success("Logged in!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Connection error: {e}")

    with tab_register:
        with st.form("register_form"):
            reg_email    = st.text_input("Email")
            reg_username = st.text_input("Username")
            reg_password = st.text_input("Password", type="password")
            reg_role     = st.selectbox("Role", ["teacher", "admin"])
            reg_submit   = st.form_submit_button("Register", use_container_width=True)

        if reg_submit:
            result = api_post("/auth/register", json_={
                "email": reg_email,
                "username": reg_username,
                "password": reg_password,
                "role": reg_role,
            })
            if result:
                st.success("Account created — please log in.")


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.get('username', 'User')}")
        if st.button("Logout", use_container_width=True):
            for key in ["access_token", "username"]:
                st.session_state.pop(key, None)
            st.rerun()

        st.divider()

        # Health check
        try:
            r = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=5)
            health = r.json()
            status_color = "🟢" if health["status"] == "healthy" else "🟡"
            st.markdown(f"**API:** {status_color} {health['status'].title()}")
            st.markdown(f"**DB:** {'🟢' if health['database'] else '🔴'}")
            st.markdown(f"**Redis:** {'🟢' if health['redis'] else '🔴'}")
            st.markdown(f"**VectorDB:** {'🟢' if health['vector_db'] else '🔴'}")
        except Exception:
            st.markdown("**API:** 🔴 Offline")

        st.divider()
        page = st.radio(
            "Navigation",
            ["📁 Materials", "📝 Generate Exam", "📋 My Exams", "🔧 Training", "📊 Jobs"],
            key="nav_page",
        )

    return page


# ── Materials Page ────────────────────────────────────────────────────────────

def page_materials():
    st.title("📁 Educational Materials")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Upload New Material")
        with st.form("upload_form"):
            title   = st.text_input("Title *", placeholder="e.g. Chapter 5: Calculus")
            subject = st.text_input("Subject", placeholder="e.g. Mathematics")
            desc    = st.text_area("Description", height=80)
            file    = st.file_uploader(
                "Choose file",
                type=["pdf", "docx", "txt", "md"],
                help="PDF, Word, Text, or Markdown — max 50MB",
            )
            submit = st.form_submit_button("Upload & Process", use_container_width=True)

        if submit and file and title:
            with st.spinner("Uploading and starting ingestion..."):
                result = api_post(
                    "/materials/upload",
                    data={"title": title, "subject": subject, "description": desc},
                    files={"file": (file.name, file.getvalue(), file.type)},
                )
            if result:
                st.success(f"Material uploaded! ID: `{result['id']}`")
                st.info(
                    "✅ File uploaded! Ingestion is running in the background.\n\n"
                    "⏱ **Wait 30–60 seconds** then click **Refresh** — status will change from PENDING → READY.\n\n"
                    "If it stays PENDING after 2 minutes, click the **🔄 Retry** button on the material card. "
                    "Make sure `sentence-transformers` is installed in your venv."
                )

    with col2:
        st.subheader("Your Materials")
        subject_filter = st.text_input("Filter by subject", placeholder="Leave blank for all")
        if st.button("Refresh", key="refresh_materials"):
            st.rerun()

        materials = api_get("/materials", params={"subject": subject_filter} if subject_filter else None) or []

        if not materials:
            st.info("No materials yet — upload your first document!")
        else:
            for mat in materials:
                status = mat["status"]
                badge_class = f"status-{status}"
                with st.expander(f"📄 {mat['title']} — {mat.get('subject', 'No subject')}"):
                    cols = st.columns([2, 1, 1, 1, 1])
                    cols[0].markdown(
                        f"<span class='status-badge {badge_class}'>{status.upper()}</span>",
                        unsafe_allow_html=True,
                    )
                    cols[1].metric("Chunks", mat["chunk_count"])
                    cols[2].metric("Size", f"{mat.get('file_size_kb', 0)} KB")

                    # Show retry button for stuck/failed materials
                    if status in ("pending", "failed"):
                        if cols[3].button("🔄 Retry", key=f"retry_mat_{mat['id']}", help="Re-trigger ingestion"):
                            r = api_post(f"/materials/{mat['id']}/reprocess")
                            if r:
                                st.success("Ingestion re-started! Refresh in 30 seconds.")
                                st.rerun()
                    else:
                        cols[3].write("")  # spacer

                    if cols[4].button("🗑 Delete", key=f"del_mat_{mat['id']}"):
                        if api_delete(f"/materials/{mat['id']}"):
                            st.success("Deleted")
                            st.rerun()

                    # Helpful hints for stuck materials
                    if status == "pending" and mat["chunk_count"] == 0:
                        st.warning(
                            "⚠️ Stuck at PENDING? The ingestion task may have failed silently. "
                            "Click **🔄 Retry** to re-run ingestion. Make sure `sentence-transformers` is installed: "
                            "`pip install sentence-transformers`"
                        )
                    elif status == "failed":
                        st.error("Ingestion failed. Click **🔄 Retry** to try again.")


# ── Generate Exam Page ────────────────────────────────────────────────────────

def page_generate_exam():
    st.title("📝 Generate Exam")

    materials = api_get("/materials") or []
    ready_materials = [m for m in materials if m["status"] == "ready"]

    if not ready_materials:
        st.warning("No ready materials found. Upload and wait for ingestion to complete.")
        return

    with st.form("generate_form"):
        st.subheader("Exam Configuration")

        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Exam Title *", placeholder="e.g. Midterm Exam — Chapter 5")
            topic = st.text_input("Topic Focus", placeholder="e.g. Derivatives and Integrals")
            desc  = st.text_area("Description", height=80)

        with col2:
            material_options = {f"{m['title']} ({m.get('subject','')})": m["id"] for m in ready_materials}
            selected_labels  = st.multiselect("Source Materials *", list(material_options.keys()))
            time_limit = st.number_input("Time Limit (minutes, 0 = none)", min_value=0, value=60)

        st.subheader("Question Types")
        q_configs = []
        type_options = ["multiple_choice", "true_false", "short_answer", "essay", "fill_blank"]
        difficulty_options = ["easy", "medium", "hard"]

        for i in range(3):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            q_type = c1.selectbox(f"Type {i+1}", type_options, key=f"qtype_{i}")
            count  = c2.number_input(f"Count {i+1}", 1, 20, 5, key=f"qcount_{i}")
            diff   = c3.selectbox(f"Difficulty {i+1}", difficulty_options, index=1, key=f"qdiff_{i}")
            active = c4.checkbox("Enable", value=(i == 0), key=f"qactive_{i}")
            if active:
                q_configs.append({"question_type": q_type, "count": count, "difficulty": diff})

        instructions = st.text_area("Special Instructions", height=80)
        submitted = st.form_submit_button("🚀 Generate Exam", use_container_width=True)

    if submitted:
        if not selected_labels:
            st.error("Select at least one source material.")
            return
        if not q_configs:
            st.error("Enable at least one question type.")
            return

        payload = {
            "title": title,
            "description": desc or None,
            "material_ids": [material_options[l] for l in selected_labels],
            "topic": topic or None,
            "question_configs": q_configs,
            "time_limit_min": time_limit if time_limit > 0 else None,
            "instructions": instructions or None,
        }

        with st.spinner("Queuing exam generation..."):
            result = api_post("/exams/generate", json_=payload)

        if result:
            st.success(f"Generation job created! Job ID: `{result['id']}`")
            st.info("Generation runs async — go to **My Exams** to see results when ready.")


# ── My Exams Page ─────────────────────────────────────────────────────────────

def page_exams():
    st.title("📋 My Exams")

    if st.button("Refresh"):
        st.rerun()

    exams = api_get("/exams") or []
    if not exams:
        st.info("No exams yet — generate your first exam!")
        return

    for exam in exams:
        with st.expander(f"📝 {exam['title']} — {exam.get('topic', '')}"):
            cols = st.columns(4)
            cols[0].metric("Questions", exam["num_questions"])
            cols[1].metric("Difficulty", exam.get("difficulty", "medium").title())
            cols[2].metric("Time Limit", f"{exam.get('time_limit_min', '—')} min")
            cols[3].metric("Published", "Yes" if exam["is_published"] else "No")

            if exam.get("questions"):
                st.markdown("---")
                for q in exam["questions"][:3]:  # Preview first 3
                    st.markdown(f"**Q{q['order_index']+1}** ({q['question_type'].replace('_',' ')}) — {q['content'][:120]}...")
                if exam["num_questions"] > 3:
                    st.caption(f"... and {exam['num_questions']-3} more questions")

            btn_col1, btn_col2, btn_col3 = st.columns(3)
            if btn_col1.button("View Full Exam", key=f"view_{exam['id']}"):
                full = api_get(f"/exams/{exam['id']}")
                if full:
                    st.json(full)

            if btn_col2.button("Export Markdown", key=f"export_{exam['id']}"):
                try:
                    r = requests.get(
                        f"{API_BASE}/exams/{exam['id']}/export/markdown",
                        headers=auth_header(),
                    )
                    if r.status_code == 200:
                        st.download_button(
                            "Download Teacher Copy",
                            r.text,
                            file_name=f"{exam['title'].replace(' ', '_')}_teacher.md",
                            mime="text/markdown",
                        )
                except Exception as e:
                    st.error(str(e))

            if btn_col3.button("Delete", key=f"del_exam_{exam['id']}"):
                if api_delete(f"/exams/{exam['id']}"):
                    st.success("Deleted")
                    st.rerun()


# ── Training Page ─────────────────────────────────────────────────────────────

def page_training():
    st.title("🔧 Model Training")
    st.info("Fine-tune a T5 model on your educational materials. Training runs asynchronously.")

    materials = api_get("/materials") or []
    ready_mats = [m for m in materials if m["status"] == "ready"]

    with st.form("train_form"):
        model_name = st.text_input("Model Name *", placeholder="e.g. math-exam-v1")
        base_model = st.selectbox("Base Model", ["google/flan-t5-small", "google/flan-t5-base", "t5-small"])
        mat_options = {f"{m['title']}": m["id"] for m in ready_mats}
        sel_mats    = st.multiselect("Training Materials *", list(mat_options.keys()))

        st.markdown("**Hyperparameters**")
        c1, c2, c3 = st.columns(3)
        epochs    = c1.number_input("Epochs", 1, 10, 3)
        batch_sz  = c2.number_input("Batch Size", 1, 16, 4)
        lr        = c3.number_input("Learning Rate", 1e-6, 1e-3, 5e-5, format="%.6f")

        submit = st.form_submit_button("Start Training", use_container_width=True)

    if submit:
        if not model_name or not sel_mats:
            st.error("Model name and materials are required.")
            return
        payload = {
            "model_name": model_name,
            "base_model": base_model,
            "material_ids": [mat_options[m] for m in sel_mats],
            "hyperparams": {
                "num_train_epochs": epochs,
                "per_device_train_batch_size": batch_sz,
                "learning_rate": lr,
            },
        }
        with st.spinner("Submitting training job..."):
            result = api_post("/training/start", json_=payload)
        if result:
            st.success(f"Training job created! ID: `{result['id']}`")

    st.divider()
    st.subheader("Training History")
    if st.button("Refresh", key="refresh_training"):
        st.rerun()

    jobs = api_get("/training") or []
    for job in jobs:
        status = job["status"]
        badge = {"queued": "🟡", "running": "🔵", "completed": "🟢", "failed": "🔴"}.get(status, "⚪")
        with st.expander(f"{badge} {job['model_name']} — {status.upper()}"):
            if job.get("metrics"):
                st.json(job["metrics"])
            if job.get("mlflow_run_url"):
                st.markdown(f"[View in MLflow]({job['mlflow_run_url']})")
            if job.get("error_message"):
                st.error(job["error_message"])


# ── Jobs Page ─────────────────────────────────────────────────────────────────

def page_jobs():
    st.title("📊 Generation Jobs")
    if st.button("Refresh"):
        st.rerun()

    jobs = api_get("/jobs") or []
    if not jobs:
        st.info("No generation jobs yet.")
        return

    for job in jobs:
        status = job["status"]
        badge = {"queued": "🟡", "running": "🔵", "completed": "🟢", "failed": "🔴"}.get(status, "⚪")
        cols = st.columns([3, 1, 2, 2])
        cols[0].markdown(f"{badge} `{job['id'][:12]}...`")
        cols[1].markdown(status.upper())
        cols[2].markdown(f"Started: {job.get('started_at', '—')}")
        if job.get("error_message"):
            st.error(job["error_message"])


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not get_token():
        page_auth()
        return

    page = sidebar()

    page_map = {
        "📁 Materials":   page_materials,
        "📝 Generate Exam": page_generate_exam,
        "📋 My Exams":    page_exams,
        "🔧 Training":    page_training,
        "📊 Jobs":        page_jobs,
    }

    fn = page_map.get(page)
    if fn:
        fn()


if __name__ == "__main__":
    main()