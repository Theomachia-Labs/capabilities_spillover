"""Policy brief generator."""

from __future__ import annotations

from datetime import datetime

from csp.reports.core import CaseStudyData
from csp.reports.figures import generate_ascii_diffusion_plot, generate_risk_table


def generate_policy_brief(data: CaseStudyData) -> str:
    """Generate a Markdown policy brief from case study data."""
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    sections = []
    
    # Header
    sections.append(f"# Policy Brief: {data.topic}")
    sections.append(f"**Date**: {date_str}")
    sections.append(f"**Papers Analyzed**: {data.paper_count}")
    sections.append(f"**Labels Analyzed**: {len(data.labels)}")
    sections.append("---")
    
    # Executive Summary
    sections.append("## Executive Summary")
    sections.append(
        f"This brief analyzes the capability spillover potential of **{data.topic}** "
        "research. "
    )
    if data.forecasting_assessment:
        ratio = data.forecasting_assessment.risk_reward_ratio
        rec = "High Priority Funding" if ratio > 2 else \
              "Caution Advised" if ratio < 0.5 else "Moderate Monitoring"
        sections.append(f"**Recommendation**: {rec}")
    sections.append("")
    
    # Key Findings / Risk Assessment
    sections.append("## Risk Assessment")
    sections.append(generate_risk_table(data))
    sections.append("")
    
    # Diffusion Analysis
    sections.append("## Diffusion Analysis")
    sections.append(generate_ascii_diffusion_plot(data))
    sections.append("")
    
    sections.append("")
    
    # Graph Analysis
    if data.graph_stats:
        gs = data.graph_stats
        sections.append("## Citation Graph Analysis")
        sections.append(f"- **Papers in Graph**: {gs['node_count']}")
        sections.append(f"- **Citations Tracked**: {gs['edge_count']}")
        sections.append(f"- **Spillover Score**: {gs['spillover_score']} (0.0 - 1.0)")
        sections.append("  *(Proportion of capability papers citing safety work)*")
        sections.append("")
    
    # Survey Insights
    sections.append("## Expert Survey Insights")
    if data.survey_stats:
        for dim, stats in data.survey_stats.items():
            sections.append(f"### {dim}")
            sections.append(f"- **Mean Score**: {stats['mean']}")
            sections.append(f"- **90% CI**: {stats['credible_interval_90']}")
            sections.append("")
    else:
        sections.append("(No expert survey data available)")
        
    # Recommendations
    sections.append("## Strategic Recommendations")
    sections.append(
        "1. **Monitor Usage**: Track citations from capabilities benchmarks.\n"
        "2. **Funding Strategy**: Adjust funding based on the Risk/Reward ratio.\n"
        "3. **Redaction**: Ensure technical details of 'capability_use' papers are not disseminated without context."
    )
        
    # Security Redaction
    from csp.security.redaction import Redactor
    redactor = Redactor()
    
    full_text = "\n".join(sections)
    return redactor.redact_text(full_text)
