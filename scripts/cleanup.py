# scripts/cleanup.py - Cleanup unused resources
#!/usr/bin/env python3
"""
Cleanup script to remove unused Docker images, containers, and Redis cache data.
"""
import docker
import redis
import sys
from src.orchestrator.config.settings import settings
from src.orchestrator.utils.logger import get_logger

logger = get_logger(__name__)

def cleanup_docker_resources():
    """Clean up unused Docker resources"""
    logger.info("🧹 Cleaning up Docker resources...")
    
    try:
        client = docker.from_env()
        
        # Remove stopped containers
        stopped_containers = client.containers.list(all=True, filters={"status": "exited"})
        for container in stopped_containers:
            if container.name.startswith("agent-"):
                container.remove()
                logger.info(f"Removed container: {container.name}")
        
        # Remove dangling images
        dangling_images = client.images.list(filters={"dangling": True})
        for image in dangling_images:
            client.images.remove(image.id, force=True)
            logger.info(f"Removed dangling image: {image.id[:12]}")
        
        # Prune unused networks
        client.networks.prune()
        
        # Prune unused volumes
        client.volumes.prune()
        
        logger.info("✅ Docker cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Docker cleanup failed: {e}")

def cleanup_redis_cache():
    """Clean up expired Redis cache entries"""
    logger.info("🧹 Cleaning up Redis cache...")
    
    try:
        # Connect to cache Redis instance
        cache_client = redis.Redis.from_url(settings.redis_cache_url)
        
        # Get all cache keys
        cache_keys = cache_client.keys("*")
        expired_keys = []
        
        for key in cache_keys:
            ttl = cache_client.ttl(key)
            if ttl == -2:  # Key doesn't exist (expired)
                expired_keys.append(key)
            elif ttl == -1:  # Key exists but has no TTL (shouldn't happen in our cache)
                # Set TTL for keys without expiration
                cache_client.expire(key, settings.cache_ttl)
        
        if expired_keys:
            cache_client.delete(*expired_keys)
            logger.info(f"Removed {len(expired_keys)} expired cache keys")
        
        # Clean up old performance metrics
        perf_keys = cache_client.keys("agent_perf:*")
        old_perf_keys = []
        
        for key in perf_keys:
            ttl = cache_client.ttl(key)
            if ttl > 0 and ttl < 3600:  # Keys expiring in less than 1 hour
                old_perf_keys.append(key)
        
        if old_perf_keys:
            cache_client.delete(*old_perf_keys)
            logger.info(f"Removed {len(old_perf_keys)} old performance keys")
        
        logger.info("✅ Redis cache cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Redis cache cleanup failed: {e}")

def cleanup_log_files():
    """Clean up old log files"""
    import os
    import glob
    from datetime import datetime, timedelta
    
    logger.info("🧹 Cleaning up old log files...")
    
    log_patterns = ["logs/*.log", "logs/*.log.*", "*.log"]
    old_threshold = datetime.now() - timedelta(days=7)  # Keep logs for 7 days
    
    removed_count = 0
    for pattern in log_patterns:
        for log_file in glob.glob(pattern):
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_time < old_threshold:
                    os.remove(log_file)
                    removed_count += 1
                    logger.info(f"Removed old log file: {log_file}")
            except Exception as e:
                logger.warning(f"Could not remove log file {log_file}: {e}")
    
    if removed_count > 0:
        logger.info(f"✅ Removed {removed_count} old log files")
    else:
        logger.info("✅ No old log files to remove")

def main():
    """Main cleanup function"""
    if len(sys.argv) > 1:
        cleanup_type = sys.argv[1].lower()
    else:
        cleanup_type = "all"
    
    logger.info(f"🧹 Starting cleanup (type: {cleanup_type})...")
    
    if cleanup_type in ["all", "docker"]:
        cleanup_docker_resources()
    
    if cleanup_type in ["all", "redis", "cache"]:
        cleanup_redis_cache()
    
    if cleanup_type in ["all", "logs"]:
        cleanup_log_files()
    
    logger.info("✅ Cleanup completed successfully!")
    print("\n🧹 Cleanup Summary:")
    print("   • Docker: Removed unused containers, images, networks, volumes")
    print("   • Redis: Cleaned expired cache keys and old metrics")
    print("   • Logs: Removed log files older than 7 days")

if __name__ == "__main__":
    main()
