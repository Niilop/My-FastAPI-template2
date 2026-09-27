import os
from typing import Any

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="API Tester")
st.title("API Tester")
st.session_state.setdefault("access_token", None)


def api_request(method: str, path: str, **kwargs: Any) -> requests.Response | None:
    headers = {}
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    try:
        response = requests.request(
            method, f"{API_URL}{path}", headers=headers, timeout=30, **kwargs
        )
    except requests.RequestException:
        st.error("Cannot reach the API. Check that the backend is running.")
        return None
    if not response.ok:
        st.error(f"Request failed ({response.status_code}): {response.text}")
        return None
    return response


with st.sidebar:
    st.header("Authentication")
    if st.session_state.access_token is None:
        mode = st.radio("Action", ["Login", "Register"])
        with st.form("auth"):
            identifier = st.text_input("Email or username" if mode == "Login" else "Email")
            username = st.text_input("Username") if mode == "Register" else ""
            password = st.text_input("Password", type="password")
            if st.form_submit_button(mode):
                if mode == "Login":
                    response = api_request(
                        "POST", "/auth/login", data={"username": identifier, "password": password}
                    )
                    if response is not None:
                        st.session_state.access_token = response.json()["access_token"]
                        st.rerun()
                else:
                    response = api_request(
                        "POST",
                        "/auth/register",
                        json={"email": identifier, "username": username, "password": password},
                    )
                    if response is not None:
                        st.success("Registered. You can now log in.")
    else:
        if st.button("My profile"):
            response = api_request("GET", "/auth/me")
            if response is not None:
                st.json(response.json())
        if st.button("Log out"):
            st.session_state.access_token = None
            st.rerun()

example_tab, data_tab = st.tabs(["Example", "Datasets"])
with example_tab:
    with st.form("example"):
        name = st.text_input("Name", value="Developer")
        task = st.text_input("Task", value="Test the connection")
        if st.form_submit_button("Run"):
            response = api_request("POST", "/example/", json={"name": name, "task": task})
            if response is not None:
                st.json(response.json())

with data_tab:
    if st.session_state.access_token is None:
        st.info("Log in to upload or list datasets.")
    else:
        with st.form("upload"):
            dataset_name = st.text_input("Dataset name")
            description = st.text_input("Description")
            upload = st.file_uploader("CSV file", type=["csv"])
            if st.form_submit_button("Upload") and upload is not None:
                response = api_request(
                    "POST",
                    "/data/upload",
                    data={"name": dataset_name, "description": description},
                    files={"file": (upload.name, upload.getvalue(), "text/csv")},
                )
                if response is not None:
                    st.json(response.json())
        if st.button("List datasets"):
            response = api_request("GET", "/data/catalog")
            if response is not None:
                st.json(response.json())
