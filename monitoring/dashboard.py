#!/usr/bin/env python3
"""
Real-time DGM-Chess Evolution Monitoring Dashboard

This dashboard provides live monitoring of the evolution training process,
including performance metrics, tool creation, resource usage, and progress visualization.
"""

import os
import sys
import time
import json
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_id: str
    generation: int
    performance: float
    legal_move_rate: float
    tool_usage_count: int
    tools_created: List[str]
    parent_id: Optional[str]
    created_at: datetime
    status: str  # 'active', 'completed', 'failed'

@dataclass
class GenerationStats:
    """Statistics for a complete generation"""
    generation: int
    agents_created: int
    agents_succeeded: int
    best_performance: float
    average_performance: float
    tools_created_this_gen: int
    total_tools_created: int
    duration: timedelta
    completed_at: Optional[datetime]

class DGMChessMonitor:
    """Main monitoring class for DGM-Chess evolution"""
    
    def __init__(self, archive_dir: str = "archive", refresh_rate: int = 5):
        self.archive_dir = Path(archive_dir)
        self.refresh_rate = refresh_rate
        self.start_time = datetime.now()
        self.generation_stats: Dict[int, GenerationStats] = {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.resource_history: List[Dict] = []
        self.running = False
        
    def start_monitoring(self):
        """Start the monitoring dashboard"""
        print("🚀 Starting DGM-Chess Evolution Monitor...")
        print(f"📁 Archive directory: {self.archive_dir}")
        print(f"🔄 Refresh rate: {self.refresh_rate}s")
        print("="*80)
        
        self.running = True
        
        # Start resource monitoring thread
        resource_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        resource_thread.start()
        
        try:
            while self.running:
                self._update_display()
                time.sleep(self.refresh_rate)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            self.running = False
    
    def _update_display(self):
        """Update the main dashboard display"""
        # Clear screen (cross-platform)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Load latest data
        self._load_archive_data()
        
        # Display header
        self._display_header()
        
        # Display current generation status
        self._display_current_generation()
        
        # Display performance trends
        self._display_performance_trends()
        
        # Display tool creation summary
        self._display_tool_summary()
        
        # Display resource usage
        self._display_resource_usage()
        
        # Display recent activities
        self._display_recent_activities()
        
        # Display milestones and targets
        self._display_milestones()
    
    def _display_header(self):
        """Display dashboard header"""
        current_time = datetime.now()
        runtime = current_time - self.start_time
        
        print("🎯 DGM-Chess Evolution Monitor")
        print("="*80)
        print(f"⏰ Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕐 Runtime: {self._format_duration(runtime)}")
        print()
    
    def _display_current_generation(self):
        """Display current generation status"""
        if not self.generation_stats:
            print("📊 Status: Waiting for evolution to begin...")
            print()
            return
            
        latest_gen = max(self.generation_stats.keys())
        current_gen = self.generation_stats[latest_gen]
        
        # Calculate overall progress
        max_generations = 80  # From config
        progress_pct = (latest_gen / max_generations) * 100
        
        # Get best performance across all generations
        best_overall = max([gs.best_performance for gs in self.generation_stats.values()], default=0)
        avg_overall = sum([gs.average_performance for gs in self.generation_stats.values()]) / len(self.generation_stats)
        
        print(f"📊 Generation: {latest_gen}/80 ({progress_pct:.1f}%)")
        print(f"🏆 Best Performance: {best_overall:.1f}%    📈 Overall Avg: {avg_overall:.1f}%")
        print(f"🤖 Current Gen - Created: {current_gen.agents_created}, Succeeded: {current_gen.agents_succeeded}")
        
        # Progress bar
        bar_length = 40
        filled_length = int(bar_length * progress_pct / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"Progress: |{bar}| {progress_pct:.1f}%")
        print()
    
    def _display_performance_trends(self):
        """Display performance trends over generations"""
        if len(self.generation_stats) < 2:
            return
            
        print("📈 Performance Trends (Last 10 Generations):")
        
        # Get last 10 generations
        recent_gens = sorted(self.generation_stats.keys())[-10:]
        
        for gen in recent_gens:
            stats = self.generation_stats[gen]
            # Simple trend indicator
            if gen > 0 and gen-1 in self.generation_stats:
                prev_best = self.generation_stats[gen-1].best_performance
                trend = "📈" if stats.best_performance > prev_best else "📉" if stats.best_performance < prev_best else "➡️"
            else:
                trend = "🆕"
            
            print(f"  Gen {gen:2d}: {stats.best_performance:5.1f}% (avg: {stats.average_performance:5.1f}%) {trend}")
        print()
    
    def _display_tool_summary(self):
        """Display tool creation summary"""
        total_tools = sum([len(agent.tools_created) for agent in self.agent_metrics.values()])
        active_agents = len([a for a in self.agent_metrics.values() if a.status == 'active'])
        
        print(f"🔧 Tools Created: {total_tools}    🤖 Active Agents: {active_agents}")
        
        # Most recent tool creations
        recent_tools = []
        for agent in self.agent_metrics.values():
            for tool in agent.tools_created:
                recent_tools.append((tool, agent.agent_id, agent.generation))
        
        recent_tools = recent_tools[-5:]  # Last 5 tools
        if recent_tools:
            print("Recent Tool Creations:")
            for tool, agent_id, gen in recent_tools:
                print(f"  🔨 {tool} (by {agent_id}, gen {gen})")
        print()
    
    def _display_resource_usage(self):
        """Display system resource usage"""
        if not self.resource_history:
            return
            
        latest_resources = self.resource_history[-1]
        
        memory_pct = latest_resources['memory_percent']
        cpu_pct = latest_resources['cpu_percent']
        
        # Memory usage bar
        memory_bar = self._create_usage_bar(memory_pct, 80)  # Warning at 80%
        cpu_bar = self._create_usage_bar(cpu_pct, 90)  # Warning at 90%
        
        print("💻 System Resources:")
        print(f"  Memory: {memory_bar} {memory_pct:.1f}% ({latest_resources['memory_used']:.1f}GB/{latest_resources['memory_total']:.1f}GB)")
        print(f"  CPU:    {cpu_bar} {cpu_pct:.1f}%")
        
        # DeepSeek process info
        deepseek_processes = self._get_deepseek_processes()
        if deepseek_processes:
            print(f"  🧠 DeepSeek Processes: {len(deepseek_processes)}")
            for i, proc in enumerate(deepseek_processes[:3]):  # Show max 3
                print(f"    Process {i+1}: {proc['memory_mb']:.0f}MB RAM, {proc['cpu_percent']:.1f}% CPU")
        print()
    
    def _display_recent_activities(self):
        """Display recent system activities"""
        print("📋 Recent Activities:")
        
        # This would be populated from log files in a real implementation
        # For now, show placeholder activities based on current state
        recent_activities = self._get_recent_activities()
        
        for activity in recent_activities[-5:]:  # Last 5 activities
            timestamp = activity['timestamp'].strftime('%H:%M:%S')
            print(f"  [{timestamp}] {activity['message']}")
        
        if not recent_activities:
            print("  No recent activities")
        print()
    
    def _display_milestones(self):
        """Display progress milestones and targets"""
        if not self.generation_stats:
            return
            
        best_performance = max([gs.best_performance for gs in self.generation_stats.values()])
        latest_gen = max(self.generation_stats.keys())
        
        milestones = [
            (20, 45.0, "Early specialization"),
            (40, 50.0, "Tool mastery"),
            (60, 55.0, "Advanced tactics"),
            (80, 60.0, "Success criteria")
        ]
        
        print("🎯 Milestones & Targets:")
        for target_gen, target_perf, description in milestones:
            if latest_gen >= target_gen:
                status = "✅" if best_performance >= target_perf else "❌"
                print(f"  Gen {target_gen:2d}: {target_perf}% {description} {status}")
            else:
                print(f"  Gen {target_gen:2d}: {target_perf}% {description} (pending)")
        print()
    
    def _load_archive_data(self):
        """Load data from archive directory"""
        if not self.archive_dir.exists():
            return
            
        # Load generation state if it exists
        gen_state_file = self.archive_dir / "generation_state.json"
        if gen_state_file.exists():
            try:
                with open(gen_state_file, 'r') as f:
                    gen_state = json.load(f)
                    
                # Update generation stats
                current_gen = gen_state.get('generation', 0)
                if current_gen not in self.generation_stats:
                    self.generation_stats[current_gen] = GenerationStats(
                        generation=current_gen,
                        agents_created=gen_state.get('parallel_runs_completed', 0),
                        agents_succeeded=gen_state.get('parallel_runs_completed', 0),
                        best_performance=gen_state.get('best_performance', 0),
                        average_performance=gen_state.get('average_performance', 0),
                        tools_created_this_gen=0,
                        total_tools_created=gen_state.get('total_tools_created', 0),
                        duration=timedelta(seconds=0),
                        completed_at=None
                    )
            except Exception as e:
                pass  # Ignore errors loading generation state
        
        # Scan for agent directories
        for agent_dir in self.archive_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name.startswith('gen'):
                self._load_agent_data(agent_dir)
    
    def _load_agent_data(self, agent_dir: Path):
        """Load data for a single agent"""
        metadata_file = agent_dir / "metadata.json"
        if not metadata_file.exists():
            return
            
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            agent_id = metadata.get('agent_id', agent_dir.name)
            
            # Create or update agent metrics
            self.agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                generation=metadata.get('generation', 0),
                performance=metadata.get('performance', 0),
                legal_move_rate=metadata.get('legal_move_rate', 0),
                tool_usage_count=metadata.get('tool_usage_count', 0),
                tools_created=metadata.get('tools_created', []),
                parent_id=metadata.get('parent_id'),
                created_at=datetime.fromisoformat(metadata.get('created_at', datetime.now().isoformat())),
                status=metadata.get('status', 'unknown')
            )
        except Exception as e:
            pass  # Ignore errors loading agent data
    
    def _monitor_resources(self):
        """Background thread to monitor system resources"""
        while self.running:
            try:
                # Get system resource info
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                
                resource_info = {
                    'timestamp': datetime.now(),
                    'memory_total': memory.total / (1024**3),  # GB
                    'memory_used': memory.used / (1024**3),   # GB
                    'memory_percent': memory.percent,
                    'cpu_percent': cpu_percent
                }
                
                self.resource_history.append(resource_info)
                
                # Keep only last hour of data
                cutoff_time = datetime.now() - timedelta(hours=1)
                self.resource_history = [r for r in self.resource_history if r['timestamp'] > cutoff_time]
                
            except Exception as e:
                pass  # Ignore resource monitoring errors
            
            time.sleep(30)  # Check every 30 seconds
    
    def _get_deepseek_processes(self):
        """Get information about running DeepSeek processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    if proc.info['cmdline'] and any('deepseek' in str(arg).lower() for arg in proc.info['cmdline']):
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'memory_mb': proc.info['memory_info'].rss / (1024*1024),
                            'cpu_percent': proc.info['cpu_percent'] or 0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            pass
        
        return processes
    
    def _get_recent_activities(self):
        """Get recent system activities (placeholder)"""
        # In a real implementation, this would parse log files
        activities = []
        
        # Generate some sample activities based on current state
        now = datetime.now()
        
        if self.agent_metrics:
            latest_agent = max(self.agent_metrics.values(), key=lambda a: a.created_at)
            activities.append({
                'timestamp': latest_agent.created_at,
                'message': f"✅ Agent {latest_agent.agent_id} created (gen {latest_agent.generation})"
            })
            
            if latest_agent.tools_created:
                activities.append({
                    'timestamp': latest_agent.created_at + timedelta(minutes=5),
                    'message': f"🔨 Tool created: {latest_agent.tools_created[-1]}"
                })
        
        return sorted(activities, key=lambda a: a['timestamp'])
    
    def _create_usage_bar(self, percent: float, warning_threshold: float = 80) -> str:
        """Create a visual usage bar"""
        bar_length = 20
        filled_length = int(bar_length * percent / 100)
        
        # Choose color based on usage level
        if percent >= warning_threshold:
            fill_char = '🔴'
        elif percent >= warning_threshold * 0.7:
            fill_char = '🟡'
        else:
            fill_char = '🟢'
        
        bar = fill_char * min(filled_length, bar_length) + '░' * (bar_length - filled_length)
        return f"|{bar}|"
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format a duration for display"""
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

def main():
    """Main function to run the dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DGM-Chess Evolution Monitor")
    parser.add_argument('--archive-dir', default='archive', help='Archive directory path')
    parser.add_argument('--refresh-rate', type=int, default=5, help='Dashboard refresh rate in seconds')
    
    args = parser.parse_args()
    
    monitor = DGMChessMonitor(archive_dir=args.archive_dir, refresh_rate=args.refresh_rate)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
