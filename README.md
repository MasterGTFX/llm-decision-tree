# LLM Decision Tree Generator

This project generates decision trees using an LLM (Large Language Model) to help diagnose issues or guide decision-making processes. It supports both **Recursive** (full tree generation) and **Interactive** (step-by-step) modes.

## Features

-   **Recursive Mode:** Generates the entire decision tree upfront.
-   **Interactive Mode:** Builds the tree step-by-step based on user choices.
-   **Predefined Roles:** Comes with built-in experts like Medical Diagnosis, Relationship Advisor, Tech Support, etc.
-   **Web Interface:** A modern, responsive UI to visualize and interact with the trees.
-   **CLI Support:** Run the generator directly from your terminal.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration:**
    Create a `.env` file in the root directory with your LLM API details:
    ```env
    OPENAI_BASE_URL=your_base_url
    OPENAI_API_KEY=your_api_key
    LLM_MODEL=gpt-4o  # or your preferred model
    ```

## Usage

### Option 1: Web Interface (Recommended)

Run the FastAPI server to use the graphical interface:

```bash
uvicorn app:app --reload
```

Then open your browser and navigate to:
[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

### Option 2: Command Line Interface (CLI)

Run the script directly in your terminal:

```bash
python main.py
```

Follow the on-screen prompts to select the generation mode (Recursive or Interactive).

## Project Structure

-   `app.py`: FastAPI backend server.
-   `main.py`: CLI entry point.
-   `tree.py`: Core logic for decision tree generation.
-   `config.py`: Configuration settings and predefined roles.
-   `static/`: Frontend files (HTML, CSS, JS).
