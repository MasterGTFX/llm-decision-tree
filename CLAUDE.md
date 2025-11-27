# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project implements a **pre-generation/static tree-building algorithm** for LLM-powered decision trees. The system constructs complete decision trees upfront using LLM calls, then serves them as fast, pre-computed expert systems.

## Development Environment

- **Python Version:** 3.12
- **Virtual Environment:** `.venv/`
- **Formatter:** Black (configured in IDE)
- **IDE:** PyCharm/IntelliJ IDEA

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt  # when created
```

## Architecture Concept

### Tree Building Algorithm
1. **Input:** User provides initial domain/symptom (e.g., "chest pain")
2. **Root Generation:** LLM generates first discriminating question with answer-to-filter mappings
3. **Recursive Expansion:** For each answer branch with multiple possibilities, recursively generate sub-questions
4. **Base Case:** Stop when diagnosis list contains single item (leaf node)

### Tree Structure
- **Root Node:** Most general discriminating question
- **Internal Nodes:** Questions that narrow down possibilities, each with answer options mapping to filtered subsets
- **Leaf Nodes:** Final conclusions (single diagnosis/outcome)

### Example: Medical Diagnosis Tree

**Initial User Input:** "chest pain"

**Generated Decision Tree:**

```
ROOT: "What is the primary characteristic of the pain?"
├─ "Sharp and stabbing" -> [Pneumothorax, Pulmonary Embolism, Pleurisy]
│   └─ "Is the pain worse when breathing deeply?"
│       ├─ "Yes, significantly worse" -> [Pleurisy, Pneumothorax]
│       │   └─ "Did symptoms start suddenly?"
│       │       ├─ "Yes, very sudden onset" -> [Pneumothorax] ✓ LEAF
│       │       └─ "Gradual onset" -> [Pleurisy] ✓ LEAF
│       └─ "No change with breathing" -> [Pulmonary Embolism] ✓ LEAF
│
├─ "Pressure or squeezing, spreading to arm/jaw" -> [Myocardial Infarction, Angina Pectoris]
│   └─ "How long does the pain last?"
│       ├─ "Less than 20 minutes, relieved by rest" -> [Angina Pectoris] ✓ LEAF
│       └─ "More than 20 minutes, not relieved" -> [Myocardial Infarction] ✓ LEAF
│
└─ "Burning sensation, worse after eating" -> [GERD, Esophagitis]
    └─ "Does antacid provide relief?"
        ├─ "Yes, quick relief" -> [GERD] ✓ LEAF
        └─ "No or minimal relief" -> [Esophagitis] ✓ LEAF
```

**Tree Construction Process:**
1. LLM receives "chest pain" and possible diagnoses
2. Generates root question that best discriminates between conditions
3. For each answer path with multiple diagnoses, recursively generates next discriminating question
4. Stops when only one diagnosis remains (leaf node)

### Core Design Patterns

**Offline Compilation Model:** LLM acts as "compiler" building expert system, not runtime brain
- Tree validated before user interaction
- User experience is fast graph traversal (clicking options)
- Full logic path is predetermined and reviewable

**Node Data Structure (Conceptual):**
```python
{
    "question": str,
    "answers": [
        {
            "answer_text": str,
            "potential_outcomes": [str],  # <-- Best general-purpose choice
        }
    ]
}
```


## Key Considerations

### Scalability Challenges
- Combinatorial explosion of branches for large domains
- Consider pruning strategies or depth limits
- May need caching/memoization for similar subproblems

### Robustness Features to Implement
- Handle "I don't know" responses
- Validation layer for tree completeness
- Error detection for missing branches or circular logic