# chess_self_improve.py - Combined traditional and enhanced self-improvement
import json
import os
from typing import Dict, List
from chess_agent import ChessAgent
from evaluation.staged_evaluation import ChessStagedEvaluation
from prompts.chess_improvement_prompt import get_chess_improvement_prompt


class ChessSelfImprove:
    def __init__(self, use_enhanced_evaluation=False):
        self.evaluator = ChessStagedEvaluation()
        self.use_enhanced_evaluation = use_enhanced_evaluation

    def self_improve_agent(self, agent_id, parent_id, entry=None):
        print(f"Self-improving agent {agent_id}")
        if entry:
            print(f"Target: {entry}")

        agent = ChessAgent(agent_dir=f"archive/{agent_id}")

        if self.use_enhanced_evaluation:
            return self._enhanced_self_improvement(agent, agent_id, parent_id, entry)
        else:
            return self._traditional_self_improvement(agent, agent_id, parent_id, entry)

    def _enhanced_self_improvement(self, agent, agent_id: str, parent_id: str, entry) -> bool:
        print(f"\n=== Self-Improvement for {agent_id} ===")
        print("Note: Agents will create tools as needed during problem-solving")

        return self._traditional_self_improvement(agent, agent_id, parent_id, entry)

    def _traditional_self_improvement(self, agent, agent_id: str, parent_id: str, entry) -> bool:
        evaluation_results = self.evaluator.evaluate_agent(agent, agent_id)

        if evaluation_results['stage1'] and not evaluation_results['stage1']['passes']:
            print(f"Agent {agent_id} failed basic functionality test")
            return False

        failed_puzzles, puzzle_solutions = self.collect_failure_data(evaluation_results)

        if not failed_puzzles:
            print(f"Agent {agent_id} has no failures to improve upon")
            return True

        return self._improve_with_traditional_method(agent_id, parent_id, evaluation_results, entry)

    def _improve_with_traditional_method(self, agent_id: str, parent_id: str, evaluation_results: Dict, entry) -> bool:
        failed_puzzles, puzzle_solutions = self.collect_failure_data(evaluation_results)

        if entry == 'solve_illegal_moves':
            target_puzzles = [p for p in failed_puzzles if not p.get('is_legal', True)]
            if not target_puzzles:
                target_puzzles = failed_puzzles
        elif entry == 'solve_stochasticity':
            target_puzzles = failed_puzzles
        elif entry == 'general_improvement':
            target_puzzles = failed_puzzles
        elif isinstance(entry, dict) and 'puzzle_id' in entry:
            target_puzzles = [p for p in failed_puzzles if p.get('id') == entry['puzzle_id']]
            if not target_puzzles:
                target_puzzles = failed_puzzles
        else:
            target_puzzles = failed_puzzles

        agent_code = self.load_agent_code(agent_id)
        puzzle_log = self.extract_puzzle_log(evaluation_results)

        improvement_prompt = get_chess_improvement_prompt(
            agent_code=agent_code,
            puzzle_log=puzzle_log,
            failed_puzzles=target_puzzles,
            puzzle_solutions=puzzle_solutions,
            evaluation_results=evaluation_results,
            entry=entry
        )

        try:
            from llm_withtools import chat_with_agent

            msg_history = chat_with_agent(
                msg=improvement_prompt,
                model="qwen2.5-coder:32b",
                msg_history=[],
                logging=lambda x: print(f"[SELF_IMPROVE] {x}") if "TOOL_CALL:" in x else None
            )

            improvement_response = self._extract_response_content(msg_history)
            improvement_plan = self.parse_improvement_response(improvement_response)

            if improvement_plan:
                return self.implement_improvements(agent_id, improvement_plan)
            else:
                print(f"Failed to parse improvement plan for {agent_id}")
                return False

        except Exception as e:
            print(f"Traditional self-improvement failed for {agent_id}: {e}")
            return False

    def _validate_improved_agent(self, agent_id: str) -> bool:
        print(f"Validating improved agent {agent_id}...")

        try:
            improved_agent = ChessAgent(agent_dir=f"archive/{agent_id}")

            validation_results = self.evaluator.stage1_evaluation(improved_agent)

            if validation_results['passes']:
                print(f"Agent {agent_id} successfully self-improved")
                return True
            else:
                print(f"Improved agent {agent_id} failed validation")
                return False

        except Exception as e:
            print(f"Validation failed for {agent_id}: {e}")
            return False

    def _extract_response_content(self, msg_history):
        if not msg_history:
            return "No response generated"

        last_msg = msg_history[-1]
        if isinstance(last_msg, dict) and 'content' in last_msg:
            content = last_msg['content']
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                response = ""
                for block in content:
                    if isinstance(block, dict) and 'text' in block:
                        response += block['text']
                return response

        return str(last_msg)
    def collect_failure_data(self, evaluation_results):
        failed_puzzles = []
        puzzle_solutions = []

        if evaluation_results.get('stage1'):
            for result in evaluation_results['stage1'].get('results', []):
                if not result.get('is_correct', False):
                    failed_puzzles.append({
                        'id': result.get('puzzle_id', 'unknown'),
                        'fen': result.get('fen', ''),
                        'agent_move': result.get('suggested_move', 'None'),
                        'agent_reasoning': result.get('agent_response', ''),
                        'rating': result.get('rating', 800),
                        'themes': result.get('themes', [])
                    })

        if evaluation_results.get('stage2'):
            for result in evaluation_results['stage2'].get('results', []):
                if not result.get('is_correct', False):
                    failed_puzzles.append({
                        'id': result.get('puzzle_id', 'unknown'),
                        'agent_move': result.get('suggested_move', 'None'),
                        'rating': result.get('rating', 900),
                        'themes': result.get('themes', [])
                    })

        for puzzle in failed_puzzles:
            solution = self.get_puzzle_solution(puzzle['id'])
            if solution:
                puzzle_solutions.append(solution)

        return failed_puzzles, puzzle_solutions

    def load_agent_code(self, agent_id):
        agent_dir = f"archive/{agent_id}"
        code_files = {}

        chess_agent_path = os.path.join(agent_dir, "chess_agent.py")
        if os.path.exists(chess_agent_path):
            with open(chess_agent_path, 'r') as f:
                code_files['chess_agent.py'] = f.read()

        tools_dir = os.path.join(agent_dir, "tools")
        if os.path.exists(tools_dir):
            for tool_file in os.listdir(tools_dir):
                if tool_file.endswith('.py'):
                    tool_path = os.path.join(tools_dir, tool_file)
                    with open(tool_path, 'r') as f:
                        code_files[f"tools/{tool_file}"] = f.read()

        code_output = ""
        for filename, content in code_files.items():
            code_output += f"\n# {filename}\n{content}\n"

        return code_output

    def parse_improvement_response(self, response):
        try:
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
        try:
            agent_dir = f"archive/{agent_id}"

            implementation_prompt = f"""
            Implement this chess improvement plan in your codebase:

            {improvement_plan.get('implementation_suggestion', '')}

            Modify the appropriate files to implement the suggested improvements.
            Focus on the specific changes described in the implementation suggestion.
            """

            agent = ChessAgent(agent_dir=agent_dir)
            agent.forward(implementation_prompt)

            return True

        except Exception as e:
            print(f"Failed to implement improvements: {e}")
            return False

    def get_puzzle_solution(self, puzzle_id):
        return {
            'id': puzzle_id,
            'moves': ['Nf3'],
            'explanation': 'Develop knight to control center',
            'key_pattern': 'Development'
        }

    def extract_puzzle_log(self, evaluation_results):
        log_entries = []

        if evaluation_results.get('stage1'):
            for result in evaluation_results['stage1'].get('results', []):
                log_entries.append(f"Puzzle {result.get('puzzle_id', 'unknown')}: {result.get('agent_response', 'No response')}")

        return "\n".join(log_entries)


def self_improve_agent(agent_id, parent_id, entry=None):
    improver = ChessSelfImprove(use_enhanced_evaluation=False)
    return improver.self_improve_agent(agent_id, parent_id, entry)


def self_improve_agent_traditional(agent_id, parent_id, entry=None):
    improver = ChessSelfImprove(use_enhanced_evaluation=False)
    return improver.self_improve_agent(agent_id, parent_id, entry)

