import streamlit as st
import os, json
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any


def _load_handle_message():
    # Ensure project root is on sys.path so `import app.controller` works.
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Try common import styles first
    for mod_name in ("app.controller", "controller"):
        try:
            mod = importlib.import_module(mod_name)
            return getattr(mod, "handle_message")
        except Exception:
            continue
    # Fallback: load controller.py directly from the same folder
    # Fallback: load controller.py directly from the app folder but register it
    # under the package name so relative imports inside it keep working.
    try:
        p = Path(__file__).parent / "controller.py"
        spec = importlib.util.spec_from_file_location("app.controller", str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["app.controller"] = mod
        spec.loader.exec_module(mod)
        return getattr(mod, "handle_message")
    except Exception as e:
        raise ImportError("Could not import `handle_message` from controller module") from e


handle_message = _load_handle_message()

st.set_page_config(page_title="GoodFoods Reservation Agent", layout="wide")

st.title("GoodFoods — Reservation Agent (Prototype)")
st.write("Chat with the agent to book, modify, cancel, or get recommendations.")

if "history" not in st.session_state:
    st.session_state.history = []


def _safe_handle(msg: str) -> Dict[str, Any]:
    try:
        return handle_message(msg)
    except Exception as e:
        return {"success": False, "reply": "Internal error processing request.", "debug": {"error": str(e)}}


def send_user_message(msg: str):
    st.session_state.history.append({"role": "user", "text": msg})
    res = _safe_handle(msg)
    st.session_state.history.append({"role": "agent", "text": res.get("reply")})
    st.session_state.debug = res.get("debug")


with st.form("message_form", clear_on_submit=True):
    user_msg = st.text_input("You:", placeholder="e.g. Book a table for 4 in Koramangala tomorrow at 7pm")
    submitted = st.form_submit_button("Send")
    if submitted and user_msg:
        send_user_message(user_msg)


# display chat area
for item in st.session_state.history:
    if item.get("role") == "user":
        st.markdown(f"**You:** {item.get('text')}")
    else:
        st.markdown(f"**Agent:** {item.get('text')}")


with st.sidebar:
    st.header("Controls")
    if st.button("Load sample queries"):
        samples = [
            "Book a table for 4 in Koramangala tomorrow at 19:00",
            "Recommend a quiet place for two in Indiranagar",
            "I want to cancel booking 1234",
            "Change my booking 9c8a7b to 20:00",
        ]
        for s in samples:
            st.session_state.history.append({"role": "user", "text": s})
            res = _safe_handle(s)
            st.session_state.history.append({"role": "agent", "text": res.get("reply")})

    st.markdown("---")
    st.header("Dataset")
    try:
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "restaurants_seed.json")
        if os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                restaurants = json.load(f)
            st.write(f"Loaded {len(restaurants)} restaurants from seed file.")
            if st.checkbox("Show sample restaurants"):
                for r in restaurants[:6]:
                    st.write(f"- {r.get('name')} — {r.get('area')} — {', '.join(r.get('cuisines', []))} — Rating {r.get('rating')}")
        else:
            st.info("No restaurants_seed.json found in /data. The app will use a fallback sample.")
    except Exception as e:
        st.error(f"Error loading dataset: {e}")

    st.markdown("---")
    if st.checkbox("Show debug for last request"):
        st.json(st.session_state.get("debug", {}))

st.markdown("---")
st.caption("This is a prototype. For production, integrate a real LLM and external notification/payment providers.")
