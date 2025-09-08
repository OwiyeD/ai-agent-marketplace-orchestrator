#!/usr/bin/env python3
"""
Startup script for the AI Agent Marketplace Orchestrator
Initializes database with sample data and starts the application
"""

import asyncio
import sys
import os
from database import SessionLocal, create_tables, Agent, Orchestration
from sqlalchemy.orm import Session

def init_sample_data():
    """Initialize database with sample agents and workflows"""
    db = SessionLocal()
    try:
        # Check if sample agents already exist
        existing_agents = db.query(Agent).count()
        if existing_agents > 0:
            print("Sample agents already exist, skipping initialization...")
            return
        
        print("Initializing sample agents...")
        
        # Sample agents for e-commerce workflow
        sample_agents = [
            {
                "name": "Data Extractor Pro",
                "description": "Advanced data extraction agent that can parse product information from websites, PDFs, and structured data sources",
                "endpoint_url": "http://localhost:8001/extract",
                "capabilities": ["extract", "data_parsing", "web_scraping"],
                "reputation_score": 95
            },
            {
                "name": "Creative Copywriter",
                "description": "AI-powered copywriting agent that creates compelling product descriptions, marketing copy, and brand messaging",
                "endpoint_url": "http://localhost:8002/copywrite",
                "capabilities": ["copywrite", "content_creation", "marketing"],
                "reputation_score": 92
            },
            {
                "name": "SEO Optimizer",
                "description": "Search engine optimization specialist that analyzes content and provides keyword recommendations and meta descriptions",
                "endpoint_url": "http://localhost:8003/seo",
                "capabilities": ["seo", "keyword_analysis", "meta_optimization"],
                "reputation_score": 88
            },
            {
                "name": "Web Research Agent",
                "description": "Comprehensive web research agent that can search, analyze, and summarize information from multiple sources",
                "endpoint_url": "http://localhost:8004/research",
                "capabilities": ["web_search", "research", "data_analysis"],
                "reputation_score": 90
            },
            {
                "name": "Data Analyst",
                "description": "Data analysis and visualization agent that processes structured data and generates insights",
                "endpoint_url": "http://localhost:8005/analyze",
                "capabilities": ["data_analysis", "visualization", "insights"],
                "reputation_score": 87
            }
        ]
        
        # Create agents
        for agent_data in sample_agents:
            agent = Agent(**agent_data)
            db.add(agent)
            print(f"  ✓ Created agent: {agent.name}")
        
        db.commit()
        print(f"Successfully created {len(sample_agents)} sample agents!")
        
    except Exception as e:
        print(f"Error initializing sample data: {e}")
        db.rollback()
    finally:
        db.close()

def check_dependencies():
    """Check if required services are available"""
    import socket
    
    services = [
        ("PostgreSQL", "localhost", 5432),
        ("Redis", "localhost", 6379)
    ]
    
    print("Checking service dependencies...")
    
    for service_name, host, port in services:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"  ✓ {service_name} is running on {host}:{port}")
            else:
                print(f"  ✗ {service_name} is not accessible on {host}:{port}")
                print(f"    Please ensure {service_name} is running before starting the application")
                return False
        except Exception as e:
            print(f"  ✗ Error checking {service_name}: {e}")
            return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 AI Agent Marketplace Orchestrator - Starting up...")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Service dependencies not met. Please start required services first.")
        print("   You can use: docker-compose up -d")
        sys.exit(1)
    
    # Initialize database
    print("\n📊 Initializing database...")
    try:
        create_tables()
        print("  ✓ Database tables created successfully")
    except Exception as e:
        print(f"  ✗ Error creating database tables: {e}")
        print("   Please check your database connection settings")
        sys.exit(1)
    
    # Initialize sample data
    print("\n🤖 Initializing sample data...")
    init_sample_data()
    
    print("\n✅ Startup complete! Starting FastAPI application...")
    print("=" * 60)
    
    # Start the FastAPI application
    import uvicorn
    from config import settings
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()




