import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional
from csp.rubric.loader import RubricDimension

def render_evidence_input(key_prefix: str) -> List[Dict[str, str]]:
    """Render inputs for evidence (citations/snippets)."""
    st.markdown("#### Evidence")
    
    # Initialize session state for evidence count if not exists
    count_key = f"{key_prefix}_evidence_count"
    if count_key not in st.session_state:
        st.session_state[count_key] = 1

    evidence_list = []
    
    for i in range(st.session_state[count_key]):
        col1, col2 = st.columns([1, 2])
        with col1:
            citation = st.text_input("Citation ID (e.g., Smith 2023)", key=f"{key_prefix}_cit_{i}")
        with col2:
            snippet = st.text_area("Snippet/Quote", height=70, key=f"{key_prefix}_snip_{i}")
        
        if citation and snippet:
            evidence_list.append({
                "citation_id": citation,
                "snippet": snippet
            })
            
    if st.button("Add more evidence", key=f"{key_prefix}_add_btn"):
        st.session_state[count_key] += 1
        st.rerun()
        
    return evidence_list

def render_dimension_scorer(dimension: RubricDimension, key_prefix: str = "") -> Dict[str, Any]:
    """Render a scoring block for a single dimension."""
    st.markdown(f"### {dimension.name}")
    st.markdown(dimension.description)
    
    # Display anchors
    with st.expander("Show Scoring Criteria (Anchors)"):
        for score, desc in dimension.anchors.items():
            st.markdown(f"**{score}**: {desc}")

    col1, col2 = st.columns([1, 3])
    
    with col1:
        score = st.selectbox(
            "Score",
            options=[0, 1, 2, 3, 4, 5],
            index=0,
            help="Select the score based on the anchors.",
            key=f"{key_prefix}_{dimension.id}_score"
        )
        uncertainty = st.slider(
            "Uncertainty (0=Confident, 1=Guess)",
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            key=f"{key_prefix}_{dimension.id}_unc"
        )

    with col2:
        rationale = st.text_area(
            "Rationale",
            placeholder="Explain why this score applies...",
            key=f"{key_prefix}_{dimension.id}_rationale"
        )

    evidence = render_evidence_input(f"{key_prefix}_{dimension.id}")
    
    return {
        "score": score,
        "uncertainty": uncertainty,
        "rationale": rationale,
        "evidence": evidence
    }
