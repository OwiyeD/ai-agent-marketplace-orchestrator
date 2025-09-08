#!/usr/bin/env python3
"""
Test script for the AI Agent Marketplace Orchestrator
Demonstrates the orchestrator functionality with sample workflows
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds to wait for orchestration completion

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_step(step: str):
    """Print a formatted step"""
    print(f"\n➤ {step}")

def wait_for_orchestration(orchestration_id: str) -> Dict[str, Any]:
    """Wait for orchestration to complete and return results"""
    print(f"Waiting for orchestration {orchestration_id} to complete...")
    
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        try:
            response = requests.get(f"{BASE_URL}/orchestrate/{orchestration_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get("current_status")
                
                if status == "COMPLETED":
                    print("✅ Orchestration completed successfully!")
                    return data
                elif status == "FAILED":
                    print("❌ Orchestration failed!")
                    return data
                elif status in ["PARSING", "EXECUTING"]:
                    print(f"⏳ Status: {status}...")
                else:
                    print(f"ℹ️  Status: {status}")
                
                time.sleep(2)
            else:
                print(f"Error checking status: {response.status_code}")
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"Error checking status: {e}")
            time.sleep(2)
    
    print(f"⏰ Timeout waiting for orchestration completion after {TIMEOUT} seconds")
    return {}

def test_health_check():
    """Test the health check endpoint"""
    print_step("Testing health check endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

def test_list_agents():
    """Test listing agents"""
    print_step("Testing agent listing")
    
    try:
        response = requests.get(f"{BASE_URL}/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Found {len(agents)} agents:")
            for agent in agents:
                print(f"  • {agent['name']} - {agent['capabilities']}")
            return agents
        else:
            print(f"❌ Failed to list agents: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing agents: {e}")
        return []

def test_workflow_definitions():
    """Test getting workflow definitions"""
    print_step("Testing workflow definitions")
    
    try:
        response = requests.get(f"{BASE_URL}/workflows")
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ Available workflows:")
            for workflow_name, workflow_data in workflows.items():
                print(f"  • {workflow_name}: {workflow_data['subtasks']}")
            return workflows
        else:
            print(f"❌ Failed to get workflows: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting workflows: {e}")
        return {}

def test_ecommerce_workflow():
    """Test the e-commerce onboarding workflow"""
    print_step("Testing e-commerce onboarding workflow")
    
    try:
        # Start the demo workflow
        response = requests.post(f"{BASE_URL}/demo/ecommerce-onboarding")
        if response.status_code == 200:
            data = response.json()
            orchestration_id = data.get("orchestration_id")
            print(f"✅ Demo workflow started: {orchestration_id}")
            
            # Wait for completion
            results = wait_for_orchestration(orchestration_id)
            if results:
                print("\n📊 Workflow Results:")
                print(json.dumps(results, indent=2))
            
            return results
        else:
            print(f"❌ Failed to start demo workflow: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error starting demo workflow: {e}")
        return {}

def test_custom_orchestration():
    """Test custom orchestration request"""
    print_step("Testing custom orchestration request")
    
    custom_request = {
        "user_input": "Research market trends for AI agents and create a summary report",
        "workflow_type": "research"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/orchestrate",
            json=custom_request
        )
        
        if response.status_code == 200:
            data = response.json()
            orchestration_id = data.get("id")
            print(f"✅ Custom orchestration created: {orchestration_id}")
            
            # Wait for completion
            results = wait_for_orchestration(orchestration_id)
            if results:
                print("\n📊 Custom Workflow Results:")
                print(json.dumps(results, indent=2))
            
            return results
        else:
            print(f"❌ Failed to create custom orchestration: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating custom orchestration: {e}")
        return {}

def test_agent_filtering():
    """Test agent filtering by capability"""
    print_step("Testing agent filtering by capability")
    
    capabilities = ["extract", "copywrite", "seo", "web_search"]
    
    for capability in capabilities:
        try:
            response = requests.get(f"{BASE_URL}/agents?capability={capability}")
            if response.status_code == 200:
                agents = response.json()
                print(f"  • {capability}: {len(agents)} agents found")
                for agent in agents:
                    print(f"    - {agent['name']}")
            else:
                print(f"  • {capability}: Error {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  • {capability}: Error {e}")

def main():
    """Main test function"""
    print_section("AI Agent Marketplace Orchestrator - Test Suite")
    
    # Check if the service is running
    if not test_health_check():
        print("\n❌ Service is not running. Please start the orchestrator first.")
        print("   Run: python start.py")
        sys.exit(1)
    
    # Test basic functionality
    test_list_agents()
    test_workflow_definitions()
    
    # Test agent filtering
    test_agent_filtering()
    
    # Test workflows
    test_ecommerce_workflow()
    test_custom_orchestration()
    
    print_section("Test Suite Complete")
    print("✅ All tests completed successfully!")
    print("\nYou can now:")
    print("• View the API documentation at: http://localhost:8000/docs")
    print("• Monitor orchestrations at: http://localhost:8000/orchestrate")
    print("• Manage agents at: http://localhost:8000/agents")

if __name__ == "__main__":
    main()




