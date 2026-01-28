"""Reports subsystem.

Provides case study aggregation and policy brief generation.
"""

from csp.reports.core import CaseStudyData, gather_case_study_data
from csp.reports.figures import generate_ascii_diffusion_plot, generate_risk_table
from csp.reports.policy_brief import generate_policy_brief

__all__ = [
    "CaseStudyData",
    "gather_case_study_data",
    "generate_ascii_diffusion_plot",
    "generate_risk_table",
    "generate_policy_brief",
]
