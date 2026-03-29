import json
import sys
import streamlit as st
import plotly.graph_objects as go
from pathlib import Path

# Add repository root to Python path
current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent.parent.parent
sys.path.append(str(repo_root))

st.set_page_config(page_title="CSP Paper Map", layout="wide")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    file_path = repo_root / "data_sample" / "mock_csp_data.json"
    with open(file_path, "r") as f:
        return json.load(f)

papers = load_data()

# ---------------------------------------------------------------------------
# Tag definitions (MVP: hardcoded until pipeline adds them)
# ---------------------------------------------------------------------------

PAPER_META = {
    "Process Reward Models (PRM)": {
        "x": 1.2, "y": 0.8,
        "tags": ["training-techniques", "test-time-compute", "2023"],
        "rating_count": 3,
    },
    "Constitutional AI (CAI)": {
        "x": 0.5, "y": 0.3,
        "tags": ["training-techniques", "alignment", "2022"],
        "rating_count": 2,
    },
    "Reinforcement Learning from Human Feedback (RLHF)": {
        "x": 0.8, "y": -0.2,
        "tags": ["training-techniques", "alignment", "2019"],
        "rating_count": 7,
    },
    "Mechanistic Interpretability (Circuits)": {
        "x": -1.5, "y": 0.5,
        "tags": ["interpretability", "circuits", "2020"],
        "rating_count": 4,
    },
}

ALL_TAGS = sorted({
    tag
    for meta in PAPER_META.values()
    for tag in meta["tags"]
})

# ---------------------------------------------------------------------------
# Sidebar: tag filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filter by Tag")
selected_tags = st.sidebar.multiselect(
    "Show papers with any of these tags:",
    options=ALL_TAGS,
    default=[],
    help="Leave empty to show all papers.",
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Tag legend**")
st.sidebar.markdown(
    "- `training-techniques` — RLHF, CAI, PRM family\n"
    "- `interpretability` — circuits / mech interp\n"
    "- `alignment` — explicit alignment framing\n"
    "- `test-time-compute` — inference-time scaling\n"
    "- `circuits` — circuits-based analysis\n"
    "- Year tags filter by publication year"
)

show_sparse = st.sidebar.checkbox("Only show papers with < 10 ratings", value=False)

# ---------------------------------------------------------------------------
# Filter papers
# ---------------------------------------------------------------------------

def paper_passes_filter(topic_name):
    meta = PAPER_META.get(topic_name, {})
    if show_sparse and meta.get("rating_count", 0) >= 10:
        return False
    if selected_tags:
        return bool(set(meta.get("tags", [])) & set(selected_tags))
    return True

visible_papers = [p for p in papers if paper_passes_filter(p["topic_name"])]

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.title("CSP Paper Map")
st.caption(
    "Each node is a reviewed paper. Distance and clustering reflect topical relatedness. "
    "Click a paper in the list below to expand its scorecard."
)

# ---------------------------------------------------------------------------
# Build Plotly figure
# ---------------------------------------------------------------------------

CLUSTER_COLORS = {
    "training-techniques": "#4C8BF5",
    "interpretability": "#F5A623",
}

def node_color(topic_name):
    tags = PAPER_META.get(topic_name, {}).get("tags", [])
    for cluster, color in CLUSTER_COLORS.items():
        if cluster in tags:
            return color
    return "#AAAAAA"

xs, ys, labels, colors, hovers = [], [], [], [], []

for p in visible_papers:
    name = p["topic_name"]
    meta = PAPER_META.get(name, {"x": 0, "y": 0, "tags": [], "rating_count": 0})
    xs.append(meta["x"])
    ys.append(meta["y"])
    labels.append(name)
    colors.append(node_color(name))

    dims = p["dimensions"]
    hover_lines = [f"<b>{name}</b><br>"]
    for dim, v in dims.items():
        hover_lines.append(f"{dim}: {v['score']}/5 (±{v['uncertainty']})")
    hover_lines.append(f"<br>Ratings: {meta['rating_count']}")
    hover_lines.append(f"Tags: {', '.join(meta['tags'])}")
    hovers.append("<br>".join(hover_lines))

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=xs,
    y=ys,
    mode="markers+text",
    marker=dict(size=28, color=colors, line=dict(width=2, color="white")),
    text=labels,
    textposition="top center",
    textfont=dict(size=12, color="#000000"),
    hovertemplate="%{customdata}<extra></extra>",
    customdata=hovers,
))

fig.update_layout(
    height=520,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="#ffffff",
    plot_bgcolor="#ffffff",
    xaxis=dict(visible=False, zeroline=False),
    yaxis=dict(visible=False, zeroline=False),
    showlegend=False,
    dragmode="pan",
)

if not selected_tags or "training-techniques" in selected_tags:
    fig.add_annotation(
        x=0.85, y=-0.55, text="● Training Techniques",
        showarrow=False, font=dict(size=13, color="#4C8BF5"),
        xref="x", yref="y",
    )
if not selected_tags or "interpretability" in selected_tags:
    fig.add_annotation(
        x=-1.5, y=0.0, text="● Interpretability",
        showarrow=False, font=dict(size=13, color="#F5A623"),
        xref="x", yref="y",
    )

st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True})

# ---------------------------------------------------------------------------
# Detail panels
# ---------------------------------------------------------------------------

if not visible_papers:
    st.info("No papers match the current filters.")
else:
    st.subheader("Paper Scorecards")
    for p in visible_papers:
        name = p["topic_name"]
        meta = PAPER_META.get(name, {})
        tag_badges = " ".join(f"`{t}`" for t in meta.get("tags", []))
        rating_note = (
            f":orange[{meta['rating_count']} ratings — sparse]"
            if meta.get("rating_count", 0) < 10
            else f"{meta['rating_count']} ratings"
        )

        with st.expander(f"**{name}** — {rating_note}   {tag_badges}"):
            st.caption(p.get("description", ""))
            st.markdown("**Scorecard dimensions**")

            cols = st.columns(len(p["dimensions"]))
            for col, (dim, v) in zip(cols, p["dimensions"].items()):
                col.metric(
                    label=dim,
                    value=f"{v['score']} / 5",
                    delta=f"Uncertainty: {v['uncertainty']}",
                    delta_color="off",
                )

            st.markdown("**Evidence & Citations**")
            for link in p.get("evidence_links", []):
                st.markdown(f"- [{link['label']}]({link['url']}) — *{link['note']}*")
