#!/usr/bin/env python3
"""
Redis Cleanup Script - Remove zombie call histories
"""
import redis
import os
from dotenv import load_dotenv

load_dotenv()

def cleanup_zombie_calls():
    try:
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        
        # Get all history keys
        keys = r.keys('history:*')
        print(f"Found {len(keys)} zombie call histories")
        
        if keys:
            # Delete all zombie call histories
            deleted = r.delete(*keys)
            print(f"Successfully cleared {deleted} zombie calls")
        else:
            print("No zombie calls found")
            
        # Also clean up old celery task metadata
        task_keys = r.keys('celery-task-meta-*')
        if len(task_keys) > 100:  # Keep only recent 100 tasks
            old_tasks = task_keys[:-100]
            if old_tasks:
                r.delete(*old_tasks)
                print(f"Cleaned up {len(old_tasks)} old task metadata")
        
        print("Redis cleanup completed successfully!")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    cleanup_zombie_calls()
