"""
sandbox_manager.py
------------------
Manages agent execution in Docker containers for strong isolation.
"""
import subprocess
import uuid
import time

class DockerSandboxManager:
    def __init__(self, image_name):
        self.image_name = image_name

    def run_agent(self, agent_cmd, mem_limit_mb=128, timeout_sec=60, network_disabled=True):
        """
        Launches a Docker container, runs the agent command, and collects logs.
        Returns execution metadata.
        """
        container_name = f"agent-sandbox-{uuid.uuid4()}"
        mem_limit = f"{mem_limit_mb}m"
        docker_cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--memory", mem_limit,
            "--cpus", "1",
        ]
        if network_disabled:
            docker_cmd += ["--network", "none"]
        docker_cmd += [self.image_name] + agent_cmd
        start_time = time.time()
        try:
            result = subprocess.run(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_sec
            )
            success = result.returncode == 0
            output = result.stdout.decode()
            error = result.stderr.decode()
        except subprocess.TimeoutExpired:
            success = False
            output = ""
            error = "Timeout"
        except Exception as e:
            success = False
            output = ""
            error = str(e)
        latency = time.time() - start_time
        return {
            "success": success,
            "latency": latency,
            "output": output,
            "error": error,
            "container_name": container_name
        }

# Example usage:
# manager = DockerSandboxManager("python:3.9-slim")
# result = manager.run_agent(["python3", "agent.py"])
# print(result)
