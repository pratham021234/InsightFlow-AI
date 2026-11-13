import os
import json
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd

def get_api_key() -> Optional[str]:
    """Retrieve Gemini API key safely from Streamlit secrets or OS environment."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            key = str(st.secrets["GEMINI_API_KEY"]).strip()
            if key and not key.startswith("your_") and not key.startswith("AQ."):
                return key
            elif key:
                # Key exists but is dummy/OAuth token
                return key
    except Exception:
        pass
        
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
        
    # Check secrets.toml file directly as fallback
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip("\"'")
        except Exception:
            pass
            
    return None

def check_gemini_status() -> Tuple[bool, str]:
    """Check if Gemini API is configured and operational."""
    key = get_api_key()
    if not key:
        return False, "No Gemini API key configured. Configure GEMINI_API_KEY in .streamlit/secrets.toml or as an environment variable."
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        # Try a minimal fast call
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content("Ping", request_options={"timeout": 5})
        if resp and resp.text:
            return True, "Connected to Google Gemini API"
        return False, "Gemini API returned an empty response."
    except Exception as e:
        err_msg = str(e)
        if "API key not valid" in err_msg or "401" in err_msg or "API_KEY_INVALID" in err_msg or "UNSUPPORTED" in err_msg:
            return False, "Gemini API key is invalid or unauthorized."
        elif "quota" in err_msg.lower() or "429" in err_msg:
            return False, "Gemini API quota exceeded or rate limit reached."
        elif "timeout" in err_msg.lower() or "deadline" in err_msg.lower():
            return False, "Gemini API request timed out."
        return False, f"Gemini API connection error: {err_msg[:120]}"

def query_gemini(prompt: str, system_instruction: str = "", timeout_secs: int = 12) -> Tuple[Optional[str], Optional[str]]:
    """
    Execute a safe query against Google Gemini.
    Returns: (response_text, error_message)
    """
    key = get_api_key()
    if not key:
        return None, "No API key configured. Running in local rule-based mode."
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=system_instruction if system_instruction else None
        )
        
        response = model.generate_content(prompt, request_options={"timeout": timeout_secs})
        if response and response.text:
            return response.text.strip(), None
        return None, "Received empty response from Gemini."
    except Exception as e:
        err_str = str(e)
        if "API key not valid" in err_str or "401" in err_str or "UNSUPPORTED" in err_str:
            return None, "Invalid Gemini API key. Please check your credentials in .streamlit/secrets.toml."
        elif "429" in err_str or "quota" in err_str.lower():
            return None, "Gemini API rate limit or quota exceeded."
        elif "timeout" in err_str.lower():
            return None, "Gemini API request timed out."
        return None, f"Gemini API error: {err_str[:120]}"

