"""Research failure types for ResearchOS."""


class ResearchFailure(Exception):
    """Base class for research execution failures."""


class TransientResearchFailure(ResearchFailure):
    """A temporary failure that may succeed on retry."""


class PermanentResearchFailure(ResearchFailure):
    """A failure that should not be retried."""
