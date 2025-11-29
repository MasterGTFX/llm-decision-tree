from typing import List, Optional, Union, Callable, Dict, Any
import uuid
import json
import time
import os
import re
from datetime import datetime
from pydantic import BaseModel
from openai import OpenAI
from config import MAX_DEPTH
from prompts import (
    INITIAL_SYSTEM_PROMPT,
    INITIAL_USER_PROMPT,
    DISCRIMINATING_SYSTEM_PROMPT,
    DISCRIMINATING_USER_PROMPT,
)

# Structured output schemas
class AnswerSchema(BaseModel):
    answer_text: str
    potential_outcomes: list[str]

class QuestionSchema(BaseModel):
    question: str
    answers: list[AnswerSchema]

class DecisionTreeGenerator:
    """Generates a decision tree using an LLM."""

    def __init__(self, client: OpenAI, llm_model: str, callback: Optional[Callable[[dict], None]] = None):
        self.client = client
        self.llm_model = llm_model
        self.callback = callback

    def generate(self, role: str, query: str, recursive: bool = True) -> "QuestionNode":
        """
        Main entry point to generate the decision tree.
        
        Args:
            role: The role of the expert.
            query: The initial user query.
            recursive: If True, generates the full tree recursively. 
                       If False, generates only the root question.
        """
        print(f"Fetching initial question for: {query}")
        initial_data, log_entry = self._get_initial_question(role, query)
        
        root = QuestionNode(initial_data.question)
        root.logs.append(log_entry) # Store initial log

        for answer in initial_data.answers:
            root.add_answer(answer.answer_text, answer.potential_outcomes)
            
        if self.callback:
            self.callback({
                "type": "root",
                "node": self._serialize_node(root)
            })
        
        # Save initial state
        self.save_tree_to_json(root, role, query)

        if recursive:
            print("Building decision tree recursively...")
            for answer_node in root.answers:
                self._build_recursive(role, query, answer_node, root)
            
        return root

    def _get_initial_question(self, role: str, query: str) -> tuple[QuestionSchema, Dict[str, Any]]:
        """Get initial question with answers and outcomes."""
        system_prompt = INITIAL_SYSTEM_PROMPT.format(role=role)
        user_prompt = INITIAL_USER_PROMPT.format(query=query)

        start_time = time.time()
        response = self.client.beta.chat.completions.parse(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=QuestionSchema,
        )
        duration = time.time() - start_time
        response_json = response.choices[0].message.parsed
        print(f"Root Question: {response_json.question}")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "initial_question",
            "duration_seconds": duration,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response": response_json.model_dump()
        }
        return response_json, log_entry

    def _get_discriminating_question(
        self, role: str, query: str, history: str, outcomes: list[str]
    ) -> tuple[QuestionSchema, Dict[str, Any]]:
        """Get the most discriminating question for current branch."""
        system_prompt = DISCRIMINATING_SYSTEM_PROMPT.format(role=role)
        outcomes_text = "\n".join(f"- {outcome}" for outcome in outcomes)
        user_prompt = DISCRIMINATING_USER_PROMPT.format(
            query=query, history=history, outcomes=outcomes_text
        )

        start_time = time.time()
        response = self.client.beta.chat.completions.parse(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=QuestionSchema,
        )
        duration = time.time() - start_time
        return response.choices[0].message.parsed, {
            "timestamp": datetime.now().isoformat(),
            "type": "discriminating_question",
            "duration_seconds": duration,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response": response.choices[0].message.parsed.model_dump()
        }

    def expand_node(self, role: str, query: str, answer_node: "AnswerNode") -> Optional["QuestionNode"]:
        """
        Expand a single answer node by generating the next question.
        Returns the new QuestionNode if created, or None if it's a leaf.
        """
        if answer_node.is_leaf:
            return None

        # Get next discriminating question
        history = answer_node.get_history_str()
        question_data, log_entry = self._get_discriminating_question(
            role, query, history, answer_node.potential_outcomes
        )
        
        # Find root to append logs
        root = answer_node.root
        if hasattr(root, 'logs'):
            root.logs.append(log_entry)
        
        print(f"  Extending branch: {answer_node.answer_text[:30]}... -> {question_data.question}")

        # Create question node
        question_node = QuestionNode(question_data.question)
        answer_node.set_child(question_node)

        # Add answers
        for answer in question_data.answers:
            question_node.add_answer(answer.answer_text, answer.potential_outcomes)
            
        if self.callback:
            self.callback({
                "type": "expand",
                "parent_answer_id": answer_node.id,
                "node": self._serialize_node(question_node)
            })
            
        # Save updated tree
        self.save_tree_to_json(root, role, query)

        return question_node

    def _build_recursive(self, role: str, query: str, answer_node: "AnswerNode", root: "QuestionNode") -> None:
        """Recursively build tree from an answer node."""
        question_node = self.expand_node(role, query, answer_node)
        
        if question_node:
            # Recursively build subtrees
            for child_answer in question_node.answers:
                self._build_recursive(role, query, child_answer, root)

    def _serialize_node(self, node: "QuestionNode") -> dict:
        """Helper to serialize a node for the callback."""
        return {
            "id": node.id,
            "question": node.question,
            "answers": [
                {
                    "id": ans.id,
                    "text": ans.answer_text,
                    "outcomes": ans.potential_outcomes
                }
                for ans in node.answers
            ]
        }

    def save_tree_to_json(self, root: "TreeNode", role: str, query: str) -> None:
        """Saves the tree and logs to a JSON file."""
        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Sanitize filename
        safe_role = re.sub(r'[^a-zA-Z0-9]', '_', role[:20])
        safe_query = re.sub(r'[^a-zA-Z0-9]', '_', query[:30])
        timestamp = datetime.fromtimestamp(root.created_at).strftime('%Y%m%d_%H%M%S')
        filename = f"{logs_dir}/{timestamp}_{safe_role}_{safe_query}.json"

        data = {
            "meta": {
                "role": role,
                "query": query,
                "model": self.llm_model,
                "created_at": datetime.fromtimestamp(root.created_at).isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            "tree": root.to_dict(),
            "logs": root.logs
        }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            # print(f"Tree saved to {filename}") # Optional: reduce noise
        except Exception as e:
            print(f"Error saving tree to JSON: {e}")


class TreeNode:
    """
    Base class for all nodes in the decision tree.
    Tracks parent, depth, and provides utility for path traversal.
    """

    def __init__(self, parent: Optional["TreeNode"] = None):
        self.parent = parent
        self.id = str(uuid.uuid4())
        self.created_at = time.time()
        self.logs: List[Dict[str, Any]] = [] # Only used by root, but kept here for simplicity

    @property
    def depth(self) -> int:
        """Return the depth of the node in the tree (Root is 0)."""
        if self.parent is None:
            return 0
        return self.parent.depth + 1

    @property
    def is_root(self) -> bool:
        """Check if this node is the root of the tree."""
        return self.parent is None

    @property
    def root(self) -> "TreeNode":
        """Traverse up to find the root of the tree."""
        node = self
        while node.parent:
            node = node.parent
        return node

    def get_path(self) -> List["TreeNode"]:
        """Get the path from root to this node."""
        path = []
        node = self
        while node:
            path.append(node)
            node = node.parent
        return list(reversed(path))

    def find_node_by_id(self, target_id: str) -> Optional["TreeNode"]:
        """Recursively find a node by ID in this subtree."""
        if hasattr(self, 'id') and self.id == target_id:
            return self
        
        # Check children
        if isinstance(self, QuestionNode):
            for answer in self.answers:
                found = answer.find_node_by_id(target_id)
                if found:
                    return found
        elif isinstance(self, AnswerNode):
            if self.child:
                found = self.child.find_node_by_id(target_id)
                if found:
                    return found
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "depth": self.depth
        }

    def __str__(self) -> str:
        """
        Return a string representation of the tree starting from this node.
        Uses recursion to format the entire subtree.
        """
        return self._get_tree_string()

    def _get_tree_string(self, level: int = 0) -> str:
        """Helper to recursively build the tree string."""
        raise NotImplementedError("Subclasses must implement _get_tree_string")

    def get_history_str(self, indent: str = "\t") -> str:
        """
        Get formatted history string for LLM context.
        Reconstructs the conversation path from root to this node.
        """
        path = self.get_path()
        lines = []
        current_indent = 0
        
        for node in path:
            if isinstance(node, QuestionNode):
                lines.append(f"{indent * current_indent}Question: {node.question}")
            elif isinstance(node, AnswerNode):
                lines.append(f"{indent * current_indent}Answer: {node.answer_text}")
                current_indent += 1
        return "\n".join(lines)


