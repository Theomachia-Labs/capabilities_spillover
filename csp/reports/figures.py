"""Visualization utilities for case study reports."""

from __future__ import annotations

from csp.reports.core import CaseStudyData


def generate_ascii_diffusion_plot(data: CaseStudyData) -> str:
    """Generate a simple ASCII bar chart of labels over year.
    
    Using ASCII to avoid matplotlib dependency complexity for MVP artifact generation.
    """
    if not data.labels:
        return "(No label data available for diffusion plot)"
        
    # Aggregate counts by year and label
    counts: dict[int, dict[str, int]] = {}
    
    # We need to map labels back to papers to get years
    paper_years = {p.paper_id: p.year for p in data.papers if p.year}
    
    for label in data.labels:
        pid = label["paper_id"]
        year = paper_years.get(pid)
        if not year:
            continue
            
        if year not in counts:
            counts[year] = {"safety_use": 0, "capability_use": 0, "mixed": 0, "other": 0}
            
        lbl_type = label["label"]
        if lbl_type in counts[year]:
            counts[year][lbl_type] += 1
        else:
            counts[year]["other"] += 1
            
    # Draw chart
    years = sorted(counts.keys())
    if not years:
        return "(No year data available)"
    
    lines = ["**Label Diffusion Over Time**", ""]
    
    for year in years:
        c = counts[year]
        total = sum(c.values())
        if total == 0:
            continue
            
        # Draw bars
        # Scale: 10 chars = 100% (roughly)
        
        s_bar = "S" * c["safety_use"]
        c_bar = "C" * c["capability_use"]
        m_bar = "M" * c["mixed"]
        
        lines.append(f"{year} |{s_bar}{c_bar}{m_bar} ({total} papers)")
        
    lines.append("")
    lines.append("Legend: S=Safety, C=Capabilities, M=Mixed")
    
    return "\n".join(lines)


def generate_risk_table(data: CaseStudyData) -> str:
    """Generate Markdown table for risk assessment."""
    assess = data.forecasting_assessment
    if not assess:
        return "(No forecasting assessment available)"
        
    return f"""
| Metric | Value | Uncertainty |
|--------|-------|-------------|
| CSP Score (Risk) | {assess.csp_score} | ±{assess.csp_uncertainty} |
| Safety Benefit | {assess.safety_benefit} | ±{assess.safety_benefit_uncertainty} |
| **Risk/Reward Ratio** | **{assess.risk_reward_ratio}** | |
"""
