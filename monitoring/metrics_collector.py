#!/usr/bin/env python3
"""
Metrics Collection System for DGM-Chess Evolution

Automated collection and storage of performance metrics, tool usage patterns,
resource utilization, and evolution statistics.
"""

import json
import os
import sys
import time
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    timestamp: datetime
    agent_id: str
    generation: int
    stage1_accuracy: float
    stage2_accuracy: float
    legal_move_rate: float
    tool_usage_count: int
    tools_created: List[str]
    evaluation_duration: float

@dataclass
class ResourceMetric:
    """System resource measurement"""
    timestamp: datetime
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    cpu_percent: float
    deepseek_processes: int
    deepseek_memory_mb: float

@dataclass
class GenerationSummary:
    """Summary metrics for a complete generation"""
    generation: int
    start_time: datetime
    end_time: Optional[datetime]
    agents_created: int
    agents_succeeded: int
    agents_failed: int
    best_performance: float
    average_performance: float
    worst_performance: float
    tools_created_count: int
    unique_tools_created: List[str]
    total_evaluation_time: float

class MetricsCollector:
    """Main metrics collection and storage system"""
    
    def __init__(self, output_dir: str = "metrics", archive_dir: str = "archive"):
        self.output_dir = Path(output_dir)
        self.archive_dir = Path(archive_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "performance").mkdir(exist_ok=True)
        (self.output_dir / "resources").mkdir(exist_ok=True)
        (self.output_dir / "generations").mkdir(exist_ok=True)
        (self.output_dir / "exports").mkdir(exist_ok=True)
        
        self.start_time = datetime.now()
        
    def collect_performance_metrics(self, agent_id: str, evaluation_results: Dict) -> PerformanceMetric:
        """Collect performance metrics from agent evaluation"""
        
        # Extract metrics from evaluation results
        stage1_accuracy = evaluation_results.get('stage1', {}).get('accuracy', 0.0)
        stage2_accuracy = evaluation_results.get('stage2', {}).get('accuracy', 0.0) 
        legal_move_rate = evaluation_results.get('stage1', {}).get('legal_move_rate', 0.0)
        
        # Parse generation from agent_id
        generation = self._extract_generation(agent_id)
        
        # Count tool usage and creation
        tool_usage_count = evaluation_results.get('tool_usage_count', 0)
        tools_created = evaluation_results.get('tools_created', [])
        
        evaluation_duration = evaluation_results.get('evaluation_duration', 0.0)
        
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            agent_id=agent_id,
            generation=generation,
            stage1_accuracy=stage1_accuracy,
            stage2_accuracy=stage2_accuracy,
            legal_move_rate=legal_move_rate,
            tool_usage_count=tool_usage_count,
            tools_created=tools_created,
            evaluation_duration=evaluation_duration
        )
        
        # Save metric
        self._save_performance_metric(metric)
        
        return metric
    
    def collect_resource_metrics(self) -> ResourceMetric:
        """Collect current system resource metrics"""
        
        # Get system memory info
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get DeepSeek process info
        deepseek_processes = self._get_deepseek_processes()
        deepseek_count = len(deepseek_processes)
        deepseek_memory = sum(p['memory_mb'] for p in deepseek_processes)
        
        metric = ResourceMetric(
            timestamp=datetime.now(),
            memory_total_gb=memory.total / (1024**3),
            memory_used_gb=memory.used / (1024**3),
            memory_percent=memory.percent,
            cpu_percent=cpu_percent,
            deepseek_processes=deepseek_count,
            deepseek_memory_mb=deepseek_memory
        )
        
        # Save metric
        self._save_resource_metric(metric)
        
        return metric
    
    def collect_generation_summary(self, generation: int) -> GenerationSummary:
        """Collect summary metrics for a completed generation"""
        
        # Load all agent metrics for this generation
        agent_metrics = self._load_generation_agents(generation)
        
        if not agent_metrics:
            return None
            
        # Calculate summary statistics
        performances = [m.stage2_accuracy for m in agent_metrics]
        
        # Find generation timing
        start_time = min(m.timestamp for m in agent_metrics)
        end_time = max(m.timestamp for m in agent_metrics)
        
        # Count successes and failures
        succeeded = len([m for m in agent_metrics if m.stage2_accuracy > 0.2])  # Basic threshold
        failed = len(agent_metrics) - succeeded
        
        # Collect unique tools created
        all_tools = []
        for m in agent_metrics:
            all_tools.extend(m.tools_created)
        unique_tools = list(set(all_tools))
        
        summary = GenerationSummary(
            generation=generation,
            start_time=start_time,
            end_time=end_time,
            agents_created=len(agent_metrics),
            agents_succeeded=succeeded,
            agents_failed=failed,
            best_performance=max(performances) if performances else 0.0,
            average_performance=sum(performances) / len(performances) if performances else 0.0,
            worst_performance=min(performances) if performances else 0.0,
            tools_created_count=len(all_tools),
            unique_tools_created=unique_tools,
            total_evaluation_time=sum(m.evaluation_duration for m in agent_metrics)
        )
        
        # Save summary
        self._save_generation_summary(summary)
        
        return summary
    
    def export_csv_data(self) -> Dict[str, str]:
        """Export all metrics to CSV files for external analysis"""
        
        exports = {}
        
        # Export performance metrics
        performance_file = self.output_dir / "exports" / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._export_performance_csv(performance_file)
        exports['performance'] = str(performance_file)
        
        # Export resource metrics
        resource_file = self.output_dir / "exports" / f"resource_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._export_resource_csv(resource_file)
        exports['resources'] = str(resource_file)
        
        # Export generation summaries
        generation_file = self.output_dir / "exports" / f"generation_summaries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self._export_generation_csv(generation_file)
        exports['generations'] = str(generation_file)
        
        return exports
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """Get comprehensive evolution statistics"""
        
        stats = {
            'collection_start_time': self.start_time,
            'current_time': datetime.now(),
            'total_runtime': datetime.now() - self.start_time,
            'generations_completed': 0,
            'total_agents_created': 0,
            'total_agents_succeeded': 0,
            'best_overall_performance': 0.0,
            'average_performance_trend': [],
            'tools_created_count': 0,
            'unique_tools_created': [],
            'resource_usage_summary': {}
        }
        
        # Load all generation summaries
        generation_summaries = self._load_all_generation_summaries()
        
        if generation_summaries:
            stats['generations_completed'] = len(generation_summaries)
            stats['total_agents_created'] = sum(g.agents_created for g in generation_summaries)
            stats['total_agents_succeeded'] = sum(g.agents_succeeded for g in generation_summaries)
            stats['best_overall_performance'] = max(g.best_performance for g in generation_summaries)
            stats['average_performance_trend'] = [(g.generation, g.average_performance) for g in generation_summaries]
            
            # Collect all unique tools
            all_tools = []
            for g in generation_summaries:
                all_tools.extend(g.unique_tools_created)
            stats['unique_tools_created'] = list(set(all_tools))
            stats['tools_created_count'] = len(stats['unique_tools_created'])
        
        # Get recent resource usage
        recent_resources = self._load_recent_resource_metrics(hours=1)
        if recent_resources:
            stats['resource_usage_summary'] = {
                'avg_memory_percent': sum(r.memory_percent for r in recent_resources) / len(recent_resources),
                'max_memory_percent': max(r.memory_percent for r in recent_resources),
                'avg_cpu_percent': sum(r.cpu_percent for r in recent_resources) / len(recent_resources),
                'max_deepseek_processes': max(r.deepseek_processes for r in recent_resources),
                'avg_deepseek_memory_mb': sum(r.deepseek_memory_mb for r in recent_resources) / len(recent_resources)
            }
        
        return stats
    
    def _save_performance_metric(self, metric: PerformanceMetric):
        """Save performance metric to file"""
        
        # Create filename with timestamp
        filename = f"performance_{metric.timestamp.strftime('%Y%m%d_%H%M%S')}_{metric.agent_id}.json"
        filepath = self.output_dir / "performance" / filename
        
        # Convert to dict and save
        with open(filepath, 'w') as f:
            json.dump(self._metric_to_dict(metric), f, indent=2, default=str)
    
    def _save_resource_metric(self, metric: ResourceMetric):
        """Save resource metric to file"""
        
        # Create filename with timestamp
        filename = f"resources_{metric.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / "resources" / filename
        
        # Convert to dict and save
        with open(filepath, 'w') as f:
            json.dump(self._metric_to_dict(metric), f, indent=2, default=str)
    
    def _save_generation_summary(self, summary: GenerationSummary):
        """Save generation summary to file"""
        
        # Create filename
        filename = f"generation_{summary.generation:03d}_summary.json"
        filepath = self.output_dir / "generations" / filename
        
        # Convert to dict and save
        with open(filepath, 'w') as f:
            json.dump(self._metric_to_dict(summary), f, indent=2, default=str)
    
    def _export_performance_csv(self, filepath: Path):
        """Export performance metrics to CSV"""
        
        # Load all performance metrics
        metrics = []
        performance_dir = self.output_dir / "performance"
        
        if performance_dir.exists():
            for metric_file in performance_dir.glob("performance_*.json"):
                try:
                    with open(metric_file, 'r') as f:
                        metric_data = json.load(f)
                        metrics.append(metric_data)
                except Exception as e:
                    continue
        
        if not metrics:
            return
            
        # Write CSV header and data
        with open(filepath, 'w') as f:
            # Write header
            headers = ['timestamp', 'agent_id', 'generation', 'stage1_accuracy', 'stage2_accuracy', 
                      'legal_move_rate', 'tool_usage_count', 'tools_created_count', 'evaluation_duration']
            f.write(','.join(headers) + '\n')
            
            # Write data rows
            for metric in sorted(metrics, key=lambda x: x['timestamp']):
                row = [
                    metric['timestamp'],
                    metric['agent_id'],
                    str(metric['generation']),
                    str(metric['stage1_accuracy']),
                    str(metric['stage2_accuracy']),
                    str(metric['legal_move_rate']),
                    str(metric['tool_usage_count']),
                    str(len(metric.get('tools_created', []))),
                    str(metric['evaluation_duration'])
                ]
                f.write(','.join(row) + '\n')
    
    def _export_resource_csv(self, filepath: Path):
        """Export resource metrics to CSV"""
        
        # Load all resource metrics
        metrics = []
        resource_dir = self.output_dir / "resources"
        
        if resource_dir.exists():
            for metric_file in resource_dir.glob("resources_*.json"):
                try:
                    with open(metric_file, 'r') as f:
                        metric_data = json.load(f)
                        metrics.append(metric_data)
                except Exception as e:
                    continue
        
        if not metrics:
            return
            
        # Write CSV header and data
        with open(filepath, 'w') as f:
            # Write header
            headers = ['timestamp', 'memory_total_gb', 'memory_used_gb', 'memory_percent', 
                      'cpu_percent', 'deepseek_processes', 'deepseek_memory_mb']
            f.write(','.join(headers) + '\n')
            
            # Write data rows
            for metric in sorted(metrics, key=lambda x: x['timestamp']):
                row = [
                    metric['timestamp'],
                    str(metric['memory_total_gb']),
                    str(metric['memory_used_gb']),
                    str(metric['memory_percent']),
                    str(metric['cpu_percent']),
                    str(metric['deepseek_processes']),
                    str(metric['deepseek_memory_mb'])
                ]
                f.write(','.join(row) + '\n')
    
    def _export_generation_csv(self, filepath: Path):
        """Export generation summaries to CSV"""
        
        # Load all generation summaries
        summaries = self._load_all_generation_summaries()
        
        if not summaries:
            return
            
        # Write CSV header and data
        with open(filepath, 'w') as f:
            # Write header
            headers = ['generation', 'start_time', 'end_time', 'agents_created', 'agents_succeeded', 
                      'agents_failed', 'best_performance', 'average_performance', 'worst_performance',
                      'tools_created_count', 'unique_tools_count', 'total_evaluation_time']
            f.write(','.join(headers) + '\n')
            
            # Write data rows
            for summary in sorted(summaries, key=lambda x: x.generation):
                row = [
                    str(summary.generation),
                    str(summary.start_time),
                    str(summary.end_time or ''),
                    str(summary.agents_created),
                    str(summary.agents_succeeded),
                    str(summary.agents_failed),
                    str(summary.best_performance),
                    str(summary.average_performance),
                    str(summary.worst_performance),
                    str(summary.tools_created_count),
                    str(len(summary.unique_tools_created)),
                    str(summary.total_evaluation_time)
                ]
                f.write(','.join(row) + '\n')
    
    def _load_generation_agents(self, generation: int) -> List[PerformanceMetric]:
        """Load all agent metrics for a specific generation"""
        
        metrics = []
        performance_dir = self.output_dir / "performance"
        
        if not performance_dir.exists():
            return metrics
            
        for metric_file in performance_dir.glob("performance_*.json"):
            try:
                with open(metric_file, 'r') as f:
                    metric_data = json.load(f)
                    
                if metric_data.get('generation') == generation:
                    # Convert back to dataclass
                    metric = PerformanceMetric(
                        timestamp=datetime.fromisoformat(metric_data['timestamp']),
                        agent_id=metric_data['agent_id'],
                        generation=metric_data['generation'],
                        stage1_accuracy=metric_data['stage1_accuracy'],
                        stage2_accuracy=metric_data['stage2_accuracy'],
                        legal_move_rate=metric_data['legal_move_rate'],
                        tool_usage_count=metric_data['tool_usage_count'],
                        tools_created=metric_data['tools_created'],
                        evaluation_duration=metric_data['evaluation_duration']
                    )
                    metrics.append(metric)
            except Exception as e:
                continue
        
        return metrics
    
    def _load_all_generation_summaries(self) -> List[GenerationSummary]:
        """Load all generation summaries"""
        
        summaries = []
        generation_dir = self.output_dir / "generations"
        
        if not generation_dir.exists():
            return summaries
            
        for summary_file in generation_dir.glob("generation_*_summary.json"):
            try:
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
                    
                summary = GenerationSummary(
                    generation=summary_data['generation'],
                    start_time=datetime.fromisoformat(summary_data['start_time']),
                    end_time=datetime.fromisoformat(summary_data['end_time']) if summary_data.get('end_time') else None,
                    agents_created=summary_data['agents_created'],
                    agents_succeeded=summary_data['agents_succeeded'],
                    agents_failed=summary_data['agents_failed'],
                    best_performance=summary_data['best_performance'],
                    average_performance=summary_data['average_performance'],
                    worst_performance=summary_data['worst_performance'],
                    tools_created_count=summary_data['tools_created_count'],
                    unique_tools_created=summary_data['unique_tools_created'],
                    total_evaluation_time=summary_data['total_evaluation_time']
                )
                summaries.append(summary)
            except Exception as e:
                continue
        
        return summaries
    
    def _load_recent_resource_metrics(self, hours: int = 1) -> List[ResourceMetric]:
        """Load resource metrics from the last N hours"""
        
        metrics = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        resource_dir = self.output_dir / "resources"
        
        if not resource_dir.exists():
            return metrics
            
        for metric_file in resource_dir.glob("resources_*.json"):
            try:
                with open(metric_file, 'r') as f:
                    metric_data = json.load(f)
                    
                timestamp = datetime.fromisoformat(metric_data['timestamp'])
                if timestamp > cutoff_time:
                    metric = ResourceMetric(
                        timestamp=timestamp,
                        memory_total_gb=metric_data['memory_total_gb'],
                        memory_used_gb=metric_data['memory_used_gb'],
                        memory_percent=metric_data['memory_percent'],
                        cpu_percent=metric_data['cpu_percent'],
                        deepseek_processes=metric_data['deepseek_processes'],
                        deepseek_memory_mb=metric_data['deepseek_memory_mb']
                    )
                    metrics.append(metric)
            except Exception as e:
                continue
        
        return sorted(metrics, key=lambda x: x.timestamp)
    
    def _extract_generation(self, agent_id: str) -> int:
        """Extract generation number from agent ID"""
        
        if agent_id == 'initial':
            return 0
            
        # Parse gen{N}_agent{M}_{timestamp} format
        try:
            if agent_id.startswith('gen'):
                gen_part = agent_id.split('_')[0]  # Get 'gen{N}' part
                return int(gen_part[3:])  # Extract N from 'gen{N}'
        except (ValueError, IndexError):
            pass
            
        return 0
    
    def _get_deepseek_processes(self) -> List[Dict]:
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
    
    def _metric_to_dict(self, metric) -> Dict:
        """Convert metric dataclass to dictionary"""
        
        if hasattr(metric, '__dict__'):
            return {k: v for k, v in metric.__dict__.items()}
        else:
            return asdict(metric)

def main():
    """Main function for testing metrics collection"""
    
    collector = MetricsCollector()
    
    # Test resource collection
    print("Collecting resource metrics...")
    resource_metric = collector.collect_resource_metrics()
    print(f"Memory usage: {resource_metric.memory_percent:.1f}%")
    print(f"CPU usage: {resource_metric.cpu_percent:.1f}%")
    print(f"DeepSeek processes: {resource_metric.deepseek_processes}")
    
    # Test statistics
    print("\nEvolution statistics:")
    stats = collector.get_evolution_statistics()
    print(f"Runtime: {stats['total_runtime']}")
    print(f"Generations completed: {stats['generations_completed']}")
    
    # Test CSV export
    print("\nExporting CSV data...")
    exports = collector.export_csv_data()
    for data_type, filepath in exports.items():
        print(f"Exported {data_type} to: {filepath}")

if __name__ == "__main__":
    main()
