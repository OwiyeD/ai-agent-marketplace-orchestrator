from celery_app import celery_app
from database import SessionLocal, Orchestration, Agent
from sqlalchemy.orm import Session
import httpx
import json
from typing import List, Dict, Any

# V0: Hardcoded workflow definitions
WORKFLOW_DEFINITIONS = {
    "ecommerce_onboarding": {
        "subtasks": ["extract", "copywrite", "seo"],
        "dependencies": {
            "extract": [],
            "copywrite": ["extract"],
            "seo": ["extract"]
        }
    }
}

@celery_app.task
def orchestrate_workflow(orchestration_id: str):
    """Main orchestration task - orchestrates the 8 steps"""
    db = SessionLocal()
    try:
        # Step 1: Parse user intent
        orchestration = db.query(Orchestration).filter(Orchestration.id == orchestration_id).first()
        if not orchestration:
            return {"error": "Orchestration not found"}
        
        # Update status
        orchestration.current_status = "EXECUTING"
        db.commit()
        
        # Step 2: Decompose into subtasks
        subtasks = parse_intent(orchestration.user_input)
        orchestration.subtasks = subtasks
        orchestration.workflow_type = determine_workflow_type(subtasks)
        db.commit()
        
        # Step 3: Discover and match agents
        agent_mappings = discover_agents(subtasks, db)
        
        # Step 4: Select optimal agents
        selected_agents = select_optimal_agents(agent_mappings, db)
        
        # Step 5: Plan workflow dependencies
        workflow_plan = plan_workflow_dependencies(subtasks, orchestration.workflow_type)
        
        # Step 6: Execute subtasks
        results = execute_subtasks(workflow_plan, selected_agents)
        
        # Step 7: Handle failures and retries
        results = handle_failures_and_retries(results, selected_agents, db)
        
        # Step 8: Aggregate and format results
        final_results = aggregate_results(results)
        
        # Update orchestration with results
        orchestration.results = final_results
        orchestration.current_status = "COMPLETED"
        db.commit()
        
        return final_results
        
    except Exception as e:
        orchestration.current_status = "FAILED"
        db.commit()
        return {"error": str(e)}
    finally:
        db.close()

def parse_intent(user_input: str) -> List[str]:
    """Step 1: Parse user intent and decompose into subtasks"""
    # V0: Simple keyword-based parsing
    input_lower = user_input.lower()
    
    if "product" in input_lower and ("onboard" in input_lower or "create" in input_lower):
        return ["extract", "copywrite", "seo"]
    elif "research" in input_lower:
        return ["web_search", "data_analysis"]
    else:
        return ["general_assistant"]
    
    return ["extract", "copywrite", "seo"]  # Default for demo

def determine_workflow_type(subtasks: List[str]) -> str:
    """Determine the workflow type based on subtasks"""
    if "extract" in subtasks and "copywrite" in subtasks and "seo" in subtasks:
        return "ecommerce_onboarding"
    elif "web_search" in subtasks:
        return "research"
    else:
        return "general"

def discover_agents(subtasks: List[str], db: Session) -> Dict[str, List[Agent]]:
    """Step 3: Discover agents for each subtask"""
    agent_mappings = {}
    
    for subtask in subtasks:
        # V0: Simple tag-based filtering using PostgreSQL
        agents = db.query(Agent).filter(
            Agent.is_active == "active",
            Agent.capabilities.contains([subtask])
        ).all()
        agent_mappings[subtask] = agents
    
    return agent_mappings

def select_optimal_agents(agent_mappings: Dict[str, List[Agent]], db: Session) -> Dict[str, Agent]:
    """Step 4: Select optimal agents (V0: simple hardcoded scoring)"""
    selected_agents = {}
    
    for subtask, agents in agent_mappings.items():
        if agents:
            # V0: Pick the first available agent (all have same hardcoded score)
            selected_agents[subtask] = agents[0]
        else:
            # Fallback to default agents if none found
            default_agent = db.query(Agent).filter(Agent.capabilities.contains([subtask])).first()
            if default_agent:
                selected_agents[subtask] = default_agent
    
    return selected_agents

