#!/usr/bin/env python3
"""
AuraVoice AI Voice Agent - Production Startup Script
Optimized for concurrent calls and low-latency processing
"""

import os
import sys
import time
import logging
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AuraVoiceManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        
    def check_dependencies(self):
        """Check if all required services are available"""
        logger.info("🔍 Checking system dependencies...")
        
        # Check Redis connection
        try:
            import redis
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            r = redis.from_url(redis_url)
            r.ping()
            logger.info("✅ Redis connection successful")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
            
        # Check Groq API key
        if not os.environ.get("GROQ_API_KEY"):
            logger.error("❌ GROQ_API_KEY not found in environment")
            return False
        logger.info("✅ Groq API key found")
        
        # Check SignalWire credentials
        required_sw_vars = ["SIGNALWIRE_PROJECT_ID", "SIGNALWIRE_API_TOKEN"]
        for var in required_sw_vars:
            if not os.environ.get(var):
                logger.error(f"❌ {var} not found in environment")
                return False
        logger.info("✅ SignalWire credentials found")
        
        # Check local STT model
        stt_path = Path("local_stt_models/tiny.en")
        if not stt_path.exists():
            logger.warning("⚠️ Local STT model not found - will download on first use")
        else:
            logger.info("✅ Local STT model found")
            
        return True
    
    def start_celery_worker(self):
        """Start optimized Celery worker for voice processing"""
        logger.info("🚀 Starting Celery worker...")
        
        cmd = [
            "celery", "-A", "celery_worker.celery_app", "worker",
            "--loglevel=info",
            "--concurrency=4",  # Optimized for voice processing
            "--pool=prefork",   # Better for CPU-intensive tasks
            "--queues=voice_processing",
            "--hostname=aura-voice-worker@%h",
            "--max-tasks-per-child=100",
            "--max-memory-per-child=200000"  # 200MB limit
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes['celery'] = process
            logger.info("✅ Celery worker started successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Celery worker: {e}")
            return False
    
    def start_relay_server(self):
        """Start SignalWire Relay server"""
        logger.info("🚀 Starting SignalWire Relay server...")
        
        try:
            # FIXED: Use the optimized relay server
            process = subprocess.Popen(
                [sys.executable, "relay_server_fixed.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes['relay'] = process
            logger.info("✅ SignalWire Relay server (FIXED VERSION) started successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Relay server: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor and restart processes if they fail"""
        logger.info("👁️ Starting process monitoring...")
        
        while self.running:
            for name, process in list(self.processes.items()):
                if process.poll() is not None:
                    logger.warning(f"⚠️ Process {name} has stopped. Restarting...")
                    
                    if name == 'celery':
                        self.start_celery_worker()
                    elif name == 'relay':
                        self.start_relay_server()
                        
            time.sleep(5)  # Check every 5 seconds
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("🛑 Received shutdown signal. Stopping services...")
        self.running = False
        
        for name, process in self.processes.items():
            logger.info(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {name}...")
                process.kill()
        
        logger.info("✅ All services stopped. Goodbye!")
        sys.exit(0)
    
    def start(self):
        """Start all services"""
        logger.info("🎯 Starting AuraVoice AI Voice Agent...")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("❌ Dependency check failed. Exiting.")
            sys.exit(1)
        
        # Start services
        if not self.start_celery_worker():
            logger.error("❌ Failed to start Celery worker. Exiting.")
            sys.exit(1)
            
        # Wait a moment for Celery to initialize
        time.sleep(3)
        
        if not self.start_relay_server():
            logger.error("❌ Failed to start Relay server. Exiting.")
            sys.exit(1)
        
        logger.info("🎉 AuraVoice is now running and ready for calls!")
        logger.info("📞 Waiting for incoming calls...")
        
        # Start monitoring
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    manager = AuraVoiceManager()
    manager.start()
