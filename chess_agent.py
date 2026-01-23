# chess_agent.py - Enhanced version with tool creation capabilities
import os
import sys
sys.path.append(os.path.dirname(__file__))

from llm_withtools import chat_with_agent
from tools import load_all_tools

class ChessAgent:
    def __init__(self, model="qwen2.5-coder:32b", agent_dir=None):
        self.model = model
        self.agent_dir = agent_dir or "."
        self.conversation_history = []

    def forward(self, position_fen):
        """Analyze a chess position and suggest the best move"""

        import re
        import os
        fen_match = re.search(r'FEN:\s*([^\n]+)', position_fen)
        if fen_match:
            clean_fen = fen_match.group(1).strip()
        else:
            clean_fen = position_fen.strip()

        # Dynamically discover created tools
        created_tools_section = self._get_created_tools_section(clean_fen)

        instruction = f"""You are a chess puzzle solver. Your mission: analyze the position and find THE BEST MOVE.

=== PUZZLE ===
{position_fen}

=== YOUR OBJECTIVE ===
Find the single best move in this position through systematic analysis.

=== AVAILABLE TOOLS ===

**chess_position** - Analyze current position (material, threats, piece placement)
Example: TOOL_CALL: {{"tool": "chess_position", "args": {{"fen": "{clean_fen}", "analysis_type": "detailed"}}}}

**chess_moves** - Get all legal moves and validate specific moves
Example: TOOL_CALL: {{"tool": "chess_moves", "args": {{"fen": "{clean_fen}"}}}}

{created_tools_section}

=== SOLVING PROCESS ===

**STEP 1: GATHER POSITION DATA**
Use chess_position to understand:
- Material balance (who's ahead in pieces?)
- Threats (what pieces are attacking/attacked?)
- King safety (is either king vulnerable?)
- Positional factors

Example:
TOOL_CALL: {{"tool": "chess_position", "args": {{"fen": "{clean_fen}", "analysis_type": "detailed"}}}}

**STEP 2: GET AVAILABLE MOVES**
Use chess_moves to see all legal options:
TOOL_CALL: {{"tool": "chess_moves", "args": {{"fen": "{clean_fen}"}}}}

**STEP 3: IDENTIFY TACTICAL PATTERNS**
Based on the position data, ask yourself:
- Is there a checkmate in 1? (Look for moves that check the king with no escape)
- Is there a fork? (One piece attacking two valuable pieces)
- Is there a pin? (Piece can't move without exposing a more valuable piece)
- Is there a material win? (Can I capture something valuable?)
- Is there a defensive need? (Must I prevent opponent's threat?)

**STEP 4: USE SPECIALIZED TOOLS (if available)**
If you have tools for specific patterns, use them:
- mate_finder: Finds checkmate in 1 moves
- fork_detector: Identifies fork opportunities
- pin_detector: Finds pinned pieces
- [other created tools listed above]

**STEP 5: APPLY REASONING**
Combine tool results with logical deduction:
- Checkmate in 1 = ALWAYS the best move
- Win material without losing material = Usually excellent
- Fork winning a valuable piece = Strong tactical move
- Defensive move preventing mate = Critical if threatened

**STEP 6: VALIDATE YOUR ANSWER**
Before finalizing, ensure:
1. The move is legal (verify with chess_moves if uncertain)
2. The move addresses the puzzle's tactical theme
3. You're not missing a better forcing move

=== OUTPUT FORMAT ===

CRITICAL: Your final answer MUST use this EXACT format at the END of your response:

MOVE: [move_in_uci_or_san_notation]
REASONING: [Brief explanation of why this is the best move]

Examples of CORRECT format:

MOVE: Qh5#
REASONING: Checkmate - queen delivers mate on h5, king has no escape squares

MOVE: Nf7
REASONING: Fork - knight attacks queen on d8 and rook on h8 simultaneously

MOVE: Bxf7+
REASONING: Check wins material - bishop takes f7 with check, forcing king to move and winning the queen next

=== IMPORTANT REMINDERS ===
- Do NOT output multiple candidate moves - give ONE final answer
- Put your MOVE: statement at the VERY END after all analysis
- Use tool results to support your reasoning, don't guess
- The puzzle ALWAYS has a clear best move - find it systematically
- Stay focused on THIS puzzle - analyze and solve it using available tools
"""

        try:
            # Use enhanced tool system
            new_msg_history = chat_with_agent(
                msg=instruction,
                model=self.model,
                msg_history=self.conversation_history,
                logging=print
            )

            # Update conversation history
            self.conversation_history = new_msg_history

            # Extract the response
            if new_msg_history and len(new_msg_history) > 0:
                last_message = new_msg_history[-1]

                # Handle different response formats
                if isinstance(last_message, dict):
                    if 'content' in last_message:
                        content = last_message['content']

                        # Handle list format (Claude-style)
                        if isinstance(content, list) and len(content) > 0:
                            for content_block in content:
                                if isinstance(content_block, dict) and 'text' in content_block:
                                    return content_block['text']

                        # Handle string format
                        elif isinstance(content, str):
                            return content

                # Fallback: convert to string
                return str(last_message)

            return "No response generated"

        except Exception as e:
            return f"Error in chess analysis: {str(e)}"

    def _get_created_tools_section(self, clean_fen):
        import os
        import importlib.util

        tools_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")
        base_tools = ["chess_position.py", "chess_moves.py", "edit.py", "bash.py", "lichess_puzzle.py", "__init__.py"]

        created_tools = []

        # Find all Python files that aren't base tools
        if os.path.exists(tools_dir):
            for file in os.listdir(tools_dir):
                if file.endswith('.py') and file not in base_tools and not file.startswith('__'):
                    tool_path = os.path.join(tools_dir, file)

                    try:
                        # Load the tool module to get its info
                        spec = importlib.util.spec_from_file_location(file[:-3], tool_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        if hasattr(module, 'tool_info'):
                            tool_info = module.tool_info()
                            tool_name = tool_info.get('name', file[:-3])
                            tool_desc = tool_info.get('description', 'No description')

                            # Format the tool call example
                            tool_call = f'**{tool_name}** - {tool_desc}\nTOOL_CALL: {{"tool": "{tool_name}", "args": {{"fen": "{clean_fen}"}}}}\n'
                            created_tools.append(tool_call)
                    except Exception:
                        # Skip tools that can't be loaded
                        pass

        if created_tools:
            header = "=== PREVIOUSLY CREATED TOOLS (Use these first!) ===\n\n"
            return header + "\n".join(created_tools) + "\n"
        else:
            return ""

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []

if __name__ == "__main__":
    # Test the agent
    agent = ChessAgent()
    test_position = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    result = agent.forward(test_position)
    print("=== Chess Agent Test ===")
    print(result)
