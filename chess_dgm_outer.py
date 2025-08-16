# chess_dgm_outer.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.parent_selection import ChessParentSelector
from utils.agent_management import ChessAgentManager
from evaluation.staged_evaluation import ChessStagedEvaluation
import json


class ChessDGMEvolution:
    def __init__(self, max_generations=80, parallel_agents=2):
        self.max_generations = max_generations
        self.parallel_agents = parallel_agents
        self.parent_selector = ChessParentSelector(k_parallel=parallel_agents)
        self.agent_manager = ChessAgentManager()
        self.evaluator = ChessStagedEvaluation()
        self.archive = []

        # Initialize with initial agent
        self.initialize_archive()

    def initialize_archive(self):
        """Create initial agent and add to archive"""
        initial_agent_id = "initial"
        self.agent_manager.create_initial_agent(f"archive/{initial_agent_id}")

        # Evaluate initial agent
        initial_agent = self.load_agent(initial_agent_id)
        initial_results = self.evaluator.evaluate_agent(initial_agent, initial_agent_id)

        self.archive.append({
            'agent_id': initial_agent_id,
            'performance': initial_results['final_performance'],
            'functioning_children_count': 0,
            'generation': 0,
            'evaluation_results': initial_results
        })

        print(f"Initial agent performance: {initial_results['final_performance']:.1%}")

    def run_evolution(self):
        """Main evolution loop"""

        for generation in range(1, self.max_generations + 1):
            print(f"\n=== Generation {generation} ===")

            # Select parents using paper-exact algorithm
            selected_parents = self.parent_selector.select_parents(self.archive)
            print(f"Selected parents: {selected_parents}")

            # Run parallel self-improvement
            new_agents = self.run_parallel_improvements(selected_parents, generation)

            # Evaluate new agents and update archive
            self.evaluate_and_update_archive(new_agents, generation)

            # Print generation summary
            self.print_generation_summary(generation)

            # Save generation state
            self.save_generation_state(generation)

    def run_parallel_improvements(self, selected_parents, generation):
        """Run self-improvement in parallel"""
        new_agents = []

        with ThreadPoolExecutor(max_workers=self.parallel_agents) as executor:
            futures = []

            for i, parent_id in enumerate(selected_parents):
                future = executor.submit(
                    self.improve_single_agent, parent_id, generation, i
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    new_agent_id = future.result(timeout=3600)  # 1 hour timeout
                    if new_agent_id:
                        new_agents.append(new_agent_id)
                        print(f"✅ Created improved agent: {new_agent_id}")
                    else:
                        print("❌ Agent improvement failed")
                except Exception as e:
                    print(f"❌ Agent improvement error: {e}")

        return new_agents

    def improve_single_agent(self, parent_id, generation, parallel_id):
        """Improve a single agent through self-modification"""

        # Create new agent from parent
        new_agent_id = self.agent_manager.create_new_agent(parent_id, generation, parallel_id)
        print(f"Created {new_agent_id} from parent {parent_id}")

        # Load the new agent
        new_agent = self.load_agent(new_agent_id)

        # Run self-improvement step
        from chess_self_improve import ChessSelfImprove
        improver = ChessSelfImprove()

        success = improver.self_improve_agent(new_agent_id, parent_id)

        if success:
            # Update parent's children count
            self.parent_selector.update_children_count(self.archive, parent_id, True)
            return new_agent_id
        else:
            # Cleanup failed agent
            import shutil
            shutil.rmtree(f"archive/{new_agent_id}", ignore_errors=True)
            self.parent_selector.update_children_count(self.archive, parent_id, False)
            return None

    def evaluate_and_update_archive(self, new_agents, generation):
        """Evaluate new agents and update archive"""

        for agent_id in new_agents:
            agent = self.load_agent(agent_id)
            evaluation_results = self.evaluator.evaluate_agent(agent, agent_id)

            # Add to archive
            self.archive.append({
                'agent_id': agent_id,
                'performance': evaluation_results['final_performance'],
                'functioning_children_count': 0,
                'generation': generation,
                'evaluation_results': evaluation_results
            })

            # Update agent's metadata file
            self.agent_manager.update_performance(
                agent_id,
                evaluation_results['final_performance'],
                evaluation_results
            )

            print(f"Agent {agent_id}: {evaluation_results['final_performance']:.1%} performance")

    def load_agent(self, agent_id):
        """Load agent from its directory"""
        from chess_agent import ChessAgent
        agent_dir = f"archive/{agent_id}"
        return ChessAgent(agent_dir=agent_dir)

    def print_generation_summary(self, generation):
        """Print summary of current generation"""
        current_gen_agents = [a for a in self.archive if a['generation'] == generation]
        all_performances = [a['performance'] for a in self.archive]

        print(f"\n--- Generation {generation} Summary ---")
        print(f"New agents created: {len(current_gen_agents)}")
        print(f"Archive size: {len(self.archive)}")
        print(f"Best performance: {max(all_performances):.1%}")
        print(f"Average performance: {sum(all_performances) / len(all_performances):.1%}")

        # Show top 3 agents
        top_agents = sorted(self.archive, key=lambda x: x['performance'], reverse=True)[:3]
        print("Top 3 agents:")
        for i, agent in enumerate(top_agents, 1):
            print(f"  {i}. {agent['agent_id']}: {agent['performance']:.1%}")

    def save_generation_state(self, generation):
        """Save current generation state"""
        state = {
            'generation': generation,
            'archive': self.archive,
            'timestamp': datetime.now().isoformat()
        }

        with open(f"generation_{generation}_state.json", 'w') as f:
            json.dump(state, f, indent=2)


if __name__ == "__main__":
    evolution = ChessDGMEvolution()
    evolution.run_evolution()