import streamlit as st
import json
import pandas as pd

# --- UI Configuration ---
st.set_page_config(page_title="CSP Scorecard MVP", layout="wide")
st.title("Capability Spillover Potential (CSP) - Scorecard")
st.markdown("Early prototype displaying retrospective case study data.")
st.divider()

# --- Load Data ---
from pathlib import Path

@st.cache_data
def load_data():
    # This finds the exact path of project_page.py, goes up one folder, then into data_sample
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / "data_sample" / "mock_csp_data.json"
    
    with open(file_path, "r") as f:
        return json.load(f)

data = load_data()

# --- Render Page ---
for item in data:
    st.subheader(item["topic_name"])
    st.write(item["description"])
    
    # Create 3 columns for the 3 rubric dimensions
    cols = st.columns(3)
    
    # Dynamically unpack the dimensions from the JSON
    for i, (dim_name, dim_data) in enumerate(item["dimensions"].items()):
        with cols[i]:
            # Using delta_color="off" keeps it grey instead of red/green
            st.metric(
                label=dim_name, 
                value=f"{dim_data['score']} / 5", 
                delta=f"Uncertainty: {dim_data['uncertainty']}",
                delta_color="off"
            )
            
    st.markdown("**Evidence & Citations:**")
    for link in item["evidence_links"]:
        st.markdown(f"* [{link['label']}]({link['url']}) - *{link['note']}*")
        
    st.divider()