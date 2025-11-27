The LLM constructs the *entire* decision tree upfront, before the user even starts answering questions. This is fundamentally different from the dynamic, step-by-step building we discussed earlier.

**How it Works:**

1.  **Start:** User provides the initial symptom ("chest pain").
2.  **LLM's First Task:** Generate the root node.
    *   **Question:** "What is the primary characteristic of the pain?"
    *   **Answers & Filters:**
        *   "Sharp and localized" -> [Muscle Strain, Pneumonia]
        *   "Pressure, spreading" -> [Heart Attack, Angina]
        *   "Burning sensation" -> [GERD, Anxiety]
3.  **Recursive Tree Building:** For each child node (defined by an answer and its filtered diagnosis list), if the list has more than one diagnosis, the LLM is prompted again in a new context to generate the *most discriminating question* for *that specific subset* of diagnoses.
4.  **Base Case:** The recursion stops when a node's diagnosis list contains only one item. That node becomes a leaf node with the conclusion.

- **Root:** The first, most general question.
- **Internal Nodes:** Questions that narrow down the possibilities.
- **Leaf Nodes:** The final conclusions (single diagnosis).

This is a very valid and often more robust design than a dynamic one. It shifts the LLM's role from a "runtime brain" to an "offline compiler" that builds a expert system.
