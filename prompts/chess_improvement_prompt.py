# prompts/chess_improvement_prompt.py

def get_chess_improvement_prompt(agent_code, puzzle_log, failed_puzzles, puzzle_solutions, evaluation_results):
    """Generate chess-specific self-improvement prompt"""

    return f"""
# Chess Agent Summary
- **Main File**: `chess_agent.py`
- **Primary Class**: `ChessAgent`
- The `forward()` function is the central entry point for chess analysis.
- Prompts are located either within the `forward()` function or in the `prompts/` directory.

- **Tools**: `tools/`
- The `tools/` directory contains various tools that the chess agent can use to analyze positions and make moves.
- Each tool must have a `tool_info()` function returning JSON with 'name', 'description', and 'input_schema'.
- Each tool must have a `tool_function()` that takes the defined arguments and returns analysis as a string.
- Available tools: chess_position, chess_moves, lichess_puzzle, bash, editor

- **Chess Knowledge**: The agent should understand:
- Tactical patterns (pins, forks, skewers, discovered attacks)
- Basic opening principles (control center, develop pieces, king safety)
- Endgame fundamentals (basic checkmates, pawn promotion)
- Position evaluation (material, piece activity, king safety, pawn structure)

- **Additional Details**:
- The agent should systematically analyze positions before suggesting moves.
- Always verify moves are legal using the chess_moves tool.
- Focus on forcing moves (checks, captures, threats) in tactical positions.
- Look for tactical motifs systematically in each position.
- Do not use 'while True' loops in the agent's code.
- Update `requirements.txt` if new chess dependencies are needed.

Here is the current implementation of the chess agent:

# Chess Agent Implementation
----- Chess Agent Implementation Start -----
{agent_code}
----- Chess Agent Implementation End -----

Your task is to identify ONE detailed plan that would improve the agent's chess analysis ability.

Here is the log of the chess agent trying to solve puzzles but failing:

# Agent Puzzle Solving Log  
----- Agent Running Log Start -----
{puzzle_log}
----- Agent Running Log End -----

# Failed Puzzles
The chess puzzles that the agent failed to solve correctly:
----- Failed Puzzles Start -----
{format_failed_puzzles(failed_puzzles)}
----- Failed Puzzles End -----

# Correct Solutions
The correct solutions for the failed puzzles:
----- Correct Solutions Start -----
{format_puzzle_solutions(puzzle_solutions)}
----- Correct Solutions End -----

# Evaluation Results
The agent's overall performance on the puzzle set:
----- Evaluation Results Start -----
Total Puzzles: {evaluation_results.get('total_puzzles', 'N/A')}
Correct Solutions: {evaluation_results.get('correct_count', 'N/A')}
Accuracy: {evaluation_results.get('accuracy', 'N/A'):.1%}
Legal Move Rate: {evaluation_results.get('legal_move_rate', 'N/A'):.1%}
Average Rating of Failed Puzzles: {evaluation_results.get('avg_failed_rating', 'N/A')}
Most Common Failed Themes: {evaluation_results.get('common_failed_themes', 'N/A')}
----- Evaluation Results End -----

Respond precisely in the following format including the JSON start and end markers:

```json
{{
    "log_summarization": "Analyze the above logs and summarize how the agent tried to solve the chess puzzles. Note which tools were used, the agent's analysis approach, what tactical patterns were missed, and any issues with move generation or position evaluation.",

    "potential_improvements": "Identify potential improvements to the chess agent that could enhance its chess analysis capabilities. Focus on general chess abilities (e.g., better tactical pattern recognition, improved position evaluation, enhanced move selection) rather than puzzle-specific fixes.",

    "improvement_proposal": "Choose ONE high-impact improvement from the identified potential improvements and describe it in detail. This should be a focused plan to enhance the agent's overall chess analysis ability, such as systematic tactical scanning, improved position evaluation, or better move prioritization.",

    "implementation_suggestion": "Referring to the chess agent's structure and tools, describe what specific code changes, new functions, or tool modifications would best implement the proposed improvement. Focus on practical implementation within the existing chess agent framework.",

    "problem_description": "Phrase the improvement proposal and implementation suggestion as a chess development task description. It should clearly describe what needs to be implemented so that the agent can modify its own code to improve its chess analysis capabilities."
}}
Your response will be automatically parsed, so ensure the JSON format is precise and valid.
"""


def format_failed_puzzles(failed_puzzles):
    """Format failed puzzles for the improvement prompt"""
    output = ""
    for i, puzzle in enumerate(failed_puzzles, 1):
        output += f"Failed Puzzle {i}:\n"
        output += f"ID: {puzzle['id']}\n"
        output += f"Rating: {puzzle['rating']}\n"
        output += f"Position: {puzzle['fen']}\n"
        output += f"Themes: {puzzle['themes']}\n"
        output += f"Agent's Move: {puzzle.get('agent_move', 'None/Invalid')}\n"
        output += f"Agent's Reasoning: {puzzle.get('agent_reasoning', 'N/A')}\n\n"
    return output

def format_puzzle_solutions(puzzle_solutions):
    """Format correct solutions for failed puzzles"""
    output = ""
    for i, solution in enumerate(puzzle_solutions, 1):
        output += f"Solution {i}:\n"
        output += f"Puzzle ID: {solution['id']}\n"
        output += f"Correct Move(s): {', '.join(solution['moves'])}\n"
        output += f"Explanation: {solution.get('explanation', 'Find the tactical motif')}\n"
        output += f"Key Pattern: {solution.get('key_pattern', 'Tactical combination')}\n\n"
    return output