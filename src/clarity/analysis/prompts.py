"""
Analysis prompt assembly (Tickets 1.4.2, 1.4.3, 1.4.4).

Builds phase-gated prompts with rubrics, lexicons, and framework definitions.
"""

from clarity.session.phase_config import Framework, Phase, PhaseConfig
from clarity.transcription.metrics import FILLER_LEXICON

# ===== RUBRIC DEFINITIONS =====

# 5-Dimension Rubric (from PRD)
DIMENSION_RUBRICS = {
    "filler_frequency": {
        "name": "Filler Frequency",
        "description": "Use of filler words (um, uh, like, so) and verbal pauses",
        "scoring": {
            "Excellent (90-100)": "≤2 fillers/min, strategic pauses replace fillers",
            "Strong (75-89)": "3-4 fillers/min, mostly at transitions",
            "Competent (50-74)": "5-7 fillers/min, noticeable but not distracting",
            "Developing (0-49)": ">7 fillers/min, frequent and disruptive",
        },
        "phases": [Phase.PHASE_1, Phase.PHASE_2, Phase.PHASE_3],
    },
    "structural_clarity": {
        "name": "Structural Clarity",
        "description": "Framework adherence and logical organization",
        "scoring": {
            "Excellent (90-100)": "All framework components present, seamless transitions",
            "Strong (75-89)": "All components present, mostly smooth flow",
            "Competent (50-74)": "Most components present, some gaps or unclear order",
            "Developing (0-49)": "Missing key components, disorganized",
        },
        "phases": [Phase.PHASE_1, Phase.PHASE_2, Phase.PHASE_3],
    },
    "conceptual_precision": {
        "name": "Conceptual Precision",
        "description": "Clarity of thought and avoidance of false starts/mazes",
        "scoring": {
            "Excellent (90-100)": "No mazes, each sentence completes clearly",
            "Strong (75-89)": "1-2 minor false starts, quickly corrected",
            "Competent (50-74)": "2-4 mazes, somewhat impacts clarity",
            "Developing (0-49)": ">4 mazes, frequent self-interruptions",
        },
        "phases": [Phase.PHASE_2, Phase.PHASE_3],
    },
    "hedging_control": {
        "name": "Hedging Control",
        "description": "Minimization of hedging language (kind of, sort of, maybe)",
        "scoring": {
            "Excellent (90-100)": "≤1 hedge/min, confident language",
            "Strong (75-89)": "2-3 hedges/min, mostly confident",
            "Competent (50-74)": "4-5 hedges/min, noticeable hesitation",
            "Developing (0-49)": ">5 hedges/min, undermines authority",
        },
        "phases": [Phase.PHASE_2, Phase.PHASE_3],
    },
    "vocal_delivery": {
        "name": "Vocal Delivery",
        "description": "Pacing, pause quality, and vocal variety (proxy: user comfort rating)",
        "scoring": {
            "Excellent (90-100)": "130-160 WPM, pauses at syntactic boundaries, comfortable",
            "Strong (75-89)": "120-170 WPM, mostly good pacing, minor issues",
            "Competent (50-74)": "100-180 WPM, some rushed or dragging sections",
            "Developing (0-49)": "<100 or >180 WPM, poor pause placement",
        },
        "phases": [Phase.PHASE_3],
    },
}


# Hedging lexicon (Phase 2+)
HEDGING_LEXICON = {
    "kind of",
    "sort of",
    "maybe",
    "perhaps",
    "I think",
    "I guess",
    "probably",
    "possibly",
    "somewhat",
    "fairly",
    "rather",
    "quite",
    "a bit",
}


# ===== FRAMEWORK DEFINITIONS =====

