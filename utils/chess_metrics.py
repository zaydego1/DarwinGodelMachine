import json
import os
from typing import Dict, List, Tuple


def load_agent_metadata(agent_id: str) -> Dict:
    metadata_path = f"archive/{agent_id}/metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return {}


def load_dgm_metadata(output_dir: str, last_only: bool = False) -> List[Dict]:
    dgm_metadata_path = os.path.join(output_dir, "dgm_metadata.jsonl")
    if not os.path.exists(dgm_metadata_path):
        return []

    with open(dgm_metadata_path, 'r') as f:
        content = f.read()

    json_entries = content.split('\n{')
    dgm_metadata = []

    for json_entry in json_entries:
        if not json_entry.strip():
            continue
        if not json_entry.startswith('{'):
            json_entry = '{' + json_entry
        try:
            metadata = json.loads(json_entry)
            dgm_metadata.append(metadata)
        except json.JSONDecodeError:
            continue

    if last_only and dgm_metadata:
        return [dgm_metadata[-1]]
    return dgm_metadata


def get_all_performance(output_dir: str = './output_dgm') -> Tuple[List[Dict], Dict]:
    dgm_metadata = load_dgm_metadata(output_dir)

    if not dgm_metadata:
        return [], {}

    all_agents = set()
    for gen_data in dgm_metadata:
        all_agents.update(gen_data.get('archive_snapshot', []))

    performance_results = []
    total_puzzles_solved = 0
    total_puzzles_evaluated = 0
    all_agent_ids = []

    for agent_id in all_agents:
        agent_meta = load_agent_metadata(agent_id)
        if not agent_meta:
            continue

        overall_perf = agent_meta.get('overall_performance', {})
        accuracy = overall_perf.get('accuracy_score', 0.0)
        puzzles_solved = overall_perf.get('total_puzzles_solved', 0)
        puzzles_evaluated = overall_perf.get('total_puzzles_evaluated', 0)

        total_puzzles_solved += puzzles_solved
        total_puzzles_evaluated += puzzles_evaluated
        all_agent_ids.append(agent_id)

        performance_results.append({
            'agent_id': agent_id,
            'accuracy_score': accuracy,
            'puzzles_solved': puzzles_solved,
            'puzzles_evaluated': puzzles_evaluated,
            **overall_perf
        })

    overall_performance = {
        'accuracy_score': total_puzzles_solved / total_puzzles_evaluated if total_puzzles_evaluated > 0 else 0,
        'total_puzzles_solved': total_puzzles_solved,
        'total_puzzles_evaluated': total_puzzles_evaluated,
        'total_agents': len(all_agent_ids),
        'agent_ids': all_agent_ids
    }

    return performance_results, overall_performance


def get_generation_trajectory(output_dir: str = './output_dgm') -> List[Dict]:
    dgm_metadata = load_dgm_metadata(output_dir)

    trajectory = []
    for gen_data in dgm_metadata:
        perf_stats = gen_data.get('performance_stats', {})
        trajectory.append({
            'generation': gen_data.get('generation'),
            'best_accuracy': perf_stats.get('best_accuracy', 0.0),
            'avg_accuracy': perf_stats.get('avg_accuracy', 0.0),
            'best_legal_rate': perf_stats.get('best_legal_rate', 0.0),
            'archive_size': gen_data.get('archive_size', 0),
            'unique_tools': len(perf_stats.get('unique_tools_created', [])),
            'duration_seconds': gen_data.get('duration_seconds', 0),
            'children_success_rate': gen_data.get('children_success_rate', 0.0)
        })

    return trajectory


def get_tool_evolution(output_dir: str = './output_dgm') -> Dict:
    dgm_metadata = load_dgm_metadata(output_dir)

    all_tools = []
    tool_frequency = {}

    for gen_data in dgm_metadata:
        perf_stats = gen_data.get('performance_stats', {})
        tools = perf_stats.get('unique_tools_created', [])
        all_tools.extend(tools)

    for tool in all_tools:
        tool_frequency[tool] = tool_frequency.get(tool, 0) + 1

    return {
        'total_unique_tools': len(set(all_tools)),
        'tools_by_frequency': dict(sorted(tool_frequency.items(), key=lambda x: x[1], reverse=True)),
        'total_tool_instances': len(all_tools)
    }


