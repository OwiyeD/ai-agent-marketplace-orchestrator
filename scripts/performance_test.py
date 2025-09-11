#!/usr/bin/env python3
"""
Performance testing script using locust for load testing the orchestrator.
"""
from locust import HttpUser, task, between
import json
import uuid
import random

class OrchestrationUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Set up test data when user starts"""
        self.sample_requests = [
            "Create e-commerce product listing for smartphone",
            "Generate marketing content for new clothing line",
            "Process customer feedback and generate insights",
            "Translate product descriptions to multiple languages",
            "Optimize website content for search engines",
            "Extract data from competitor websites",
            "Generate social media content calendar",
            "Create automated email marketing campaign"
        ]
    
    @task(3)
    def create_orchestration(self):
        """Test orchestration creation (most common operation)"""
        request_data = {
            "user_input": random.choice(self.sample_requests),
            "workflow_type": "performance_test",
            "priority": random.choice(["low", "medium", "high"])
        }
        
        with self.client.post("/orchestrate", json=request_data, catch_response=True) as response:
            if response.status_code == 200:
                response_data = response.json()
                # Store orchestration ID for later status checks
                if hasattr(self, 'orchestration_ids'):
                    self.orchestration_ids.append(response_data.get("orchestration_id"))
                else:
                    self.orchestration_ids = [response_data.get("orchestration_id")]
                response.success()
            else:
                response.failure(f"Failed to create orchestration: {response.status_code}")
    
    @task(2)
    def check_orchestration_status(self):
        """Test status checking"""
        if hasattr(self, 'orchestration_ids') and self.orchestration_ids:
            orchestration_id = random.choice(self.orchestration_ids)
            with self.client.get(f"/orchestrate/{orchestration_id}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to get orchestration status: {response.status_code}")
    
    @task(1)
    def list_agents(self):
        """Test agent listing"""
        with self.client.get("/agents", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list agents: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """Test metrics endpoint"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get metrics: {response.status_code}")

# Run performance test
if __name__ == "__main__":
    import subprocess
    import sys
    
    # Default configuration
    users = 10
    spawn_rate = 2
    run_time = "30s"
    host = "http://localhost:8000"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        users = int(sys.argv[1])
    if len(sys.argv) > 2:
        spawn_rate = int(sys.argv[2])
    if len(sys.argv) > 3:
        run_time = sys.argv[3]
    if len(sys.argv) > 4:
        host = sys.argv[4]
    
    print(f"🚀 Starting performance test...")
    print(f"   Users: {users}")
    print(f"   Spawn rate: {spawn_rate}/second")
    print(f"   Duration: {run_time}")
    print(f"   Target: {host}")
    
    # Run locust
    cmd = [
        "locust",
        "-f", __file__,
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "-t", run_time,
        "--host", host,
        "--html", "performance_report.html"
    ]
    
    subprocess.run(cmd)
    print("✅ Performance test completed. Report saved to performance_report.html")