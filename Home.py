import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="CSP Toolkit", page_icon="🛡️", layout="wide")

st.title("Capability Spillover Potential (CSP) Toolkit")
st.markdown("""
Welcome to the CSP Toolkit MVP. This project investigates the paradoxical dynamic where AI safety research inadvertently accelerates general AI capabilities. 
""")

st.divider()

# Load data for the front page overview
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "data_sample" / "mock_csp_data.json"
    with open(file_path, "r") as f:
        return json.load(f)

data = load_data()

st.subheader("Explore the Data")
st.markdown("Use the dropdown below to select a specific case study, or navigate to the **Scorecard** in the sidebar for full details.")

# Add an interactive dropdown widget
topic_names = [item["topic_name"] for item in data]
selected_topic = st.selectbox("Select a Research Topic to preview:", topic_names)

# Display a quick summary based on the dropdown selection
for item in data:
    if item["topic_name"] == selected_topic:
        st.info(f"**Summary:** {item['description']}")
        st.warning(f"**Overall Strategic Leverage Score:** {item['dimensions']['Strategic Leverage']['score']} / 5")