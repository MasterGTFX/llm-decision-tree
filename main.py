"""
LLM Decision Tree Generator - Proof of Concept

Pre-generates a complete decision tree using LLM calls.
"""

from openai import OpenAI
from config import BASE_URL, API_KEY, LLM_MODEL
from tree import DecisionTreeGenerator

def main():
    # Example: Medical diagnosis for chest pain
    role = "Technical Troubleshooter"
    query = "My computer screen keeps flickering."

    print(f"Building decision tree for: {query}")
    print(f"Role: {role}")
    print("-" * 50)

    # Initialize OpenAI client
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    
    # Initialize Generator
    generator = DecisionTreeGenerator(client, LLM_MODEL)

    # Ask user for mode
    print("Select generation mode:")
    print("1. Recursive (Generate full tree automatically)")
    print("2. Interactive (Step-by-step generation)")
    
    while True:
        mode = input("Enter choice (1 or 2): ").strip()
        if mode in ["1", "2"]:
            break
        print("Invalid choice. Please enter 1 or 2.")

    if mode == "1":
        # Recursive Mode
        print("\nStarting Recursive Generation...")
        root = generator.generate(role, query, recursive=True)
        print("-" * 50)
        print("Generated Decision Tree:")
        print("=" * 50)
        print(root)
        
    else:
        # Interactive Mode
        print("\nStarting Interactive Generation...")
        root = generator.generate(role, query, recursive=False)
        current_node = root
        
        while True:
            print("\n" + "=" * 50)
            print(f"Question: {current_node.question}")
            print("-" * 50)
            
            for i, answer in enumerate(current_node.answers):
                print(f"{i + 1}. {answer.answer_text}")
                print(f"   (Potential outcomes: {', '.join(answer.potential_outcomes)})")
            
            print("0. Stop and show tree")
            
            while True:
                try:
                    choice = int(input(f"\nSelect an answer (1-{len(current_node.answers)}) or 0 to stop: "))
                    if 0 <= choice <= len(current_node.answers):
                        break
                    print("Invalid choice.")
                except ValueError:
                    print("Please enter a number.")
            
            if choice == 0:
                break
                
            selected_answer = current_node.answers[choice - 1]
            
            if selected_answer.is_leaf:
                print(f"\nSelected answer is a leaf node. Reached end of this branch.")
                break
                
            print(f"\nGenerating next question for answer: {selected_answer.answer_text}...")
            next_node = generator.expand_node(role, query, selected_answer)
            
            if next_node:
                current_node = next_node
            else:
                print("No further questions generated.")
                break

        print("\n" + "-" * 50)
        print("Final Generated Tree (Partial):")
        print("=" * 50)
        print(root)

if __name__ == "__main__":
    main()