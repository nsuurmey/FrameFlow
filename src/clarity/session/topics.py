"""
Topic pool & rotation management (Ticket 1.3.2).

Loads 20 business topics, tracks usage, ensures no repeats until pool exhausted.
Supports topic override via --topic parameter.
"""

import random
from dataclasses import dataclass


@dataclass
class Topic:
    """A practice topic with metadata."""

    title: str
    description: str
    topic_type: str  # explain, teach, persuade, etc.
    topic_id: int  # Unique ID for tracking


# All 20 business topics from docs/20-business-topics.md
# Categorized by topic type for phase-appropriate selection
TOPIC_POOL = [
    # EXPLAIN topics (Phase 1+)
    Topic(
        title="The Shift to Agile Project Management",
        description="Agile methodology focuses on iterative development and constant feedback rather than a rigid, linear path. This allows managers to pivot quickly in response to market changes and improves team collaboration.",
        topic_type="explain",
        topic_id=1,
    ),
    Topic(
        title="Supply Chain Resilience in a Volatile World",
        description='Modern managers are moving away from "just-in-time" inventory toward "just-in-case" strategies to avoid disruptions. This involves diversifying suppliers and leveraging AI to predict potential bottlenecks before they happen.',
        topic_type="explain",
        topic_id=2,
    ),
    Topic(
        title="Total Quality Management (TQM)",
        description="TQM is a management approach centered on long-term success through customer satisfaction. It requires every employee in an organization to focus on continuous improvement of processes, products, and services.",
        topic_type="explain",
        topic_id=3,
    ),
    Topic(
        title="The Impact of Lean Six Sigma",
        description="Lean Six Sigma combines waste reduction with process variation control to maximize efficiency. By identifying and removing defects, managers can significantly lower operational costs while increasing product value.",
        topic_type="explain",
        topic_id=4,
    ),
    Topic(
        title="The Role of Big Data in Strategic Planning",
        description="Big data allows managers to identify trends and patterns that were previously invisible. By leveraging this information, businesses can personalize marketing efforts and optimize their internal resource allocation.",
        topic_type="explain",
        topic_id=10,
    ),
    Topic(
        title="Digital Transformation Management",
        description="Digital transformation involves more than just buying new software; it requires a complete overhaul of how a business operates. Successful managers lead this change by aligning technology goals with overall business objectives.",
        topic_type="explain",
        topic_id=12,
    ),
    # TEACH topics (Phase 1+)
    Topic(
        title="Managing Hybrid Work Cultures",
        description="The rise of remote and hybrid work requires managers to focus on outcomes rather than hours spent at a desk. Building trust and maintaining a cohesive company culture across digital platforms is now a critical leadership skill.",
        topic_type="teach",
        topic_id=5,
    ),
    Topic(
        title="Psychological Safety in the Workplace",
        description="Managers who foster psychological safety encourage employees to take risks and voice concerns without fear of punishment. This environment is proven to drive innovation and prevent high-stakes organizational errors.",
        topic_type="teach",
        topic_id=6,
    ),
    Topic(
        title="Emotional Intelligence (EQ) in Leadership",
        description="A leader's ability to recognize and regulate their own emotions, while empathizing with others, is often more predictive of success than IQ. High EQ helps in navigating office politics and resolving team conflicts effectively.",
        topic_type="teach",
        topic_id=7,
    ),
    Topic(
        title="Conflict Resolution Strategies",
        description="Managers spend a significant amount of time mediating disputes between team members. Understanding different styles of conflict—such as collaborating versus compromising—is vital for maintaining a productive work environment.",
        topic_type="teach",
        topic_id=19,
    ),
    # PERSUADE topics (Phase 2+)
    Topic(
        title="Inclusive Leadership and DE&I",
        description="Diversity, Equity, and Inclusion (DE&I) are no longer just HR buzzwords but essential pillars of a modern business strategy. Inclusive leaders actively seek diverse perspectives to avoid groupthink and better understand a global customer base.",
        topic_type="persuade",
        topic_id=8,
    ),
    Topic(
        title="Environmental, Social, and Governance (ESG) Criteria",
        description="Investors and consumers are increasingly holding companies accountable for their impact on the planet and society. Managers must integrate ESG goals into their business models to ensure long-term sustainability and brand loyalty.",
        topic_type="persuade",
        topic_id=13,
    ),
    Topic(
        title="Ethical Leadership and Corporate Responsibility",
        description="In an era of high transparency, managers must lead with a clear ethical compass to maintain public trust. Corporate Social Responsibility (CSR) initiatives help businesses give back to the community while enhancing their brand image.",
        topic_type="persuade",
        topic_id=16,
    ),
    Topic(
        title="Employee Engagement and Retention",
        description="High turnover is costly, making employee engagement a top priority for modern management. Strategies often include providing clear career development paths, recognition programs, and a healthy work-life balance.",
        topic_type="persuade",
        topic_id=20,
    ),
    # ANALYZE topics (Phase 2+)
    Topic(
        title="Integrating AI into Managerial Decision-Making",
        description="Artificial Intelligence is transforming management by providing real-time data analytics for faster decision-making. Managers must learn to balance machine-generated insights with human intuition and ethical oversight.",
        topic_type="analyze",
        topic_id=9,
    ),
    Topic(
        title="Cybersecurity as a Management Responsibility",
        description="Cybersecurity is no longer just an IT issue; it is a critical business risk that managers must oversee. Leaders need to cultivate a 'security-first' culture to protect intellectual property and customer data.",
        topic_type="analyze",
        topic_id=11,
    ),
    Topic(
        title="Change Management Models",
        description="Managing organizational change requires a structured approach, such as Kotter's 8-Step Process, to minimize employee resistance. Success depends on clear communication and getting 'buy-in' from key stakeholders early in the process.",
        topic_type="analyze",
        topic_id=17,
    ),
    # DESCRIBE topics (Phase 1+)
    Topic(
        title="Value-Based Management (VBM)",
        description="VBM focuses on making decisions that maximize shareholder value over time. It requires managers to link every operational goal back to the company's cost of capital and overall financial performance.",
        topic_type="describe",
        topic_id=14,
    ),
    Topic(
        title="Crisis Management and Continuity Planning",
        description="Crisis management involves preparing for high-impact, low-probability events like natural disasters or financial crashes. A solid plan ensures that the business can maintain core functions and protect its reputation during a 'black swan' event.",
        topic_type="describe",
        topic_id=15,
    ),
    Topic(
        title='The "Flat" Organizational Structure',
        description="Moving away from traditional hierarchies, many modern firms adopt flat structures to speed up communication. This empowers lower-level employees to make decisions, though it requires high levels of self-discipline and accountability.",
        topic_type="describe",
        topic_id=18,
    ),
]


