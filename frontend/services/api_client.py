"""
API client for communicating with the backend.
"""
import os
import streamlit as st
import requests
from typing import Optional, Dict, Any


# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def api_request(
    endpoint: str,
    method: str = "GET",
    data: Dict = None,
    files: Dict = None,
    auth: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Make API request to backend.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, DELETE)
        data: Request data (JSON)
        files: Files to upload
        auth: Whether to include authentication token

    Returns:
        Response data or None if error
    """
    url = f"{BACKEND_URL}{endpoint}"
    headers = {}

    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None

        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Error: {error_detail}")
            return None

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend server. Please ensure the backend is running.")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None
