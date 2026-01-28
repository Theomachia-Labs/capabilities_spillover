"""Audit Queue Streamlit Page for Label Review."""

import streamlit as st
import sys
from pathlib import Path

# Add repository root to Python path
current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent.parent
sys.path.append(str(repo_root))

from csp.data.db import init_db, get_db
from csp.data import crud
from csp.labeling import audit
from csp.rubric.reliability import compute_cohens_kappa
from sqlalchemy import select
from csp.data.models import Label

# Ensure DB is initialized
init_db()

# Page Configuration
st.set_page_config(
    page_title="CSP Audit Queue",
    page_icon="🔍",
    layout="wide",
)


def main():
    st.title("🔍 Label Audit Queue")
    st.markdown("Review and verify AI-generated labels for research papers.")

    tab1, tab2 = st.tabs(["Queue", "Reliability Checks"])
    
    with tab1:
        render_audit_queue()
        
    with tab2:
        render_reliability_metrics()


def render_audit_queue():
    with get_db() as db:
        pending_labels = audit.get_audit_queue(db)

    if not pending_labels:
        st.success("✅ No labels pending review!")
        st.info("All labels have been verified. Check back when new labels are generated.")
        return

    st.info(f"**{len(pending_labels)}** labels pending review")

    for label_obj in pending_labels:
        with st.container():
            st.divider()
            
            # Get paper details
            with get_db() as db:
                paper = crud.get_paper(db, label_obj.paper_id)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(paper.title if paper else label_obj.paper_id)
                if paper and paper.abstract:
                    with st.expander("Abstract"):
                        st.write(paper.abstract[:500] + "..." if len(paper.abstract or "") > 500 else paper.abstract)
                
                if label_obj.evidence_spans:
                    st.markdown("**Evidence:**")
                    for span in label_obj.evidence_spans:
                        st.caption(f"• {span}")
            
            with col2:
                # Current label info
                confidence_color = "🟢" if label_obj.confidence >= 0.7 else "🟡" if label_obj.confidence >= 0.4 else "🔴"
                st.metric("Current Label", label_obj.label.replace("_", " ").title())
                st.write(f"Confidence: {confidence_color} {label_obj.confidence:.0%}")
                st.write(f"Method: `{label_obj.method}`")
                
                # Action buttons
                st.markdown("---")
                
                if st.button("✅ Approve", key=f"approve_{label_obj.label_id}"):
                    with get_db() as db:
                        audit.approve_label(db, label_obj.label_id)
                    st.success("Approved!")
                    st.rerun()
                
                # Override with correction
                corrected = st.selectbox(
                    "Or correct to:",
                    ["safety_use", "capability_use", "mixed", "unclear"],
                    index=["safety_use", "capability_use", "mixed", "unclear"].index(label_obj.label),
                    key=f"correct_{label_obj.label_id}"
                )
                
                if st.button("✏️ Apply Correction", key=f"reject_{label_obj.label_id}"):
                    with get_db() as db:
                        audit.reject_label(db, label_obj.label_id, corrected)
                    st.success(f"Corrected to: {corrected}")
                    st.rerun()
                if st.button("✏️ Apply Correction", key=f"reject_{label_obj.label_id}"):
                    with get_db() as db:
                        audit.reject_label(db, label_obj.label_id, corrected)
                    st.success(f"Corrected to: {corrected}")
                    st.rerun()


def render_reliability_metrics():
    st.markdown("### Inter-Rater Reliability")
    st.markdown("Compare agreement between LLM predictions and Human corrections (verified labels).")
    
    with get_db() as db:
        # Fetch all verified labels that started as LLM predictions
        # Strategy: Find verified labels where method='llm' (which means approved LLM)
        # OR labels that were corrected (method='human' but might have history).
        # For MVP, let's just compare 'llm' Method vs 'human' Method on same papers?
        # Actually simplest is: Compare 'pending' (original LLM) vs 'verified' (Human Final)
        # But pending labels convert to verified. We lose the original state unless we track history.
        # MVP Hack: Compare labels where method='llm' vs method='human' if both exist for same paper?
        # Better MVP: Just show stats for all labels currently in DB.
        
        labels = db.execute(select(Label)).scalars().all()
        
    if not labels:
        st.info("No labels found.")
        return
        
    # Stats
    total = len(labels)
    llm_count = sum(1 for l in labels if l.method == "llm")
    human_count = sum(1 for l in labels if l.method == "human")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Labels", total)
    col2.metric("LLM Labels", llm_count)
    col3.metric("Human Labels", human_count)
    
    # Placeholder for Kappa if we had paired data
    # (Real implementation needs a table tracking [PaperID, RaterID, Label])
    st.info("ℹ️ To compute Cohen's Kappa, we need paired ratings (same paper rated by 2 inputs). currently storing one final label per paper.")


if __name__ == "__main__":
    main()
