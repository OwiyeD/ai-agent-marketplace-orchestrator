# scripts/seed_data.py - Seed database with sample data
#!/usr/bin/env python3
"""
Seed database with sample agents and workflows for development and testing.
"""
import asyncio
import uuid
from sqlalchemy.orm import Session
from src.orchestrator.config.database import SessionLocal
from src.orchestrator.models.database import Agent, Orchestration
from src.orchestrator.utils.logger import get_logger

logger = get_logger(__name__)

SAMPLE_AGENTS = [
    {
        "name": "Data Extractor Pro",
        "description": "Advanced data extraction from various sources including APIs, databases, and files",
        "endpoint_url": "http://localhost:8001/extract",
        "capabilities": ["data_extraction", "api_scraping", "file_parsing", "database_query"],
        "reputation_score": 95,
        "docker_image": "agent-data-extractor-pro:latest"
    },
    {
        "name": "AI Copywriter",
        "description": "Generate compelling marketing copy and product descriptions",
        "endpoint_url": "http://localhost:8002/copywrite",
        "capabilities": ["copywriting", "content_generation", "marketing_copy", "product_descriptions"],
        "reputation_score": 90,
        "docker_image": "agent-ai-copywriter:latest"
    },
    {
        "name": "SEO Optimizer",
        "description": "Optimize content for search engines and improve rankings",
        "endpoint_url": "http://localhost:8003/optimize",
        "capabilities": ["seo_optimization", "keyword_analysis", "meta_tags", "content_optimization"],
        "reputation_score": 88,
        "docker_image": "agent-seo-optimizer:latest"
    },
    {
        "name": "Image Processor",
        "description": "Process and optimize images for web and mobile applications",
        "endpoint_url": "http://localhost:8004/process",
        "capabilities": ["image_processing", "image_optimization", "thumbnail_generation", "format_conversion"],
        "reputation_score": 92,
        "docker_image": "agent-image-processor:latest"
    },
    {
        "name": "Translation Service",
        "description": "Multi-language translation with context awareness",
        "endpoint_url": "http://localhost:8005/translate",
        "capabilities": ["translation", "localization", "multilingual_support", "context_translation"],
        "reputation_score": 87,
        "docker_image": "agent-translation-service:latest"
    },
    {
        "name": "Data Validator",
        "description": "Validate and clean data across multiple formats",
        "endpoint_url": "http://localhost:8006/validate",
        "capabilities": ["data_validation", "data_cleaning", "schema_validation", "quality_assurance"],
        "reputation_score": 93,
        "docker_image": "agent-data-validator:latest"
    }
]

SAMPLE_WORKFLOWS = [
    {
        "user_input": "Set up e-commerce product onboarding workflow",
        "workflow_type": "ecommerce_onboarding",
        "current_status": "COMPLETED",
        "subtasks": [
            "Extract product data from supplier feed",
            "Generate compelling product descriptions",
            "Optimize content for SEO",
            "Process and optimize product images"
        ],
        "results": {
            "summary": {"total": 4, "success": 4, "failed": 0, "success_rate": 1.0},
            "results": {
                "extract": {"status": "success", "processing_time": 2.3},
                "copywrite": {"status": "success", "processing_time": 4.1},
                "seo": {"status": "success", "processing_time": 1.8},
                "images": {"status": "success", "processing_time": 3.2}
            }
        }
    },
    {
        "user_input": "Create multilingual content pipeline",
        "workflow_type": "content_localization",
        "current_status": "COMPLETED",
        "subtasks": [
            "Extract source content",
            "Translate to target languages",
            "Validate translations",
            "Generate localized SEO content"
        ]
    }
]

def seed_agents(db: Session) -> None:
    """Seed database with sample agents"""
    logger.info("🌱 Seeding agents...")
    
    # Check if agents already exist
    existing_count = db.query(Agent).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing agents. Skipping agent seeding.")
        return
    
    for agent_data in SAMPLE_AGENTS:
        agent = Agent(
            id=str(uuid.uuid4()),
            **agent_data
        )
        db.add(agent)
    
    db.commit()
    logger.info(f"✅ Successfully seeded {len(SAMPLE_AGENTS)} agents")

def seed_orchestrations(db: Session) -> None:
    """Seed database with sample orchestrations"""
    logger.info("🌱 Seeding orchestrations...")
    
    # Check if orchestrations already exist
    existing_count = db.query(Orchestration).count()
    if existing_count > 0:
        logger.info(f"Found {existing_count} existing orchestrations. Skipping orchestration seeding.")
        return
    
    for workflow_data in SAMPLE_WORKFLOWS:
        orchestration = Orchestration(
            id=str(uuid.uuid4()),
            **workflow_data
        )
        db.add(orchestration)
    
    db.commit()
    logger.info(f"✅ Successfully seeded {len(SAMPLE_WORKFLOWS)} orchestrations")

def main():
    """Main seeding function"""
    logger.info("🌱 Starting database seeding...")
    
    db = SessionLocal()
    try:
        seed_agents(db)
        seed_orchestrations(db)
        logger.info("✅ Database seeding completed successfully!")
        
        # Print summary
        agent_count = db.query(Agent).count()
        orchestration_count = db.query(Orchestration).count()
        
        print(f"\n📊 Database Summary:")
        print(f"   Agents: {agent_count}")
        print(f"   Orchestrations: {orchestration_count}")
        print(f"\n🌐 You can now:")
        print(f"   • View agents: http://localhost:8000/agents")
        print(f"   • View orchestrations: http://localhost:8000/orchestrate")
        print(f"   • API docs: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