class TopicManager:
    """
    Manages topic selection and rotation tracking.

    Ensures no topic repeats until the full pool has been exhausted.
    Supports phase-appropriate filtering and manual override.
    """

    def __init__(self, storage_manager):
        """
        Initialize topic manager.

        Args:
            storage_manager: StorageManager instance for tracking used topics
        """
        self.storage = storage_manager

    def _get_used_topic_ids(self) -> set[int]:
        """
        Get set of topic IDs used in current rotation.

        Returns:
            Set of topic_id values
        """
        try:
            data = self.storage.read_all()
            return set(data.get("topic_rotation", {}).get("used_ids", []))
        except Exception:
            # Storage not initialized or key missing
            return set()

    def _mark_topic_used(self, topic_id: int) -> None:
        """
        Mark a topic as used in current rotation.

        Args:
            topic_id: ID of topic to mark
        """
        data = self.storage.read_all()

        if "topic_rotation" not in data:
            data["topic_rotation"] = {"used_ids": [], "rotation_count": 0}

        used_ids = set(data["topic_rotation"]["used_ids"])
        used_ids.add(topic_id)

        # Check if pool exhausted
        if len(used_ids) >= len(TOPIC_POOL):
            # Reset rotation
            data["topic_rotation"]["used_ids"] = [topic_id]
            data["topic_rotation"]["rotation_count"] = (
                data["topic_rotation"].get("rotation_count", 0) + 1
            )
        else:
            data["topic_rotation"]["used_ids"] = list(used_ids)

        # Write updated data using atomic write
        self.storage._atomic_write(self.storage.sessions_file, data)

    def get_topic(
        self,
        allowed_types: list[str] | None = None,
        override_title: str | None = None,
    ) -> Topic:
        """
        Select a topic for the current session.

        Args:
            allowed_types: List of allowed topic types (e.g., ["explain", "teach"])
                          If None, all types are allowed.
            override_title: Manual topic override (user provided via --topic)
                           If provided, creates custom topic and skips rotation

        Returns:
            Selected Topic

        Raises:
            ValueError: If no topics match criteria
        """
        # Handle manual override
        if override_title:
            return Topic(
                title=override_title,
                description="User-provided topic (custom)",
                topic_type="custom",
                topic_id=-1,  # Special ID for custom topics
            )

        # Filter by allowed types
        if allowed_types:
            pool = [t for t in TOPIC_POOL if t.topic_type in allowed_types]
        else:
            pool = TOPIC_POOL

        if not pool:
            raise ValueError(f"No topics available for types: {allowed_types}")

        # Get used topics in current rotation
        used_ids = self._get_used_topic_ids()

        # Filter out used topics
        available = [t for t in pool if t.topic_id not in used_ids]

        # If all topics in filtered pool have been used, reset
        if not available:
            available = pool

        # Select random topic from available
        topic = random.choice(available)

        # Mark as used
        self._mark_topic_used(topic.topic_id)

        return topic

    def get_topic_by_id(self, topic_id: int) -> Topic | None:
        """
        Retrieve a topic by its ID.

        Args:
            topic_id: Unique topic ID

        Returns:
            Topic if found, None otherwise
        """
        for topic in TOPIC_POOL:
            if topic.topic_id == topic_id:
                return topic
        return None

    def get_rotation_stats(self) -> dict[str, int]:
        """
        Get statistics about topic rotation.

        Returns:
            Dictionary with rotation_count and topics_used_in_current_rotation
        """
        try:
            data = self.storage.read_all()
            rotation_data = data.get("topic_rotation", {})
            return {
                "rotation_count": rotation_data.get("rotation_count", 0),
                "topics_used": len(rotation_data.get("used_ids", [])),
                "topics_remaining": len(TOPIC_POOL)
                - len(rotation_data.get("used_ids", [])),
            }
        except Exception:
            return {
                "rotation_count": 0,
                "topics_used": 0,
                "topics_remaining": len(TOPIC_POOL),
            }


def parse_custom_topic(user_input: str) -> Topic:
    """
    Parse user-provided topic string into Topic object.

    Args:
        user_input: User's custom topic text

    Returns:
        Topic object with custom type
    """
    # Clean up input
    title = user_input.strip()

    # If it's very long, truncate title and use rest as description
    if len(title) > 100:
        description = title
        title = title[:97] + "..."
    else:
        description = f"User-provided topic: {title}"

    return Topic(
        title=title,
        description=description,
        topic_type="custom",
        topic_id=-1,
    )
