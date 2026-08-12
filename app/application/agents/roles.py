"""Specialized agent role definitions for ResearchOS."""

from enum import StrEnum


class AgentRole(StrEnum):
    """Supported roles in the multi-agent research system."""

    RETRIEVAL = "retrieval"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
