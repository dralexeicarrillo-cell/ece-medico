import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

def api_request(method, endpoint, data=None):
    """Función centralizada para hacer requests al API"""
    headers = {}
    if 'token' in st.session_state and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return response
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None