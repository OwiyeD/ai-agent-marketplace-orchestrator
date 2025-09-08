from celery import shared_task, group, chord
from celery_app import celery_app
from database import SessionLocal, Orchestration, Agent
from sqlalchemy.orm import Session
import json
import logging
import redis
import hashlib
import pickle
from typing import Dict, Any, List, Optional
from sandbox_manager import DockerSandboxManager
from llm_workflow import parse_workflow_with_llm
from vector_store import select_agents_for_intent
from prometheus_client import Counter, Histogram, Gauge
import time

# Prometheus Metrics
TASK_COUNTER = Counter('orchestrator_tasks_total', 'Total orchestration tasks', ['status'])
TASK_DURATION = Histogram('orchestrator_task_duration_seconds', 'Task execution duration')
ACTIVE_ORCHESTRATIONS = Gauge('orchestrator_active_orchestrations', 'Currently running orchestrations')
AGENT_PERFORMANCE = Histogram('agent_execution_duration_seconds', 'Agent execution time', ['agent_id', 'status'])

# Redis Cache Setup
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=False)
CACHE_TTL = 3600  # 1 hour

logger = logging.getLogger("orchestrator")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --------------------------
# CACHING UTILITIES
# --------------------------
def get_cache_key(prefix: str, data: str) -> str:
    """Generate a consistent cache key"""
    return f"{prefix}:{hashlib.md5(data.encode()).hexdigest()}"

def cache_workflow(user_input: str, workflow: Dict[str, Any]) -> None:
    """Cache LLM-parsed workflow"""
    cache_key = get_cache_key("workflow", user_input)
    redis_client.setex(cache_key, CACHE_TTL, pickle.dumps(workflow))