FRAMEWORK_DEFINITIONS = {
    Framework.PREP: {
        "name": "PREP",
        "components": [
            "Point (main message upfront)",
            "Reason (why it matters)",
            "Example (evidence or story)",
            "Point (restate with clarity)",
        ],
        "example": "Point: 'Agile increases team velocity.' Reason: 'It enables rapid iteration.' Example: 'At my company, sprint cycles cut delivery time by 40%.' Point: 'Agile clearly drives faster results.'",
    },
    Framework.WHAT_SO_WHAT_NOW_WHAT: {
        "name": "What-So What-Now What",
        "components": [
            "What (the situation or fact)",
            "So What (why it matters)",
            "Now What (action or implication)",
        ],
        "example": "What: 'Remote work is now standard.' So What: 'This changes how we build culture.' Now What: 'We need new rituals for connection.'",
    },
    Framework.PROBLEM_SOLUTION_BENEFIT: {
        "name": "Problem-Solution-Benefit",
        "components": [
            "Problem (what's wrong)",
            "Solution (how to fix it)",
            "Benefit (why this solution wins)",
        ],
        "example": "Problem: 'Meetings waste time.' Solution: 'Use async updates instead.' Benefit: 'Saves 5 hours/week per person.'",
    },
}


# ===== FEW-SHOT EXAMPLES =====

FEW_SHOT_EXAMPLES = """
## Example 1: High Filler Usage
Transcript: "Um, so like, the thing is, uh, we need to, you know, actually focus on, um, customer feedback."
Analysis: 7 fillers in 15 words (47% filler rate) → Developing (30/100)

## Example 2: Good Framework Adherence
Transcript: "Agile increases velocity. It enables rapid iteration. At my company, sprints cut delivery time by 40%. Clearly, Agile drives results."
Analysis: All PREP components present, smooth transitions → Excellent (95/100)

## Example 3: Maze/False Start
Transcript: "The issue is— well, actually, what I mean is— let me start over. The real problem is unclear requirements."
Analysis: Multiple false starts, conceptual imprecision → Competent (60/100)
"""


# ===== PROMPT BUILDERS =====


