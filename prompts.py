"""Prompt templates for LLM decision tree generation."""

# System prompts
INITIAL_SYSTEM_PROMPT = """# Role
You are {role}. Your task is to create the starting point for a decision tree.

# Your Task
Generate a response with this exact structure:
```json
{{
    "question": "The most useful initial question to ask",
    "answers": [
        {{"answer_text": "Answer option 1", "potential_outcomes": ["Outcome A", "Outcome B"]}},
        {{"answer_text": "Answer option 2", "potential_outcomes": ["Outcome C", "Outcome D"]}}
    ]
}}
```

# Requirements
- List ALL logically possible outcomes for this domain
- Create distinct answer options that are mutually exclusive
- Ensure answer options cover all possible scenarios
- Outcomes should be specific and actionable
- The question should be the most useful starting point for differentiation
"""

DISCRIMINATING_SYSTEM_PROMPT = """# Role
You are {role}. Your task is to create the next branching question for a decision tree.

# Task
Generate a response with this exact structure:
```json
{{
    "question": "The question that best differentiates these outcomes",
    "answers": [
        {{"answer_text": "Answer option 1", "potential_outcomes": ["Outcome A", "Outcome C"]}},
        {{"answer_text": "Answer option 2", "potential_outcomes": ["Outcome B"]}}
    ]
}}
```

# Requirements
- Create exactly ONE question that best distinguishes between the possible outcomes
- Answers must be mutually exclusive and collectively exhaustive
- Each answer's outcomes list must be a non-empty subset of the original outcomes
- The question should maximally reduce uncertainty in one step
"""

# User prompts
INITIAL_USER_PROMPT = """
Initial user query: {query}
"""

DISCRIMINATING_USER_PROMPT = """
# Decision Path
Initial query: {query}

{history}

# Current Possible Outcomes
{outcomes}
"""