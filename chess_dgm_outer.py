# chess_dgm_outer.py - Evolution with tool creation
import os
import json
import math
import random
import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import List, Dict, Any
from utils.agent_management import ChessAgentManager
from evaluation.staged_evaluation import ChessStagedEvaluation
from chess_self_improve import ChessSelfImprove


class ChessDGMEvolution:
    def __init__(self, max_generations=80, parallel_agents=2, use_enhanced_evaluation=False,
                 choose_method='score_child_prop', update_archive='keep_all', eval_noise=0.1,
                 output_dir='./output_dgm'):
        self.max_generations = max_generations
        self.parallel_agents = parallel_agents
        self.use_enhanced_evaluation = use_enhanced_evaluation
        self.choose_method = choose_method
        self.update_archive_method = update_archive
        self.eval_noise = eval_noise
        self.output_dir = output_dir
        self.agent_manager = ChessAgentManager()
        self.evaluator = ChessStagedEvaluation(stage1_count=5, stage2_count=10)

        self.archive = []
        self.generation_history = []
        self.tool_evolution_log = []
        self.initial_performance = None
        self.start_time = time.time()

        os.makedirs(output_dir, exist_ok=True)

        self.initialize_archive()

    def initialize_archive(self):
        initial_agent_id = "initial"
        self.agent_manager.create_initial_agent(f"archive/{initial_agent_id}")

        initial_agent = self.load_agent(initial_agent_id)
        initial_results = self.evaluator.evaluate_agent(initial_agent, initial_agent_id)

        archive_entry = {
            'agent_id': initial_agent_id,
            'performance': initial_results['final_performance'],
            'functioning_children_count': 0,
            'generation': 0,
            'evaluation_results': initial_results,
            'created_tools': self._extract_agent_tools(initial_agent_id),
            'mastered_themes': [],
            'total_failed_puzzles': self._count_failed_puzzles(initial_results)
        }

        self.archive.append(archive_entry)
        self.initial_performance = initial_results['final_performance']

        print(f"Initial agent performance: {initial_results['final_performance']:.1%}")
        print(f"Tools available: {len(archive_entry['created_tools'])}")

    def run_evolution(self):
        for generation in range(1, self.max_generations + 1):
            gen_start_time = time.time()
            print(f"\n=== Generation {generation} ===")

            selfimprove_entries = self.choose_selfimproves()
            print(f"Self-improve entries: {selfimprove_entries}")

            new_agents = self.run_parallel_improvements(selfimprove_entries, generation)

            new_agents_compiled = self.filter_compiled(new_agents)

            archive_before = len(self.archive)
            self.update_archive(new_agents_compiled, generation)
            archive_after = len(self.archive)

            self.print_generation_summary(generation)

            gen_duration = time.time() - gen_start_time
            self._save_generation_metadata(generation, selfimprove_entries, new_agents,
                                          new_agents_compiled, gen_duration)

            self.save_generation_state(generation)

            self._save_evolution_summary(generation)

    def choose_selfimproves(self):
        selfimprove_entries = []
        candidates = {}

        for entry in self.archive:
            commit = entry['agent_id']
            try:
                candidates[commit] = {
                    'performance': entry['performance'],
                    'children_count': entry['functioning_children_count'],
                    'total_failed_puzzles': entry.get('total_failed_puzzles', [])
                }
            except Exception as e:
                print(f"{commit} not eligible for being a parent: {e}")
                continue

        if self.choose_method == 'score_prop':
            commits = list(candidates.keys())
            scores = [candidates[commit]['performance'] for commit in commits]
            scores = [1 / (1 + math.exp(-10*(score-0.5))) for score in scores]
            probabilities = [score / sum(scores) for score in scores]
            parent_commits = random.choices(commits, probabilities, k=self.parallel_agents)
        elif self.choose_method == 'score_child_prop':
            commits = list(candidates.keys())
            scores = [candidates[commit]['performance'] for commit in commits]
            scores = [1 / (1 + math.exp(-10*(score-0.5))) for score in scores]
            children_counts = [candidates[commit]['children_count'] for commit in commits]
            children_counts = [1 / (1 + count) for count in children_counts]
            probabilities = [score * count for score, count in zip(scores, children_counts)]
            probabilities = [prob / sum(probabilities) for prob in probabilities]
            parent_commits = random.choices(commits, probabilities, k=self.parallel_agents)
        elif self.choose_method == 'best':
            sorted_commits = sorted(candidates, key=lambda x: candidates[x]['performance'])
            parent_commits = sorted_commits[:min(self.parallel_agents, len(sorted_commits))]
            if len(parent_commits) < self.parallel_agents:
                parent_commits.extend(random.choices(parent_commits, k=self.parallel_agents - len(parent_commits)))
        else:
            parent_commits = random.choices(list(candidates.keys()), k=self.parallel_agents)

        for parent_commit in parent_commits:
            failed_puzzles = candidates[parent_commit]['total_failed_puzzles']

            if len(failed_puzzles) >= 0.1 * 10 and random.random() < 0.25:
                entry = 'solve_illegal_moves'
                selfimprove_entries.append((parent_commit, entry))
                continue

            if random.random() < 0.25:
                entry = 'solve_stochasticity'
                selfimprove_entries.append((parent_commit, entry))
                continue

            if not failed_puzzles:
                entry = 'general_improvement'
            else:
                entry = random.choice(failed_puzzles)
            selfimprove_entries.append((parent_commit, entry))

        return selfimprove_entries

    def run_parallel_improvements(self, selfimprove_entries, generation):
        new_agents = []

        with ThreadPoolExecutor(max_workers=self.parallel_agents) as executor:
            futures = [
                executor.submit(
                    self.improve_single_agent, parent_id, entry, generation, i
                )
                for i, (parent_id, entry) in enumerate(selfimprove_entries)
            ]

            for future in as_completed(futures):
                try:
                    new_agent_id = future.result(timeout=5400)
                    if new_agent_id:
                        new_agents.append(new_agent_id)
                        print(f"✅ Created improved agent: {new_agent_id}")
                    else:
                        print("❌ Agent improvement failed")
                except TimeoutError:
                    print("❌ Agent improvement timed out")
                    future.cancel()
                except Exception as e:
                    import traceback
                    print(f"❌ Agent improvement error: {e}")
                    print(f"Traceback:\n{traceback.format_exc()}")

        return new_agents

    def improve_single_agent(self, parent_id, entry, generation, parallel_id):
        new_agent_id = self.agent_manager.create_new_agent(parent_id, generation, parallel_id)
        print(f"Created {new_agent_id} from parent {parent_id}")
        print(f"Improvement target: {entry}")

        improver = ChessSelfImprove(use_enhanced_evaluation=self.use_enhanced_evaluation)
        success = improver.self_improve_agent(new_agent_id, parent_id, entry)

        if success:
            for archive_entry in self.archive:
                if archive_entry['agent_id'] == parent_id:
                    archive_entry['functioning_children_count'] += 1
                    break

            if self.use_enhanced_evaluation:
                improvement_report = self._load_improvement_report(new_agent_id)
                if improvement_report:
                    self.tool_evolution_log.append({
                        'generation': generation,
                        'agent_id': new_agent_id,
                        'parent_id': parent_id,
                        'created_tools': improvement_report.get('created_tools', []),
                        'performance_delta': improvement_report.get('improvement_achieved', {}).get('performance_delta', 0)
                    })

            return new_agent_id
        else:
            import shutil
            shutil.rmtree(f"archive/{new_agent_id}", ignore_errors=True)
            return None

    def filter_compiled(self, run_ids):
        run_ids_compiled = []

        for run_id in run_ids:
            try:
                agent = self.load_agent(run_id)
                validation_results = self.evaluator.stage1_evaluation(agent)
                if validation_results['passes']:
                    run_ids_compiled.append(run_id)
                else:
                    print(f"{run_id} failed validation")
            except Exception as e:
                print(f"{run_id} not eligible: {e}")
                continue

        return run_ids_compiled

    def update_archive(self, new_ids, generation):
        if self.update_archive_method == 'keep_better':
            original_score = self.initial_performance - self.eval_noise
            for run_id in new_ids:
                agent = self.load_agent(run_id)
                evaluation_results = self.evaluator.evaluate_agent(agent, run_id)
                score = evaluation_results['final_performance']
                if score >= original_score:
                    parent_id = self._get_parent_id(run_id)
                    archive_entry = {
                        'agent_id': run_id,
                        'performance': score,
                        'functioning_children_count': 0,
                        'generation': generation,
                        'evaluation_results': evaluation_results,
                        'created_tools': self._extract_agent_tools(run_id),
                        'mastered_themes': [],
                        'total_failed_puzzles': self._count_failed_puzzles(evaluation_results),
                        'tool_diversity_score': len(set(self._extract_agent_tools(run_id)))
                    }
                    self.archive.append(archive_entry)

                    self._save_agent_metadata(run_id, parent_id, generation, evaluation_results)

                    self.agent_manager.update_performance(
                        run_id,
                        score,
                        evaluation_results
                    )

                    print(f"Agent {run_id}: {score:.1%} performance")
                    print(f"  Tools created: {archive_entry['created_tools']}")
                else:
                    print(f"Agent {run_id} rejected: {score:.1%} < {original_score:.1%}")
        else:
            for run_id in new_ids:
                agent = self.load_agent(run_id)
                evaluation_results = self.evaluator.evaluate_agent(agent, run_id)
                score = evaluation_results['final_performance']

                parent_id = self._get_parent_id(run_id)
                archive_entry = {
                    'agent_id': run_id,
                    'performance': score,
                    'functioning_children_count': 0,
                    'generation': generation,
                    'evaluation_results': evaluation_results,
                    'created_tools': self._extract_agent_tools(run_id),
                    'mastered_themes': [],
                    'total_failed_puzzles': self._count_failed_puzzles(evaluation_results),
                    'tool_diversity_score': len(set(self._extract_agent_tools(run_id)))
                }
                self.archive.append(archive_entry)

                self._save_agent_metadata(run_id, parent_id, generation, evaluation_results)

                self.agent_manager.update_performance(
                    run_id,
                    score,
                    evaluation_results
                )

                print(f"Agent {run_id}: {score:.1%} performance")
                print(f"  Tools created: {archive_entry['created_tools']}")

    def load_agent(self, agent_id):
        from chess_agent import ChessAgent
        agent_dir = f"archive/{agent_id}"
        return ChessAgent(agent_dir=agent_dir)

    def print_generation_summary(self, generation):
        current_gen_agents = [a for a in self.archive if a['generation'] == generation]
        all_performances = [a['performance'] for a in self.archive]

        print(f"\n--- Generation {generation} Summary ---")
        print(f"New agents created: {len(current_gen_agents)}")
        print(f"Archive size: {len(self.archive)}")
        print(f"Best performance: {max(all_performances):.1%}")
        print(f"Average performance: {sum(all_performances) / len(all_performances):.1%}")

        # Enhanced analysis if using enhanced evaluation
        if self.use_enhanced_evaluation:
            # Tool evolution analysis
            all_tools = []
            for agent in self.archive:
                all_tools.extend(agent.get('created_tools', []))
            unique_tools = set(all_tools)
            
            # Theme mastery analysis
            all_mastered_themes = []
            for agent in self.archive:
                all_mastered_themes.extend(agent.get('mastered_themes', []))
            unique_mastered_themes = set(all_mastered_themes)
            
            print(f"Tool diversity: {len(unique_tools)} unique tools")
            print(f"Theme coverage: {len(unique_mastered_themes)} themes mastered")

        top_agents = sorted(self.archive, key=lambda x: x['performance'], reverse=True)[:3]
        print("Top 3 agents:")
        for i, agent in enumerate(top_agents, 1):
            tools_str = ', '.join(agent.get('created_tools', [])[:3])
            if len(agent.get('created_tools', [])) > 3:
                tools_str += f" (+{len(agent.get('created_tools', [])) - 3} more)"
            print(f"  {i}. {agent['agent_id']}: {agent['performance']:.1%}")
            if self.use_enhanced_evaluation and tools_str:
                print(f"     Tools: [{tools_str}]")

    def save_generation_state(self, generation):
        state = {
            'generation': generation,
            'archive': self.archive,
            'generation_history': self.generation_history,
            'tool_evolution_log': self.tool_evolution_log,
            'timestamp': datetime.datetime.now().isoformat(),
            'use_enhanced_evaluation': self.use_enhanced_evaluation,
            'evolution_summary': {
                'total_agents_created': len(self.archive),
                'best_performance': max(agent['performance'] for agent in self.archive),
                'current_generation': generation
            }
        }
        
        # Add enhanced summary if enabled
        if self.use_enhanced_evaluation:
            state['evolution_summary'].update({
                'unique_tools_created': len(set(tool for agent in self.archive for tool in agent.get('created_tools', []))),
                'themes_mastered': len(set(theme for agent in self.archive for theme in agent.get('mastered_themes', []))),
            })

        with open(f"generation_{generation}_state.json", 'w') as f:
            json.dump(state, f, indent=2)

    def _count_failed_puzzles(self, evaluation_results):
        failed = []
        for stage_key in ['stage1', 'stage2']:
            if stage_key in evaluation_results:
                for result in evaluation_results[stage_key].get('results', []):
                    if not result.get('is_correct', False):
                        failed.append({
                            'puzzle_id': result.get('puzzle_id'),
                            'fen': result.get('fen'),
                            'themes': result.get('themes', [])
                        })
        return failed

    def _extract_mastered_themes(self, enhanced_results: Dict) -> List[str]:
        mastered_themes = []
        stage_results = enhanced_results.get('stage_results', {})

        for stage_name, stage_result in stage_results.items():
            theme_accuracies = stage_result.get('theme_accuracies', {})
            for theme, accuracy in theme_accuracies.items():
                if accuracy > 0.8:
                    mastered_themes.append(theme)

        return list(set(mastered_themes))

    def _extract_agent_tools(self, agent_id: str) -> List[str]:
        tool_registry_path = f"archive/{agent_id}/tool_registry.json"
        if os.path.exists(tool_registry_path):
            with open(tool_registry_path, 'r') as f:
                registry = json.load(f)
                return [tool['name'] for tool in registry.get('tools', [])]

        return []

    def _load_improvement_report(self, agent_id: str) -> Dict:
        report_path = f"archive/{agent_id}/improvement_report.json"
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                return json.load(f)

        return {}

    def _get_parent_id(self, agent_id: str) -> str:
        metadata_path = f"archive/{agent_id}/metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                return metadata.get('parent_agent_id', 'initial')
        return 'initial'

    def _save_agent_metadata(self, agent_id: str, parent_id: str, generation: int, evaluation_results: Dict):
        stage1 = evaluation_results.get('stage1', {})
        stage2 = evaluation_results.get('stage2', {})
        stage3 = evaluation_results.get('stage3', {})

        total_puzzles = 0
        total_solved = 0
        total_legal = 0
        failed_ids = []
        solved_ids = []

        if stage1:
            results = stage1.get('results', [])
            total_puzzles += len(results)
            for r in results:
                if r.get('is_legal'):
                    total_legal += 1
                if r.get('is_correct'):
                    total_solved += 1
                    solved_ids.append(r.get('puzzle_id'))
                else:
                    failed_ids.append(r.get('puzzle_id'))

        if stage2:
            results = stage2.get('results', [])
            total_puzzles += len(results)
            for r in results:
                if r.get('is_correct'):
                    total_solved += 1
                    solved_ids.append(r.get('puzzle_id'))
                else:
                    failed_ids.append(r.get('puzzle_id'))

        legal_rate = total_legal / total_puzzles if total_puzzles > 0 else 0
        accuracy = evaluation_results.get('final_performance', 0.0)

        metadata = {
            "agent_id": agent_id,
            "parent_agent_id": parent_id,
            "generation": generation,
            "creation_timestamp": datetime.datetime.now().isoformat(),

            "overall_performance": {
                "accuracy_score": accuracy,
                "legal_move_rate": legal_rate,
                "stage1_passed": stage1.get('passes', False) if stage1 else False,
                "stage2_accuracy": stage2.get('accuracy', 0.0) if stage2 else 0.0,
                "stage3_win_rate": stage3.get('win_rate') if stage3 else None,
                "total_puzzles_evaluated": total_puzzles,
                "total_puzzles_solved": total_solved,
                "total_legal_moves": total_legal,
                "failed_puzzle_ids": failed_ids,
                "solved_puzzle_ids": solved_ids
            },

            "tool_usage": {
                "tools_created": self._extract_agent_tools(agent_id),
                "tool_diversity_score": len(set(self._extract_agent_tools(agent_id)))
            },

            "evaluation_breakdown": {
                "stage1": stage1,
                "stage2": stage2,
                "stage3": stage3
            }
        }

        metadata_path = f"archive/{agent_id}/metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _save_generation_metadata(self, generation: int, selfimprove_entries: List,
                                  children_created: List[str], children_validated: List[str],
                                  duration_seconds: float):
        children_archived = [aid for aid in children_validated
                            if any(a['agent_id'] == aid for a in self.archive)]

        archive_snapshot = [a['agent_id'] for a in self.archive]

        all_performances = [a['performance'] for a in self.archive]
        all_legal_rates = []
        all_tools = []

        for agent in self.archive:
            eval_res = agent.get('evaluation_results', {})
            stage1 = eval_res.get('stage1', {})
            if stage1:
                all_legal_rates.append(stage1.get('legal_move_rate', 0))
            all_tools.extend(agent.get('created_tools', []))

        unique_tools = list(set(all_tools))

        metadata = {
            "generation": generation,
            "timestamp": datetime.datetime.now().isoformat(),
            "duration_seconds": duration_seconds,

            "selfimprove_entries": selfimprove_entries,

            "children_created": children_created,
            "children_validated": children_validated,
            "children_archived": children_archived,

            "archive_snapshot": archive_snapshot,
            "archive_size": len(archive_snapshot),

            "performance_stats": {
                "best_accuracy": max(all_performances) if all_performances else 0.0,
                "avg_accuracy": sum(all_performances) / len(all_performances) if all_performances else 0.0,
                "best_legal_rate": max(all_legal_rates) if all_legal_rates else 0.0,
                "archive_tool_count": len(all_tools),
                "unique_tools_created": unique_tools
            },

            "parent_selection_method": self.choose_method,
            "children_success_rate": len(children_validated) / len(children_created) if children_created else 0.0
        }

        dgm_metadata_path = os.path.join(self.output_dir, "dgm_metadata.jsonl")
        with open(dgm_metadata_path, 'a') as f:
            f.write(json.dumps(metadata, indent=2) + "\n")

    def _save_evolution_summary(self, current_generation: int):
        from utils.chess_metrics import get_generation_trajectory, get_tool_evolution, get_parent_selection_stats

        trajectory = get_generation_trajectory(self.output_dir)
        tool_evolution = get_tool_evolution(self.output_dir)
        parent_stats = get_parent_selection_stats(self.output_dir)

        all_performances = [a['performance'] for a in self.archive]
        all_legal_rates = []
        total_agents_created = 0
        total_agents_validated = 0
        total_agents_archived = len(self.archive)

        for agent in self.archive:
            eval_res = agent.get('evaluation_results', {})
            stage1 = eval_res.get('stage1', {})
            if stage1:
                all_legal_rates.append(stage1.get('legal_move_rate', 0))

        from utils.chess_metrics import load_dgm_metadata
        dgm_metadata = load_dgm_metadata(self.output_dir)
        for gen_data in dgm_metadata:
            total_agents_created += len(gen_data.get('children_created', []))
            total_agents_validated += len(gen_data.get('children_validated', []))

        best_agent = None
        if all_performances:
            best_idx = all_performances.index(max(all_performances))
            best_agent = {
                'agent_id': self.archive[best_idx]['agent_id'],
                'accuracy': self.archive[best_idx]['performance'],
                'generation': self.archive[best_idx]['generation']
            }

        total_duration = time.time() - self.start_time
        avg_improvement_time = sum(g['duration_seconds'] for g in trajectory) / len(trajectory) if trajectory else 0

        summary = {
            "current_generation": current_generation,
            "total_agents_created": total_agents_created,
            "total_agents_validated": total_agents_validated,
            "total_agents_archived": total_agents_archived,

            "best_agent": best_agent,

            "performance_trajectory": trajectory,

            "tool_evolution": tool_evolution,

            "efficiency_metrics": {
                "avg_improvement_time_seconds": avg_improvement_time,
                "validation_success_rate": total_agents_validated / total_agents_created if total_agents_created > 0 else 0.0,
                "archive_acceptance_rate": total_agents_archived / total_agents_validated if total_agents_validated > 0 else 0.0,
                "total_evolution_time_seconds": total_duration
            },

            "parent_selection_stats": parent_stats
        }

        summary_path = os.path.join(self.output_dir, "evolution_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)


def run_enhanced_chess_evolution(max_generations=80, parallel_agents=2, use_enhanced_evaluation=True,
                                choose_method='score_child_prop', update_archive='keep_all', eval_noise=0.1,
                                output_dir='./output_dgm'):
    evolution = ChessDGMEvolution(
        max_generations=max_generations,
        parallel_agents=parallel_agents,
        use_enhanced_evaluation=use_enhanced_evaluation,
        choose_method=choose_method,
        update_archive=update_archive,
        eval_noise=eval_noise,
        output_dir=output_dir
    )

    print(f"Starting Chess DGM Evolution")
    print(f"Max generations: {max_generations}")
    print(f"Parallel agents: {parallel_agents}")
    print(f"Enhanced evaluation: {use_enhanced_evaluation}")
    print(f"Parent selection method: {choose_method}")
    print(f"Archive update method: {update_archive}")
    if use_enhanced_evaluation:
        print("Tool creation enabled for LLM weakness compensation")

    evolution.run_evolution()

    return evolution


if __name__ == "__main__":
    evolution = run_enhanced_chess_evolution(max_generations=80, parallel_agents=2, use_enhanced_evaluation=True)
    print("Chess evolution complete!")
