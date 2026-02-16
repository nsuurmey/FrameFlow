"""
Framework assignment logic (Ticket 1.3.3).

Maps topic types to speaking frameworks.
For MVP1, all topics use PREP framework (per user specification).
"""

from clarity.session.phase_config import Framework
from clarity.session.topics import Topic


def assign_framework(topic: Topic, available_frameworks: list[Framework]) -> Framework:
    """
    Assign a framework to a topic based on topic type.

    For MVP1: All topics get PREP framework (simplified).
    Future versions will implement topic type → framework mapping.

    Args:
        topic: Topic object
        available_frameworks: Frameworks available in current phase

    Returns:
        Framework to use for this topic

    Examples:
        >>> topic = Topic("Agile", "...", "explain", 1)
        >>> assign_framework(topic, [Framework.PREP])
        <Framework.PREP: 'PREP'>
    """
    # MVP1: Always return PREP
    # This simplifies implementation while framework rotation logic is developed
    return Framework.PREP


# Future implementation (deferred to later iteration)
# TOPIC_TYPE_TO_FRAMEWORK = {
#     "explain": Framework.PREP,
#     "teach": Framework.WHAT_SO_WHAT_NOW_WHAT,
#     "persuade": Framework.PROBLEM_SOLUTION_BENEFIT,
#     "analyze": Framework.PAST_PRESENT_FUTURE,
#     "describe": Framework.STAR,
#     "custom": Framework.PREP,  # Default for custom topics
# }
#
# def assign_framework_by_type(
#     topic: Topic, available_frameworks: list[Framework]
# ) -> Framework:
#     """
#     Assign framework based on topic type mapping.
#
#     Falls back to PREP if:
#     - Topic type not in mapping
#     - Mapped framework not available in current phase
#     """
#     # Get mapped framework
#     mapped = TOPIC_TYPE_TO_FRAMEWORK.get(topic.topic_type, Framework.PREP)
#
#     # Check if available in phase
#     if mapped in available_frameworks:
#         return mapped
#
#     # Fallback to PREP (always available)
#     return Framework.PREP