def build_analysis_prompt(
    phase_config: PhaseConfig,
    framework: Framework,
    transcript: str,
    baseline_metrics: dict | None = None,
    recent_metrics: list[dict] | None = None,
) -> str:
    """
    Build phase-gated analysis prompt.

    Args:
        phase_config: PhaseConfig for current phase
        framework: Framework being used
        transcript: Transcript to analyze
        baseline_metrics: User's baseline metrics (optional)
        recent_metrics: Last 5 session metrics (optional)

    Returns:
        Complete analysis prompt string
    """
    # Start with system message
    prompt_parts = [
        "You are an expert speaking coach analyzing a practice transcript.",
        "",
        "# Your Task",
        f"Analyze this transcript against the {framework.value} framework.",
        "Provide scores (0-100) for each active dimension and 3 actionable tips.",
        "",
    ]

    # Add active dimensions rubric (phase-gated)
    prompt_parts.append("# Scoring Rubric")
    prompt_parts.append("")
    for rubric in DIMENSION_RUBRICS.values():
        if any(phase == phase_config.phase for phase in rubric["phases"]):
            prompt_parts.append(f"## {rubric['name']}")
            prompt_parts.append(rubric["description"])
            prompt_parts.append("")
            for rating, criteria in rubric["scoring"].items():
                prompt_parts.append(f"- {rating}: {criteria}")
            prompt_parts.append("")

    # Add filler lexicon
    prompt_parts.append("# Filler Words to Detect")
    prompt_parts.append(", ".join(sorted(FILLER_LEXICON)[:20]))  # First 20 for brevity
    prompt_parts.append("")

    # Add hedging lexicon (Phase 2+)
    if phase_config.phase in [Phase.PHASE_2, Phase.PHASE_3]:
        prompt_parts.append("# Hedging Language to Detect")
        prompt_parts.append(", ".join(sorted(HEDGING_LEXICON)))
        prompt_parts.append("")

    # Add framework definition
    if framework in FRAMEWORK_DEFINITIONS:
        fw_def = FRAMEWORK_DEFINITIONS[framework]
        prompt_parts.append(f"# {fw_def['name']} Framework")
        prompt_parts.append("Components:")
        for i, component in enumerate(fw_def["components"], 1):
            prompt_parts.append(f"{i}. {component}")
        prompt_parts.append("")
        prompt_parts.append(f"Example: {fw_def['example']}")
        prompt_parts.append("")

    # Add few-shot examples
    prompt_parts.append("# Calibration Examples")
    prompt_parts.append(FEW_SHOT_EXAMPLES)
    prompt_parts.append("")

    # Add baseline context (if available)
    if baseline_metrics:
        prompt_parts.append("# User's Baseline (for comparison)")
        prompt_parts.append(f"- Filler rate: {baseline_metrics.get('filler_rate', 'N/A')}/min")
        prompt_parts.append(f"- WPM: {baseline_metrics.get('speaking_rate_wpm', 'N/A')}")
        prompt_parts.append("")

    # Add recent performance context (if available)
    if recent_metrics and len(recent_metrics) > 0:
        avg_filler = sum(m.get("filler_rate", 0) for m in recent_metrics) / len(recent_metrics)
        prompt_parts.append("# Recent Performance (last 5 sessions)")
        prompt_parts.append(f"- Average filler rate: {avg_filler:.1f}/min")
        prompt_parts.append("")

    # Add output format instructions
    prompt_parts.append("# Output Format (JSON)")
    prompt_parts.append("Return a JSON object with this exact structure:")
    prompt_parts.append("")
    prompt_parts.append("{")
    prompt_parts.append('  "dimension_scores": [')
    prompt_parts.append("    {")
    prompt_parts.append('      "dimension": "Filler Frequency",')
    prompt_parts.append('      "score": 75,')
    prompt_parts.append('      "rating": "Strong",')
    prompt_parts.append('      "feedback": "Brief dimension-specific feedback"')
    prompt_parts.append("    }")
    prompt_parts.append("  ],")
    prompt_parts.append('  "composite_score": 78,')
    prompt_parts.append('  "tips": [')
    prompt_parts.append("    {")
    prompt_parts.append('      "title": "Replace fillers with pauses",')
    prompt_parts.append('      "explanation": "Detailed actionable advice",')
    prompt_parts.append('      "transcript_excerpt": "Optional excerpt showing the issue",')
    prompt_parts.append('      "technique": "Box breathing before speaking"')
    prompt_parts.append("    }")
    prompt_parts.append("  ],")
    prompt_parts.append('  "framework_analysis": {')
    prompt_parts.append(f'    "framework_used": "{framework.value}",')
    prompt_parts.append('    "completion": true,')
    prompt_parts.append('    "missing_components": []')
    prompt_parts.append("  },")
    prompt_parts.append('  "filler_count": 12,')
    prompt_parts.append('  "filler_rate": 4.5,')
    prompt_parts.append('  "filler_percentage": 3.2,')
    prompt_parts.append('  "word_count": 375,')
    prompt_parts.append('  "duration_seconds": 160,')
    prompt_parts.append('  "speaking_rate_wpm": 140')

    # Add phase-specific metrics
    if phase_config.phase in [Phase.PHASE_2, Phase.PHASE_3]:
        prompt_parts.append(',  "maze_count": 2,')
        prompt_parts.append('  "maze_rate": 0.75,')
        prompt_parts.append('  "hedging_count": 3,')
        prompt_parts.append('  "hedging_rate": 1.12')

    if phase_config.phase == Phase.PHASE_3:
        prompt_parts.append(',  "pause_quality_score": 85')

    prompt_parts.append("}")
    prompt_parts.append("")

    prompt_parts.append("Analyze the transcript and return ONLY the JSON object. No markdown formatting.")

    return "\n".join(prompt_parts)


def get_prompt_version() -> str:
    """Get current prompt version for tracking calibration."""
    return "v2.0"  # Updated after calibration (Ticket 1.4.3)
