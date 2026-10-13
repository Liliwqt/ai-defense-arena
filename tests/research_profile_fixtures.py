"""Explicit source-bound profiles for offline room fixtures."""

from backend.question_generator import GroundedCitation
from backend.research_plan import ResearchProfile


def research_profile(reference: GroundedCitation) -> ResearchProfile:
    return ResearchProfile(("Education",), ("quantitative",), "University campus",
                           "The proposal examines a campus queue pilot.", (reference,))
