"""
llm_workflow.py
---------------
LLM-powered workflow parsing and subtask extraction for orchestrator.
"""
import os
import openai  # You can swap for other LLM providers
from typing import List, Dict, Any

# Set your OpenAI API key (or use environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-...")

SYSTEM_PROMPT = """
You are an expert workflow orchestrator. Given a user's natural language request, output a structured JSON object with:
- subtasks: list of atomic steps
- dependencies: DAG mapping (subtask: [dependencies])
- rationale: reasoning for each subtask and dependency
"""

def parse_workflow_with_llm(user_input: str) -> Dict[str, Any]:
    """
    Use LLM to parse user intent and generate workflow subtasks, dependencies, and rationale.
    """
    prompt = f"""
{SYSTEM_PROMPT}
User request: {user_input}
Output JSON:
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ],
        temperature=0.2,
        max_tokens=512
    )
    # Extract JSON from LLM response
    import json
    try:
        content = response["choices"][0]["message"]["content"]
        workflow = json.loads(content)
    except Exception as e:
        workflow = {"error": f"Failed to parse LLM output: {str(e)}", "raw": content}
    return workflow

# Example usage:
# user_input = "Onboard a new product for my e-commerce store."
# workflow = parse_workflow_with_llm(user_input)
# print(workflow)
