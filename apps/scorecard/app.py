import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add repository root to Python path to allow imports from csp package
current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent.parent
sys.path.append(str(repo_root))

from csp.rubric.loader import load_default_rubric
from apps.scorecard.components import render_dimension_scorer
from csp.data.db import init_db, get_db
from csp.data import crud, models

# Ensure DB is initialized
init_db()

# Page Configuration
st.set_page_config(
    page_title="CSP Scorecard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    st.title("🛡️ CSP Scorecard")
    st.markdown("Assess research papers against the Capability Spillover Potential (CSP) rubric.")

    # Load Rubric
    try:
        rubric = load_default_rubric()
    except Exception as e:
        st.error(f"Failed to load rubric: {e}")
        return

    # Sidebar: Paper Metadata & Loading
    with st.sidebar:
        st.header("Paper Metadata")
        
        # Load Existing
        load_id = st.text_input("Load by Paper ID", key="load_input")
        loaded_paper = None
        
        if load_id:
            with get_db() as db:
                loaded_paper = crud.get_paper(db, load_id)
                if not loaded_paper:
                    st.warning(f"Paper {load_id} not found.")
                else:
                    st.success(f"Loaded: {loaded_paper.title}")

        # Input fields (auto-filled if loaded)
        paper_id = st.text_input("Paper ID (Internal/DOI)", 
                                 value=loaded_paper.paper_id if loaded_paper else "",
                                 key="paper_id")
        paper_title = st.text_input("Title", 
                                    value=loaded_paper.title if loaded_paper else "",
                                    key="paper_title")
        scorer_name = st.text_input("Scorer Name", key="scorer_name")
        
        st.divider()
        st.info(f"Using Rubric: **{rubric.name}** ({rubric.version})")

    # Display Paper Abstract if loaded
    if loaded_paper and loaded_paper.abstract:
        with st.expander("Paper Abstract", expanded=False):
            st.markdown(loaded_paper.abstract)

    # Main Scoring Area
    scores = {}
    
    st.subheader("Scoring Dimensions")
    
    for dim in rubric.dimensions:
        with st.container():
            st.divider()
            scores[dim.id] = render_dimension_scorer(dim, key_prefix=f"{paper_id}_{dim.id}" if paper_id else "")

    # Export/Save Section
    st.divider()
    st.header("Save Record")

    if st.button("Save Score to DB"):
        if not paper_id:
            st.warning("Please enter a Paper ID in the sidebar.")
        else:
            record_data = {
                "score_id": f"score_{paper_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "paper_id": paper_id,
                "rubric_version": rubric.version,
                "dimensions": scores,
                "provenance": {
                    "method": "human",
                    "created_at": datetime.now().isoformat(),
                    "model": scorer_name,
                    "notes": "Generated wait CSP Scorecard UI"
                }
            }
            
            # Save to DB
            try:
                with get_db() as db:
                    # Ensure paper exists first (if manual entry)
                    if not loaded_paper:
                        # minimal paper creation
                        new_paper = {
                            "paper_id": paper_id,
                            "title": paper_title or "Untitled",
                            "year": datetime.now().year
                        }
                        try:
                            # Verify if it exists again to avoid race/error
                            if not crud.get_paper(db, paper_id):
                                crud.create_paper(db, new_paper)
                        except Exception as e:
                            st.warning(f"Could not create paper record (might exist): {e}")

                    crud.create_score(db, record_data)
                    st.success("Score saved to database successfully!")
                    
                    # Also offer JSON download
                    st.json(record_data)
            except Exception as e:
                st.error(f"Error saving to database: {e}")


if __name__ == "__main__":
    main()

