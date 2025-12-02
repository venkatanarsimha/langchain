# app.py
import streamlit as st
import requests
import uuid
import os
import re
import json
from typing import Any, Optional

# ----------------------
# Configuration
# ----------------------
LANGFLOW_API_URL = os.getenv(
    "LANGFLOW_API_URL",
    "http://127.0.0.1:7860/api/v1/run/a8b894bc-5791-4eb9-a925-3a8136872944",
)
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY")  # must be set in environment

# ----------------------
# Utilities
# ----------------------
_uuid_regex = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def is_uuid(s: str) -> bool:
    try:
        return bool(_uuid_regex.fullmatch(s.strip()))
    except Exception:
        return False


def extract_langflow_text(resp: Any) -> str:
    """
    Deterministic extractor for Langflow run responses.
    Looks for common keys where human-friendly text appears and ignores UUID-like strings.
    """
    if resp is None:
        return ""

    # 1) If top-level outputs list exists, inspect its items
    try:
        outputs = resp.get("outputs") if isinstance(resp, dict) else None
        if outputs and isinstance(outputs, list):
            for out in outputs:
                if not isinstance(out, dict):
                    continue

                # a) out['outputs'] -> message -> message
                o_outputs = out.get("outputs")
                if isinstance(o_outputs, dict):
                    msg_obj = o_outputs.get("message")
                    if isinstance(msg_obj, dict):
                        candidate = msg_obj.get("message") or msg_obj.get("text")
                        if candidate and isinstance(candidate, str) and not is_uuid(candidate):
                            return candidate.strip()

                # b) out['messages'] -> first -> message
                msgs = out.get("messages")
                if isinstance(msgs, list) and len(msgs) > 0:
                    first = msgs[0]
                    if isinstance(first, dict):
                        cand = first.get("message")
                        if cand and isinstance(cand, str) and not is_uuid(cand):
                            return cand.strip()

                # c) out['artifacts'].message
                artifacts = out.get("artifacts")
                if isinstance(artifacts, dict):
                    cand = artifacts.get("message")
                    if cand and isinstance(cand, str) and not is_uuid(cand):
                        return cand.strip()

                # d) out['results']['message']['data']['text'] (deep shape)
                results = out.get("results")
                if isinstance(results, dict):
                    msg = results.get("message")
                    if isinstance(msg, dict):
                        data = msg.get("data")
                        if isinstance(data, dict):
                            txt = data.get("text")
                            if txt and isinstance(txt, str) and not is_uuid(txt):
                                return txt.strip()
                        txt2 = msg.get("text") or msg.get("default_value")
                        if txt2 and isinstance(txt2, str) and not is_uuid(txt2):
                            return txt2.strip()
    except Exception:
        pass

    # 2) quick top-level keys
    if isinstance(resp, dict):
        for k in ("message", "text", "output", "result"):
            v = resp.get(k)
            if isinstance(v, str) and not is_uuid(v):
                return v.strip()

    # 3) safe recursive fallback: pick the longest non-UUID string (>10 chars)
    longest = ""

    def walk(x: Any):
        nonlocal longest
        if x is None:
            return
        if isinstance(x, str):
            s = x.strip()
            if not s:
                return
            if is_uuid(s):
                return
            if len(s) > len(longest) and len(s) > 10:
                longest = s
            return
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
            return
        if isinstance(x, (list, tuple)):
            for item in x:
                walk(item)
            return

    walk(resp)
    return longest.strip()


# ----------------------
# API call wrapper
# ----------------------
def call_langflow_api(user_message: str, session_id: Optional[str]) -> dict:
    if not LANGFLOW_API_KEY:
        raise RuntimeError(
            "LANGFLOW_API_KEY environment variable is not set. Set it and re-run the app."
        )

    headers = {"Content-Type": "application/json", "x-api-key": LANGFLOW_API_KEY}
    payload = {
        "output_type": "chat",
        "input_type": "chat",
        "input_value": user_message,
        "session_id": session_id or str(uuid.uuid4()),
    }

    r = requests.post(LANGFLOW_API_URL, json=payload, headers=headers, timeout=30)

    # raise if non-200
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        body = r.text
        raise RuntimeError(f"Langflow API returned HTTP {r.status_code}: {body}")

    try:
        return r.json()
    except ValueError:
        return {"raw_text": r.text}


# ----------------------
# Streamlit UI
# ----------------------
st.set_page_config(page_title="Langflow Chatbot", layout="centered")
st.title("🤖 Langflow Chatbot")
st.write("Ask anything about your documents.")

# persistent session id to preserve conversational context
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat input
user_input = st.chat_input("Ask your question...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    try:
        raw = call_langflow_api(user_input, st.session_state.session_id)
        bot_answer = extract_langflow_text(raw)
        if not bot_answer:
            if isinstance(raw, dict) and "raw_text" in raw:
                bot_answer = raw["raw_text"]
            else:
                bot_answer = "No human-readable answer found."
    except Exception as e:
        bot_answer = f"Error calling Langflow API: {e}"

    st.session_state.chat_history.append(("bot", bot_answer))

# Display chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(message)