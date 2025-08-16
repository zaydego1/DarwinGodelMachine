# chess_self_improve.py
import json
import os
from chess_agent import ChessAgent
from evaluation.staged_evaluation import ChessStagedEvaluation
from prompts.chess_improvement_prompt import get_chess_improvement_prompt


class ChessSelfImprove:
    def __init__(self):
        self.evaluator = ChessStagedEvaluation()

    def self_improve_agent(self, agent_id, parent_id):
        """Execute self-improvement for a chess agent"""

        print(f"Self-improving agent {agent_id}")

        # 1. Load the agent
        agent = ChessAgent(agent_dir=f"archive/{agent_id}")

        # 2. Evaluate current performance and identify failures
        evaluation_results = self.evaluator.evaluate_agent(agent, agent_id)

        if evaluation_results['stage1'] and not evaluation_results['stage1']['passes']:
            print(f"Agent {agent_id} failed basic functionality test")
            return False

        # 3. Collect failure data for improvement
        failed_puzzles, puzzle_solutions = self.collect_failure_data(evaluation_results)

        if not failed_puzzles:
            print(f"Agent {agent_id} has no failures to improve upon")
            return True  # Agent is already performing well

        # 4. Generate improvement prompt
        agent_code = self.load_agent_code(agent_id)
        puzzle_log = self.extract_puzzle_log(evaluation_results)

        improvement_prompt = get_chess_improvement_prompt(
            agent_code=agent_code,
            puzzle_log=puzzle_log,
            failed_puzzles=failed_puzzles,
            puzzle_solutions=puzzle_solutions,
            evaluation_results=evaluation_results
        )

        # 5. Agent self-modifies using enhanced tool system
        try:
            # Use the enhanced chat_with_agent function for better tool integration
            from llm_withtools import chat_with_agent
            
            # Create conversation with improvement prompt
            msg_history = chat_with_agent(
                msg=improvement_prompt,
                model="deepseek-r1:14b",
                msg_history=[],
                logging=lambda x: print(f"[SELF_IMPROVE] {x}") if "TOOL_CALL:" in x else None
            )
            
            # Extract the improvement response
            if msg_history:
                last_msg = msg_history[-1]
                if isinstance(last_msg, dict) and 'content' in last_msg:
                    improvement_response = last_msg['content']
                    if isinstance(improvement_response, str):
                        pass
                    elif isinstance(improvement_response, list):
                        # Handle Claude-style content blocks
                        improvement_response = ""
                        for block in improvement_response:
                            if isinstance(block, dict) and 'text' in block:
                                improvement_response += block['text']
                else:
                    improvement_response = str(last_msg)
            else:
                improvement_response = "No response generated"
            
            improvement_plan = self.parse_improvement_response(improvement_response)

            if not improvement_plan:
                print(f"Failed to parse improvement plan for {agent_id}")
                return False

            # 6. Implement the improvements
            success = self.implement_improvements(agent_id, improvement_plan)

            if not success:
                print(f"Failed to implement improvements for {agent_id}")
                return False

            # 7. Validate the improved agent still functions
            improved_agent = ChessAgent(agent_dir=f"archive/{agent_id}")
            validation_results = self.evaluator.stage1_evaluation(improved_agent)

            if validation_results['passes']:
                print(f"✅ Agent {agent_id} successfully self-improved")
                return True
            else:
                print(f"❌ Improved agent {agent_id} failed validation")
                return False

        except Exception as e:
            print(f"Self-improvement failed for {agent_id}: {e}")
            return False

    def collect_failure_data(self, evaluation_results):
        """Extract failed puzzles and their solutions"""
        failed_puzzles = []
        puzzle_solutions = []

        # Collect from Stage 1
        if evaluation_results['stage1']:
            for result in evaluation_results['stage1']['results']:
                if not result.get('is_correct', False):
                    failed_puzzles.append({
                        'id': result['puzzle_id'],
                        'fen': result.get('fen', ''),
                        'agent_move': result.get('suggested_move', 'None'),
                        'agent_reasoning': result.get('agent_response', ''),
                        'rating': result.get('rating', 800),
                        'themes': result.get('themes', [])
                    })

        # Collect from Stage 2
        if evaluation_results['stage2']:
            for result in evaluation_results['stage2']['results']:
                if not result.get('is_correct', False):
                    failed_puzzles.append({
                        'id': result['puzzle_id'],
                        'agent_move': result.get('suggested_move', 'None'),
                        'rating': result.get('rating', 900),
                        'themes': result.get('themes', [])
                    })

        # Get correct solutions for failed puzzles
        # This would query the puzzle database for the correct answers
        for puzzle in failed_puzzles:
            solution = self.get_puzzle_solution(puzzle['id'])
            if solution:
                puzzle_solutions.append(solution)

        return failed_puzzles, puzzle_solutions

    def load_agent_code(self, agent_id):
        """Load agent's current code for analysis"""
        agent_dir = f"archive/{agent_id}"
        code_files = {}

        # Read main agent file
        chess_agent_path = os.path.join(agent_dir, "chess_agent.py")
        if os.path.exists(chess_agent_path):
            with open(chess_agent_path, 'r') as f:
                code_files['chess_agent.py'] = f.read()

        # Read tool files
        tools_dir = os.path.join(agent_dir, "tools")
        if os.path.exists(tools_dir):
            for tool_file in os.listdir(tools_dir):
                if tool_file.endswith('.py'):
                    tool_path = os.path.join(tools_dir, tool_file)
                    with open(tool_path, 'r') as f:
                        code_files[f"tools/{tool_file}"] = f.read()

        # Format code for prompt
        code_output = ""
        for filename, content in code_files.items():
            code_output += f"\n# {filename}\n{content}\n"

        return code_output

    def parse_improvement_response(self, response):
        """Parse JSON improvement plan from agent response"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                improvement_plan = json.loads(json_str)
                return improvement_plan
            else:
                print("No JSON found in improvement response")
                return None
        except Exception as e:
            print(f"Failed to parse improvement response: {e}")
            return None

    def implement_improvements(self, agent_id, improvement_plan):
        """Implement the suggested improvements"""
        try:
            agent_dir = f"archive/{agent_id}"

            # The improvement implementation would depend on the specific suggestions
            # For now, we'll simulate by having the agent modify its own files

            implementation_prompt = f"""
            Implement this chess improvement plan in your codebase:

            {improvement_plan.get('implementation_suggestion', '')}

            Modify the appropriate files to implement the suggested improvements.
            Focus on the specific changes described in the implementation suggestion.
            """

            # Load agent and have it implement the changes
            agent = ChessAgent(agent_dir=agent_dir)
            agent.forward(implementation_prompt)

            return True

        except Exception as e:
            print(f"Failed to implement improvements: {e}")
            return False

    def get_puzzle_solution(self, puzzle_id):
        """Get correct solution for a puzzle"""
        # This would query the puzzle database
        # For now, return a placeholder
        return {
            'id': puzzle_id,
            'moves': ['Nf3'],  # Placeholder
            'explanation': 'Develop knight to control center',
            'key_pattern': 'Development'
        }

    def extract_puzzle_log(self, evaluation_results):
        """Extract puzzle-solving log from evaluation results"""
        log_entries = []

        if evaluation_results['stage1']:
            for result in evaluation_results['stage1']['results']:
                log_entries.append(f"Puzzle {result['puzzle_id']}: {result.get('agent_response', 'No response')}")

        return "\n".join(log_entries)