def get_cached_workflow(user_input: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached workflow"""
    cache_key = get_cache_key("workflow", user_input)
    cached = redis_client.get(cache_key)
    return pickle.loads(cached) if cached else None

def cache_agent_embeddings(subtask: str, agents: List[Dict[str, Any]]) -> None:
    """Cache agent selection results"""
    cache_key = get_cache_key("agents", subtask)
    redis_client.setex(cache_key, CACHE_TTL, pickle.dumps(agents))

def get_cached_agents(subtask: str) -> Optional[List[Dict[str, Any]]]:
    """Retrieve cached agent selections"""
    cache_key = get_cache_key("agents", subtask)
    cached = redis_client.get(cache_key)
    return pickle.loads(cached) if cached else None

# --------------------------
# ASYNC DAG EXECUTION WITH CELERY
# --------------------------
def build_execution_groups(workflow_plan: Dict[str, Any], selected_agents: Dict[str, Agent]) -> List[List[str]]:
    """Build execution groups for parallel processing"""
    levels = []
    completed = set()
    
    while len(completed) < len(workflow_plan):
        current_level = []
        for subtask, plan in workflow_plan.items():
            if subtask not in completed and all(dep in completed for dep in plan.get("dependencies", [])):
                current_level.append(subtask)
        
        if not current_level:
            # Break circular dependencies
            remaining = set(workflow_plan.keys()) - completed
            current_level = list(remaining)
        
        levels.append(current_level)
        completed.update(current_level)
    
    return levels

@shared_task
def execute_subtask_group(subtask_group: List[str], selected_agents: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a group of parallel subtasks"""
    results = {}
    
    # Create Celery group for parallel execution
    job = group(
        run_agent_in_sandbox_task.s(selected_agents[subtask], subtask, 3) 
        for subtask in subtask_group
    )
    
    group_result = job.apply_async()
    group_results = group_result.get()
    
    for i, subtask in enumerate(subtask_group):
        results[subtask] = group_results[i]
    
    return results

@shared_task
def run_agent_in_sandbox_task(agent: Dict[str, Any], subtask: str, max_retries: int = 1) -> Dict[str, Any]:
    """Celery task wrapper for agent execution with metrics"""
    start_time = time.time()
    
    try:
        result = run_agent_in_sandbox(agent, subtask, max_retries)
        
        # Record metrics
        duration = time.time() - start_time
        AGENT_PERFORMANCE.labels(
            agent_id=agent.get('id', 'unknown'),
            status=result.get('status', 'unknown')
        ).observe(duration)
        
        return result
    except Exception as e:
        AGENT_PERFORMANCE.labels(
            agent_id=agent.get('id', 'unknown'),
            status='error'
        ).observe(time.time() - start_time)
        raise

# --------------------------
# MAIN ORCHESTRATION WITH OPTIMIZATIONS
# --------------------------
@celery_app.task
def orchestrate_workflow(orchestration_id: str):
    """Optimized orchestration with caching, async execution, and monitoring"""
    ACTIVE_ORCHESTRATIONS.inc()
    start_time = time.time()
    
    db = SessionLocal()
    try:
        orchestration = db.query(Orchestration).filter(Orchestration.id == orchestration_id).first()
        if not orchestration:
            TASK_COUNTER.labels(status='not_found').inc()
            return {"error": "Orchestration not found"}

        orchestration.current_status = "EXECUTING"
        db.commit()
        logger.info(f"Starting orchestration {orchestration_id}")

        # STEP 1: Parse Workflow with Caching
        cached_workflow = get_cached_workflow(orchestration.user_input)
        if cached_workflow:
            logger.info(f"Using cached workflow for orchestration {orchestration_id}")
            workflow = cached_workflow
        else:
            workflow = parse_workflow_with_llm(orchestration.user_input)
            cache_workflow(orchestration.user_input, workflow)
        
        subtasks = workflow.get("subtasks", [])
        workflow_plan = workflow.get("dependencies", {})
        orchestration.subtasks = subtasks
        db.commit()

        # STEP 2: Semantic Agent Selection with Caching
        selected_agents = {}
        for subtask in subtasks:
            cached_agents = get_cached_agents(subtask)
            if cached_agents:
                selected_agents[subtask] = cached_agents[0]
                logger.info(f"Using cached agent for subtask '{subtask}'")
            else:
                candidates = select_agents_for_intent(subtask, top_k=3)
                if candidates:
                    selected_agents[subtask] = candidates[0]
                    cache_agent_embeddings(subtask, candidates)
                    logger.info(f"Selected agent {candidates[0]['name']} for subtask '{subtask}'")

        # STEP 3: Async DAG Execution
        results = execute_subtasks_async(workflow_plan, selected_agents)

        # STEP 4: Failover & Retry
        results = handle_failures_and_retries(results, selected_agents, db)

        # STEP 5: Aggregate Results
        final_results = aggregate_results(results)
        orchestration.results = final_results
        orchestration.current_status = "COMPLETED"
        db.commit()

        # Record success metrics
        TASK_COUNTER.labels(status='success').inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        logger.info(f"Orchestration {orchestration_id} completed successfully")
        return final_results

    except Exception as e:
        orchestration.current_status = "FAILED"
        db.commit()
        
        # Record failure metrics
        TASK_COUNTER.labels(status='failed').inc()
        TASK_DURATION.observe(time.time() - start_time)
        
        logger.error(f"Orchestration {orchestration_id} failed: {e}")
        return {"error": str(e)}
    finally:
        ACTIVE_ORCHESTRATIONS.dec()
        db.close()

def execute_subtasks_async(workflow_plan: Dict[str, Any], selected_agents: Dict[str, Agent]) -> Dict[str, Any]:
    """Execute subtasks using Celery groups for parallelization"""
    execution_levels = build_execution_groups(workflow_plan, selected_agents)
    all_results = {}
    
    for level in execution_levels:
        logger.info(f"Executing parallel group: {level}")
        
        # Execute current level in parallel using Celery group
        job = group(
            run_agent_in_sandbox_task.s(selected_agents[subtask], subtask, 3)
            for subtask in level if subtask in selected_agents
        )
        
        group_result = job.apply_async()
        level_results = group_result.get()
        
        # Map results back to subtasks
        for i, subtask in enumerate(level):
            if subtask in selected_agents:
                all_results[subtask] = level_results[i]
            else:
                all_results[subtask] = {"status": "failed", "error": "No agent selected"}
    
    return all_results

# --------------------------
# ENHANCED AGENT EXECUTION
# --------------------------
def run_agent_in_sandbox(agent: Dict[str, Any], subtask: str, max_retries: int = 1) -> Dict[str, Any]:
    """Enhanced agent execution with circuit breaker pattern"""
    manager = DockerSandboxManager(agent.get("docker_image") or agent.get("name"))
    cmd = ["python3", "agent.py", subtask]

    # Circuit breaker: check agent health before execution
    agent_health_key = f"agent_health:{agent['id']}"
    failure_count = redis_client.get(agent_health_key)
    
    if failure_count and int(failure_count) > 5:
        logger.warning(f"Circuit breaker: Agent {agent['id']} temporarily disabled")
        return {"status": "failed", "error": "Agent temporarily disabled due to high failure rate"}

    for attempt in range(max_retries):
        try:
            result = manager.run_agent(cmd)
            if result.get("success"):
                # Reset failure count on success
                redis_client.delete(agent_health_key)
                return {"status": "success", "result": result, "agent_id": agent["id"]}
        except Exception as e:
            logger.error(f"Agent execution attempt {attempt + 1} failed: {e}")
    
    # Increment failure count
    redis_client.incr(agent_health_key)
    redis_client.expire(agent_health_key, 300)  # 5 minutes
    
    return {"status": "failed", "error": "Max retries exceeded", "agent_id": agent["id"]}

# --------------------------
# ENHANCED MONITORING
# --------------------------
@shared_task
def cleanup_stale_orchestrations():
    """Periodic task to clean up stale orchestrations"""
    db = SessionLocal()
    try:
        stale_threshold = time.time() - 3600  # 1 hour ago
        stale_orchestrations = db.query(Orchestration).filter(
            Orchestration.current_status.in_(["EXECUTING", "PENDING"]),
            Orchestration.created_at < stale_threshold
        ).all()
        
        for orch in stale_orchestrations:
            orch.current_status = "TIMEOUT"
            logger.warning(f"Marked orchestration {orch.id} as TIMEOUT")
        
        db.commit()
        return {"cleaned": len(stale_orchestrations)}
    finally:
        db.close()

# --------------------------
# WORKFLOW VISUALIZATION DATA
# --------------------------
@shared_task
def generate_workflow_visualization_data(orchestration_id: str) -> Dict[str, Any]:
    """Generate data structure for frontend DAG visualization"""
    db = SessionLocal()
    try:
        orchestration = db.query(Orchestration).filter(Orchestration.id == orchestration_id).first()
        if not orchestration:
            return {"error": "Orchestration not found"}
        
        # Parse workflow for visualization
        workflow = get_cached_workflow(orchestration.user_input)
        if not workflow:
            workflow = parse_workflow_with_llm(orchestration.user_input)
        
        nodes = []
        edges = []
        
        for subtask, plan in workflow.get("dependencies", {}).items():
            # Create node
            nodes.append({
                "id": subtask,
                "label": subtask,
                "status": orchestration.results.get(subtask, {}).get("status", "pending"),
                "agent": orchestration.results.get(subtask, {}).get("agent_id"),
                "order": plan.get("order", 1)
            })
            
            # Create edges for dependencies
            for dependency in plan.get("dependencies", []):
                edges.append({
                    "source": dependency,
                    "target": subtask
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_tasks": len(nodes),
                "orchestration_id": orchestration_id,
                "status": orchestration.current_status
            }
        }
    finally:
        db.close()

# Existing functions remain the same...
def handle_failures_and_retries(results: Dict[str, Any], selected_agents: Dict[str, Agent], db: Session) -> Dict[str, Any]:
    """Retry failed tasks with fallback agents"""
    for subtask, res in results.items():
        if res["status"] == "failed":
            logger.warning(f"Retrying subtask {subtask} with fallback agent")
            fallback_agent = find_fallback_agent(subtask, selected_agents[subtask]["id"], db)
            if fallback_agent:
                retry_res = run_agent_in_sandbox(fallback_agent, subtask)
                results[subtask] = retry_res
    return results

def find_fallback_agent(subtask: str, current_agent_id: str, db: Session) -> Agent:
    """Find a backup agent for a failed subtask"""
    return db.query(Agent).filter(
        Agent.is_active == "active",
        Agent.capabilities.contains([subtask]),
        Agent.id != current_agent_id
    ).first()

def aggregate_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced result aggregation with metrics"""
    successes = {k: v for k, v in results.items() if v["status"] == "success"}
    failures = {k: v for k, v in results.items() if v["status"] == "failed"}

    return {
        "summary": {
            "total": len(results), 
            "success": len(successes), 
            "failed": len(failures),
            "success_rate": len(successes) / len(results) if results else 0
        },
        "results": successes,
        "errors": failures,
        "aggregated_output": "\n".join([f"{k}: {v['result']}" for k, v in successes.items()]),
        "execution_metrics": {
            "parallel_groups_executed": len(build_execution_groups({}, {})),
            "cache_hits": 0  # This would need to be tracked during execution
        }
    }
