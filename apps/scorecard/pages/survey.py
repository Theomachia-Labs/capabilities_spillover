"""Survey & Forecasting Streamlit Page."""

import streamlit as st
import pandas as pd
import sys
import json
from pathlib import Path
from io import StringIO

# Add repository root to Python path
current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent.parent
sys.path.append(str(repo_root))

from csp.data.db import init_db, get_db
from csp.survey import (
    import_from_json,
    aggregate_responses,
    generate_risk_reward_matrix,
    rank_portfolio_options,
)
from csp.survey.aggregation import get_all_topic_aggregations

# Ensure DB is initialized
init_db()

# Page Configuration
st.set_page_config(
    page_title="CSP Survey & Forecasting",
    page_icon="📊",
    layout="wide",
)


def main():
    st.title("📊 Survey & Forecasting")
    st.markdown("Import expert surveys, aggregate responses, and generate risk-reward analysis.")
    
    tab1, tab2, tab3 = st.tabs(["📥 Import", "📈 Aggregation", "⚖️ Risk-Reward Matrix"])
    
    with tab1:
        render_import_tab()
    
    with tab2:
        render_aggregation_tab()
    
    with tab3:
        render_forecasting_tab()


def render_import_tab():
    st.header("Import Survey Responses")
    
    st.markdown("""
    Upload a JSON file containing survey responses. Expected format:
    ```json
    {
        "response_id": "unique_id",
        "respondent_id": "expert_1",
        "created_at": "2026-01-28T12:00:00",
        "responses": [
            {
                "topic": "RLHF",
                "dimensions": {
                    "knowledge_accessibility": {"score": 3.5, "uncertainty": 0.3}
                }
            }
        ]
    }
    ```
    """)
    
    uploaded_file = st.file_uploader("Choose JSON file", type=["json"])
    
    if uploaded_file is not None:
        try:
            content = json.load(uploaded_file)
            st.json(content)
            
            if st.button("Import to Database"):
                # Write to temp file and import
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(content if isinstance(content, list) else [content], f)
                    temp_path = f.name
                
                with get_db() as db:
                    responses = import_from_json(db, temp_path)
                    st.success(f"✅ Imported {len(responses)} response(s)")
                    
        except Exception as e:
            st.error(f"Error: {e}")


def render_aggregation_tab():
    st.header("Aggregated Results")
    
    with get_db() as db:
        all_aggs = get_all_topic_aggregations(db)
    
    if not all_aggs:
        st.info("No survey data available. Import responses first.")
        return
    
    topic = st.selectbox("Select Topic", list(all_aggs.keys()))
    
    if topic:
        agg = all_aggs[topic]
        
        # Convert to DataFrame for display
        rows = []
        for dim_id, stats in agg.items():
            rows.append({
                "Dimension": dim_id,
                "Mean": stats["mean"],
                "Median": stats["median"],
                "Std Dev": stats["std"],
                "90% CI": f"[{stats['credible_interval_90'][0]}, {stats['credible_interval_90'][1]}]",
                "N": stats["n"],
            })
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        if rows:
            st.bar_chart(df.set_index("Dimension")[["Mean"]])


def render_forecasting_tab():
    st.header("Risk-Reward Analysis")
    
    with get_db() as db:
        all_aggs = get_all_topic_aggregations(db)
    
    if not all_aggs:
        st.info("No survey data available. Import responses first.")
        return
    
    topics = list(all_aggs.keys())
    
    st.markdown("### Generate Risk-Reward Matrix")
    
    selected_topics = st.multiselect("Select topics to analyze", topics, default=topics)
    
    if st.button("Generate Analysis") and selected_topics:
        with get_db() as db:
            assessments = generate_risk_reward_matrix(db, selected_topics)
            recommendations = rank_portfolio_options(assessments)
        
        # Display results
        st.markdown("### Portfolio Recommendations")
        
        for rec in recommendations:
            category_colors = {
                "high_priority": "🟢",
                "moderate_priority": "🟡", 
                "low_priority": "🟠",
                "caution": "🔴",
            }
            color = category_colors.get(rec["category"], "⚪")
            
            with st.expander(f"{color} #{rec['rank']}: {rec['topic']}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("CSP Score", rec["csp_score"])
                col2.metric("Safety Benefit", rec["safety_benefit"])
                col3.metric("Risk-Reward Ratio", rec["risk_reward_ratio"])
                
                st.markdown(f"**Recommendation:** {rec['recommendation']}")
                st.caption(rec["uncertainty_note"])
        
        # Summary table
        st.markdown("### Summary Table")
        summary_df = pd.DataFrame([
            {
                "Rank": r["rank"],
                "Topic": r["topic"],
                "Category": r["category"],
                "CSP": r["csp_score"],
                "Benefit": r["safety_benefit"],
                "Ratio": r["risk_reward_ratio"],
            }
            for r in recommendations
        ])
        st.dataframe(summary_df, use_container_width=True)


if __name__ == "__main__":
    main()