def plan_workflow_dependencies(subtasks: List[str], workflow_type: str) -> Dict[str, Any]:
    """Step 5: Plan workflow dependencies (V0: hardcoded DAG)"""
    if workflow_type == "ecommerce_onboarding":
        return {
            "extract": {"dependencies": [], "order": 1},
            "copywrite": {"dependencies": ["extract"], "order": 2},
            "seo": {"dependencies": ["extract"], "order": 2}
        }
    else:
        # Default: parallel execution
        return {subtask: {"dependencies": [], "order": 1} for subtask in subtasks}

def execute_subtasks(workflow_plan: Dict[str, Any], selected_agents: Dict[str, Agent]) -> Dict[str, Any]:
    """Step 6: Execute subtasks according to workflow plan"""
    results = {}
    
    # V0: Simple sequential execution (can be enhanced with parallel execution)
    for subtask, plan in sorted(workflow_plan.items(), key=lambda x: x[1]["order"]):
        if subtask in selected_agents:
            agent = selected_agents[subtask]
            try:
                # Execute agent
                result = execute_agent(agent, subtask)
                results[subtask] = {"status": "success", "result": result, "agent_id": agent.id}
            except Exception as e:
                results[subtask] = {"status": "failed", "error": str(e), "agent_id": agent.id}
    
    return results

def execute_agent(agent: Agent, subtask: str) -> Any:
    """Execute a single agent"""
    # V0: Mock agent execution (replace with actual HTTP calls)
    if subtask == "extract":
        return {"extracted_data": "Sample product data", "confidence": 0.95}
    elif subtask == "copywrite":
        return {"copy": "Compelling product description", "tone": "professional"}
    elif subtask == "seo":
        return {"keywords": ["product", "quality", "value"], "meta_description": "SEO optimized"}
    else:
        return {"response": f"Processed {subtask} successfully"}

def handle_failures_and_retries(results: Dict[str, Any], selected_agents: Dict[str, Agent], db: Session) -> Dict[str, Any]:
    """Step 7: Handle failures and retries (V0: simple try/except)"""
    for subtask, result in results.items():
        if result["status"] == "failed":
            # V0: Simple retry with fallback agent
            try:
                fallback_agent = find_fallback_agent(subtask, selected_agents[subtask].id, db)
                if fallback_agent:
                    retry_result = execute_agent(fallback_agent, subtask)
                    results[subtask] = {"status": "success", "result": retry_result, "agent_id": fallback_agent.id}
            except Exception as e:
                results[subtask]["retry_error"] = str(e)
    
    return results

def find_fallback_agent(subtask: str, current_agent_id: str, db: Session) -> Agent:
    """Find a fallback agent for a subtask"""
    fallback_agents = db.query(Agent).filter(
        Agent.is_active == "active",
        Agent.capabilities.contains([subtask]),
        Agent.id != current_agent_id
    ).all()
    
    return fallback_agents[0] if fallback_agents else None

def aggregate_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Step 8: Aggregate and format results"""
    successful_results = {k: v for k, v in results.items() if v["status"] == "success"}
    failed_results = {k: v for k, v in results.items() if v["status"] == "failed"}
    
    return {
        "summary": {
            "total_subtasks": len(results),
            "successful": len(successful_results),
            "failed": len(failed_results)
        },
        "results": successful_results,
        "errors": failed_results,
        "aggregated_output": combine_outputs(successful_results)
    }

def combine_outputs(successful_results: Dict[str, Any]) -> str:
    """Combine outputs from successful subtasks"""
    if not successful_results:
        return "No successful results to combine"
    
    # V0: Simple concatenation (can be enhanced with AI summarization)
    combined = []
    for subtask, result in successful_results.items():
        if "result" in result:
            combined.append(f"{subtask}: {str(result['result'])}")
    
    return "\n".join(combined)



