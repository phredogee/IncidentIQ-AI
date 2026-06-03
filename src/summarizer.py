import os
from openai import OpenAI
import streamlit as st

@st.cache_data(show_spinner="Generating DeepSeek Executive Summary...")
def generate_executive_summary(metrics, top_category, top_severity, top_keywords, filtered_incidents_json):
    """
    Sends filtered incident data to DeepSeek to generate an operational narrative.
    Replaces the previous Anthropic Claude implementation.
    """
    # Initialize the client pointing to DeepSeek's endpoint
    # Ensure DEEPSEEK_API_KEY is set in your .streamlit/secrets.toml or environment
    api_key = os.environ.get("DEEPSEEK_API_KEY") or st.secrets.get("DEEPSEEK_API_KEY")
    
    if not api_key:
        # Fallback to your existing templated summary logic if no key is present
        return fallback_templated_summary(filtered_incidents_json)

    client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key=api_key
    )
    
    system_prompt = (
        "You are an IT Operations Lead assistant. Provide a concise, stakeholder-ready "
        "narrative summary of the provided incident batch. You must ground your summary "
        "in real numbers and specific ticket IDs from the data. Do not use generic placeholders."
    )
    
    try:
        # Using deepseek-chat for standard conversational/analytical tasks
        response = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze these incidents:\n{filtered_incidents_json}"}
            ],
            stream=False,
            temperature=0.2
        )
        
        # Extract the text from the OpenAI/DeepSeek response structure
        return response.choices[0].message.content

    except Exception as e:
        st.error(f"DeepSeek API Error: {e}")
        return fallback_templated_summary(filtered_incidents_json)