class QuestionNode(TreeNode):
    """
    Represents a question node in the decision tree.
    Contains a question and a list of possible answers (branches).
    """

    def __init__(self, question: str, parent: Optional[TreeNode] = None):
        super().__init__(parent)
        self.question = question
        self.answers: List["AnswerNode"] = []

    def add_answer(self, answer_text: str, potential_outcomes: List[str]) -> "AnswerNode":
        """Add an answer branch to this question."""
        answer_node = AnswerNode(answer_text, potential_outcomes, parent=self)
        self.answers.append(answer_node)
        return answer_node

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "type": "question",
            "question": self.question,
            "answers": [ans.to_dict() for ans in self.answers]
        })
        return data

    def _get_tree_string(self, level: int = 0) -> str:
        indent = "\t" * level
        result = f"{indent}Question: {self.question}\n"
        for answer in self.answers:
            result += answer._get_tree_string(level + 1)
        return result

    def __repr__(self) -> str:
        return f"<QuestionNode depth={self.depth} question='{self.question}' branches={len(self.answers)}>"


class AnswerNode(TreeNode):
    """
    Represents an answer node in the decision tree.
    Contains the answer text, potential outcomes, and a child node (next question or None).
    """

    def __init__(self, answer_text: str, potential_outcomes: List[str], parent: Optional[TreeNode] = None):
        super().__init__(parent)
        self.answer_text = answer_text
        self.potential_outcomes = potential_outcomes
        self.child: Optional[QuestionNode] = None

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node (single outcome or max depth reached)."""
        # We can also consider it a leaf if we hit MAX_DEPTH, though logic might vary.
        return len(self.potential_outcomes) <= 1

    def set_child(self, question_node: "QuestionNode") -> None:
        """Set the child question node."""
        self.child = question_node
        question_node.parent = self

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "type": "answer",
            "answer_text": self.answer_text,
            "potential_outcomes": self.potential_outcomes,
            "child": self.child.to_dict() if self.child else None
        })
        return data

    def _get_tree_string(self, level: int = 0) -> str:
        indent = "\t" * level
        outcomes_str = ", ".join(self.potential_outcomes)
        result = f"{indent}Answer: \"{self.answer_text}\" -> [{outcomes_str}]"
        
        if self.depth >= MAX_DEPTH:
             result += " [MAX DEPTH REACHED]"
        
        result += "\n"
        
        if self.child:
            result += self.child._get_tree_string(level + 1)
        return result

    def __repr__(self) -> str:
        return f"<AnswerNode depth={self.depth} answer='{self.answer_text}' outcomes={len(self.potential_outcomes)}>"