def get_parent_selection_stats(output_dir: str = './output_dgm') -> Dict:
    dgm_metadata = load_dgm_metadata(output_dir)

    parent_counts = {}
    total_selections = 0

    for gen_data in dgm_metadata:
        entries = gen_data.get('selfimprove_entries', [])
        for parent_id, _ in entries:
            parent_counts[parent_id] = parent_counts.get(parent_id, 0) + 1
            total_selections += 1

    return {
        'parent_selection_counts': dict(sorted(parent_counts.items(), key=lambda x: x[1], reverse=True)),
        'total_selections': total_selections,
        'unique_parents_selected': len(parent_counts)
    }


def is_compiled_agent(agent_id: str) -> bool:
    metadata = load_agent_metadata(agent_id)
    if not metadata:
        return False

    overall_perf = metadata.get('overall_performance', {})
    required_keys = ['accuracy_score', 'total_puzzles_evaluated', 'total_puzzles_solved']

    if not all(k in overall_perf for k in required_keys):
        return False

    if overall_perf.get('total_puzzles_evaluated', 0) == 0:
        return False

    if not overall_perf.get('stage1_passed', False):
        return False

    return True


def plot_performance_trajectory(output_dir: str = './output_dgm', save_path: str = None):
    """Plot performance trajectory over generations"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    except ImportError:
        print("matplotlib not available for plotting")
        return

    trajectory = get_generation_trajectory(output_dir)
    if not trajectory:
        print("No trajectory data available")
        return

    generations = [t['generation'] for t in trajectory]
    best_accs = [t['best_accuracy'] * 100 for t in trajectory]
    avg_accs = [t['avg_accuracy'] * 100 for t in trajectory]

    plt.figure(figsize=(10, 6))
    plt.plot(generations, best_accs, marker='o', label='Best Accuracy', linewidth=2)
    plt.plot(generations, avg_accs, marker='s', label='Avg Accuracy', linewidth=2)
    plt.xlabel('Generation')
    plt.ylabel('Accuracy (%)')
    plt.title('Performance Evolution Over Generations')
    plt.legend()
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.savefig(f"{output_dir}/performance_trajectory.png", dpi=300, bbox_inches='tight')

    plt.close()


def plot_tool_evolution(output_dir: str = './output_dgm', save_path: str = None):
    """Plot tool creation over time"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    except ImportError:
        print("matplotlib not available for plotting")
        return

    tool_evo = get_tool_evolution(output_dir)
    if not tool_evo or not tool_evo['tools_by_frequency']:
        print("No tool evolution data available")
        return

    tools = list(tool_evo['tools_by_frequency'].keys())[:10]  # Top 10
    freqs = [tool_evo['tools_by_frequency'][t] for t in tools]

    plt.figure(figsize=(10, 6))
    plt.barh(tools, freqs, color='steelblue')
    plt.xlabel('Frequency')
    plt.ylabel('Tool')
    plt.title('Most Frequently Created Tools')
    plt.grid(True, alpha=0.3, axis='x')

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.savefig(f"{output_dir}/tool_evolution.png", dpi=300, bbox_inches='tight')

    plt.close()


def plot_agent_comparison(agents: List[Dict], save_path: str = None):
    """Compare multiple agents visually"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
    except ImportError:
        print("matplotlib not available for plotting")
        return

    if not agents:
        return

    agent_ids = [a['agent_id'] for a in agents]
    accuracies = [a['accuracy'] * 100 for a in agents]

    plt.figure(figsize=(10, 6))
    plt.bar(agent_ids, accuracies, color='green')
    plt.xlabel('Agent ID')
    plt.ylabel('Accuracy (%)')
    plt.title('Agent Performance Comparison')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.savefig('agent_comparison.png', dpi=300, bbox_inches='tight')

    plt.close()
