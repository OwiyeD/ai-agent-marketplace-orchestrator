class OrchestrationError(Exception):
    """Base exception for orchestration errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or "ORCHESTRATION_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class AgentSelectionError(OrchestrationError):
    """Agent selection failed"""
    def __init__(self, message: str, subtask: str = None):
        super().__init__(message, "AGENT_SELECTION_ERROR", {"subtask": subtask})

class SandboxExecutionError(OrchestrationError):
    """Sandbox execution failed"""
    def __init__(self, message: str, agent_id: str = None, exit_code: int = None):
        super().__init__(
            message, 
            "SANDBOX_ERROR", 
            {"agent_id": agent_id, "exit_code": exit_code}
        )

class CacheError(OrchestrationError):
    """Cache operation failed"""
    pass

class WorkflowParsingError(OrchestrationError):
    """Workflow parsing failed"""
    pass