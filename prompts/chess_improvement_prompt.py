# chess_improvement_prompt.py - Enhanced improvement prompt generator with success/failure analysis

def get_chess_improvement_prompt(agent_code, puzzle_log, failed_puzzles, puzzle_solutions, evaluation_results, entry=None):
    """Generate a prompt for agent self-improvement"""

    # Prepare performance statistics
    performance_stats = evaluation_results.get('stage1', {})
    accuracy = performance_stats.get('accuracy', 0)
    legal_rate = performance_stats.get('legal_move_rate', 0)
    results = performance_stats.get('results', [])

    # Separate successes and failures
    successful_puzzles = [r for r in results if r.get('is_correct', False)]
    failed_puzzles_detailed = [r for r in results if not r.get('is_correct', False)]

    # Analyze success patterns
    success_summary = ""
    if successful_puzzles:
        success_themes = {}
        for puzzle in successful_puzzles:
            for theme in puzzle.get('themes', []):
                success_themes[theme] = success_themes.get(theme, 0) + 1
        success_summary = "Successful patterns:\n" + "\n".join([
            f"- {theme}: {count} puzzles solved"
            for theme, count in sorted(success_themes.items(), key=lambda x: x[1], reverse=True)
        ])
    else:
        success_summary = "No successful puzzles yet."

    # Analyze failure patterns
    failed_summary = ""
    if failed_puzzles:
        failure_themes = {}
        for puzzle in failed_puzzles[:10]:  # Show first 10
            themes = puzzle.get('themes', [])
            for theme in themes:
                failure_themes[theme] = failure_themes.get(theme, 0) + 1
            failed_summary += f"\n- Puzzle {puzzle['id']} (Rating: {puzzle.get('rating', 'unknown')})\n"
            failed_summary += f"  Themes: {', '.join(themes)}\n"
            failed_summary += f"  Agent suggested: {puzzle.get('agent_move', 'None')}\n"
            failed_summary += f"  Agent reasoning: {puzzle.get('agent_reasoning', 'No reasoning provided')[:200]}\n"

        if len(failed_puzzles) > 10:
            failed_summary += f"\n... and {len(failed_puzzles) - 10} more failed puzzles"

        failure_theme_summary = "\nMost common failure themes:\n" + "\n".join([
            f"- {theme}: {count} failures"
            for theme, count in sorted(failure_themes.items(), key=lambda x: x[1], reverse=True)[:5]
        ])
        failed_summary += failure_theme_summary
    else:
        failed_summary = "No failures to analyze."

    # Format successful puzzles
    success_details = _format_successful_puzzles(successful_puzzles[:5])

    improvement_focus = ""
    if entry == 'solve_illegal_moves':
        improvement_focus = "\n## PRIORITY FOCUS: Fix illegal move suggestions\nThe agent is suggesting illegal moves. Analyze WHY and fix the root cause.\n"
    elif entry == 'solve_stochasticity':
        improvement_focus = "\n## PRIORITY FOCUS: Improve consistency\nThe agent's performance varies. Make the analysis process more reliable and systematic.\n"
    elif isinstance(entry, dict) and 'puzzle_id' in entry:
        improvement_focus = f"\n## PRIORITY FOCUS: Solve puzzle {entry['puzzle_id']}\nSpecific themes: {', '.join(entry.get('themes', []))}\n"

    return f"""You are a meta-learning system that improves chess agents. Your role is to analyze an agent's performance and modify its code to perform better.

{improvement_focus}

=== AGENT PERFORMANCE SUMMARY ===

Overall Statistics:
- Accuracy: {accuracy:.1%} ({len(successful_puzzles)} correct out of {len(results)} total)
- Legal Move Rate: {legal_rate:.1%}
- Total Puzzles Evaluated: {len(results)}

{success_summary}

=== SUCCESSFUL PUZZLES (Learn from these!) ===
{success_details}

=== FAILED PUZZLES (Identify gaps!) ===
{failed_summary}

=== CURRENT AGENT CODE ===
{agent_code}

=== YOUR IMPROVEMENT TASK ===

As a self-improvement system, analyze BOTH successes and failures to identify how to improve the agent.

**STEP 1: PATTERN ANALYSIS**
Answer these questions:
1. What tactical patterns does the agent solve consistently? (from successes)
2. What tactical patterns does the agent fail on? (from failures)
3. Is there a gap in available tools? (e.g., no mate_finder but fails checkmate puzzles)
4. Is there a flaw in the reasoning process? (e.g., agent doesn't use tools correctly)

**STEP 2: ROOT CAUSE IDENTIFICATION**
Determine the PRIMARY reason for failures:
- TOOL_GAP: Agent lacks a tool for a specific pattern (e.g., no fork_detector)
- REASONING_FLAW: Agent has tools but doesn't use them correctly
- PROMPT_ISSUE: Instructions unclear about how to approach certain positions
- VALIDATION_ISSUE: Agent suggests illegal moves (not validating properly)

**STEP 3: DESIGN IMPROVEMENT**
Based on root cause, choose the best improvement approach:

**OPTION A: Create a New Tool** (when there's a consistent pattern gap)
When to use:
- Agent fails 3+ puzzles with same theme (e.g., "checkmate in 1")
- No existing tool addresses this pattern
- Tool would be reusable across many positions

Tool templates to consider:

MATE FINDER - Detects checkmate in 1:
```python
import chess

def tool_info():
    return {{
        'name': 'mate_finder',
        'description': 'Find moves that result in checkmate in 1 move',
        'input_schema': {{
            'type': 'object',
            'properties': {{'fen': {{'type': 'string', 'description': 'Board position in FEN notation'}}}},
            'required': ['fen']
        }}
    }}

def tool_function(fen):
    board = chess.Board(fen)
    mate_moves = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            mate_moves.append(move.uci())
        board.pop()
    return {{'mate_moves': mate_moves, 'found': len(mate_moves) > 0}}
```

FORK DETECTOR - Finds fork opportunities:
```python
import chess

def tool_info():
    return {{
        'name': 'fork_detector',
        'description': 'Detect moves that attack multiple opponent pieces (forks)',
        'input_schema': {{
            'type': 'object',
            'properties': {{'fen': {{'type': 'string'}}}},
            'required': ['fen']
        }}
    }}

def tool_function(fen):
    board = chess.Board(fen)
    forks = []
    for move in board.legal_moves:
        board.push(move)
        piece = board.piece_at(move.to_square)
        if piece:
            attacked = [sq for sq in board.attacks(move.to_square)
                       if board.piece_at(sq) and board.piece_at(sq).color != piece.color]
            if len(attacked) >= 2:
                forks.append({{'move': move.uci(), 'attacks_count': len(attacked)}})
        board.pop()
    return {{'forks': forks, 'found': len(forks) > 0}}
```

**OPTION B: Modify Agent Reasoning** (when process is flawed)
When to use:
- Agent has the right tools but uses them incorrectly
- Agent's step-by-step process is missing something
- Agent doesn't validate moves before outputting

**OPTION C: Enhance Existing Tool** (when tool exists but incomplete)
When to use:
- Agent has a tool for the pattern but it's not comprehensive
- Tool returns incomplete information

=== OUTPUT FORMAT ===

Provide your analysis as JSON. Follow this EXACT structure:

```json
{{
  "performance_analysis": {{
    "successful_patterns": ["pattern1", "pattern2"],
    "failed_patterns": ["pattern3", "pattern4"],
    "success_rate_by_theme": {{"theme1": 0.8, "theme2": 0.2}}
  }},
  "root_cause": {{
    "primary_issue": "TOOL_GAP | REASONING_FLAW | PROMPT_ISSUE | VALIDATION_ISSUE",
    "explanation": "Detailed explanation of why failures occur",
    "evidence": ["Failed puzzle X because...", "Failed puzzle Y because..."]
  }},
  "improvement_plan": {{
    "approach": "CREATE_TOOL | MODIFY_REASONING | ENHANCE_TOOL",
    "rationale": "Why this approach is best for the identified root cause"
  }},
  "implementation_steps": [
    {{
      "action": "create_tool | modify_code | enhance_tool",
      "target": "tools/mate_finder.py | chess_agent.py",
      "description": "Specific change to make",
      "code_snippet": "Exact code to add/modify"
    }}
  ],
  "expected_improvement": {{
    "target_puzzles": ["puzzle_id1", "puzzle_id2"],
    "estimated_accuracy_gain": "+15%",
    "reasoning": "Why this will help"
  }}
}}
```

=== CRITICAL REQUIREMENTS ===
1. Be SPECIFIC - provide exact code, not vague suggestions
2. Focus on ROOT CAUSE - don't just create tools randomly
3. Learn from SUCCESSES - understand what's already working
4. Provide EVIDENCE - reference specific failed puzzles
5. Make changes TESTABLE - clear success criteria

Your output will be parsed automatically, so use EXACT JSON format."""


def _format_successful_puzzles(puzzles):
    """Helper function to format successful puzzle details"""
    if not puzzles:
        return "None yet - agent hasn't solved any puzzles."

    formatted = []
    for p in puzzles:
        formatted.append(f"- Puzzle {p.get('puzzle_id', 'unknown')} (Rating: {p.get('rating', 'N/A')})")
        formatted.append(f"  Themes: {', '.join(p.get('themes', []))}")
        formatted.append(f"  Agent move: {p.get('suggested_move', 'N/A')}")
    return "\n".join(formatted)
