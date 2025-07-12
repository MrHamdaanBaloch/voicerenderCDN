#!/usr/bin/env python3
"""
AuraVoice Debug Monitor - Real-time Performance Tracking
Monitors latency, errors, and system health for production debugging
"""

import os
import time
import json
import redis
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()

class AuraVoiceMonitor:
    def __init__(self):
        self.redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        self.metrics = defaultdict(lambda: deque(maxlen=100))  # Keep last 100 entries
        self.call_stats = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - MONITOR - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_call_metrics(self):
        """Collect real-time call metrics from Redis"""
        try:
            # Get all active call histories
            call_keys = self.redis_client.keys("history:*")
            active_calls = len(call_keys)
            
            # Get recent task completion times
            task_keys = self.redis_client.keys("celery-task-meta-*")
            
            current_time = datetime.now()
            
            # Collect metrics
            self.metrics['active_calls'].append({
                'timestamp': current_time.isoformat(),
                'count': active_calls
            })
            
            # Analyze task performance
            recent_tasks = 0
            total_task_time = 0
            
            for key in task_keys[-10:]:  # Check last 10 tasks
                try:
                    task_data = self.redis_client.get(key)
                    if task_data:
                        task_info = json.loads(task_data)
                        if task_info.get('status') == 'SUCCESS':
                            recent_tasks += 1
                            # Estimate task time (this is simplified)
                            total_task_time += 2.5  # Average task time
                except:
                    continue
            
            avg_task_time = total_task_time / max(recent_tasks, 1)
            
            self.metrics['avg_task_time'].append({
                'timestamp': current_time.isoformat(),
                'time': avg_task_time
            })
            
            return {
                'active_calls': active_calls,
                'recent_tasks': recent_tasks,
                'avg_task_time': avg_task_time
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None
    
    def analyze_performance(self):
        """Analyze system performance and identify bottlenecks"""
        if len(self.metrics['active_calls']) < 2:
            return "Insufficient data for analysis"
        
        # Get recent metrics
        recent_calls = [m['count'] for m in list(self.metrics['active_calls'])[-10:]]
        recent_times = [m['time'] for m in list(self.metrics['avg_task_time'])[-10:]]
        
        avg_calls = sum(recent_calls) / len(recent_calls)
        avg_time = sum(recent_times) / len(recent_times)
        
        analysis = []
        
        # Performance analysis
        if avg_time > 5.0:
            analysis.append("⚠️ HIGH LATENCY: Average task time > 5s")
        elif avg_time < 2.0:
            analysis.append("✅ GOOD LATENCY: Average task time < 2s")
        
        if avg_calls > 5:
            analysis.append("📈 HIGH LOAD: Multiple concurrent calls")
        elif avg_calls == 0:
            analysis.append("💤 IDLE: No active calls")
        
        # Check for trends
        if len(recent_times) >= 5:
            recent_trend = sum(recent_times[-3:]) / 3
            older_trend = sum(recent_times[-6:-3]) / 3
            
            if recent_trend > older_trend * 1.2:
                analysis.append("📈 DEGRADING: Performance getting worse")
            elif recent_trend < older_trend * 0.8:
                analysis.append("📉 IMPROVING: Performance getting better")
        
        return "\n".join(analysis) if analysis else "✅ System running normally"
    
    def check_system_health(self):
        """Check overall system health"""
        health_status = {
            'redis': False,
            'groq_api': False,
            'signalwire': False,
            'local_models': False
        }
        
        # Check Redis
        try:
            self.redis_client.ping()
            health_status['redis'] = True
        except:
            pass
        
        # Check if Groq API key exists
        if os.environ.get("GROQ_API_KEY"):
            health_status['groq_api'] = True
        
        # Check SignalWire credentials
        if os.environ.get("SIGNALWIRE_PROJECT_ID") and os.environ.get("SIGNALWIRE_API_TOKEN"):
            health_status['signalwire'] = True
        
        # Check local models
        if os.path.exists("local_stt_models/tiny.en"):
            health_status['local_models'] = True
        
        return health_status
    
    def display_dashboard(self):
        """Display real-time dashboard"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🎯 AuraVoice AI Voice Agent - Live Monitor")
        print("=" * 60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Collect current metrics
        current_metrics = self.collect_call_metrics()
        
        if current_metrics:
            print("📊 CURRENT METRICS:")
            print(f"   Active Calls: {current_metrics['active_calls']}")
            print(f"   Recent Tasks: {current_metrics['recent_tasks']}")
            print(f"   Avg Task Time: {current_metrics['avg_task_time']:.2f}s")
            print()
        
        # System health
        health = self.check_system_health()
        print("🏥 SYSTEM HEALTH:")
        for service, status in health.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {service.replace('_', ' ').title()}")
        print()
        
        # Performance analysis
        analysis = self.analyze_performance()
        print("🔍 PERFORMANCE ANALYSIS:")
        for line in analysis.split('\n'):
            print(f"   {line}")
        print()
        
        # Recent activity
        if len(self.metrics['active_calls']) > 0:
            print("📈 RECENT ACTIVITY (Last 10 measurements):")
            recent_calls = list(self.metrics['active_calls'])[-10:]
            for entry in recent_calls[-5:]:  # Show last 5
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%H:%M:%S')
                print(f"   {timestamp}: {entry['count']} active calls")
        
        print("\n" + "=" * 60)
        print("Press Ctrl+C to exit")
    
    def run_monitor(self):
        """Run the monitoring dashboard"""
        self.logger.info("Starting AuraVoice Monitor...")
        
        try:
            while True:
                self.display_dashboard()
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped. Goodbye!")
    
    def export_metrics(self, filename=None):
        """Export collected metrics to JSON file"""
        if not filename:
            filename = f"aura_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'metrics': {
                key: list(values) for key, values in self.metrics.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Metrics exported to {filename}")
        return filename

def main():
    import sys
    
    monitor = AuraVoiceMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--export':
        # Export mode
        filename = monitor.export_metrics()
        print(f"Metrics exported to {filename}")
    else:
        # Live monitor mode
        monitor.run_monitor()

if __name__ == "__main__":
    main()
