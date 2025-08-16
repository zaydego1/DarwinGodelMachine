# chess_agent.py - Enhanced version with tool creation capabilities
import os
import sys
sys.path.append(os.path.dirname(__file__))

from llm_withtools import chat_with_agent
from tools import load_all_tools

class ChessAgent:
    def __init__(self, model="deepseek-r1:14b", agent_dir=None):
        self.model = model
        self.agent_dir = agent_dir or "."
        self.conversation_history = []
        
    def forward(self, position_fen):
        """Analyze a chess position and suggest the best move"""
        
        instruction = f"""
You are an advanced chess analysis agent with tool creation capabilities. Your goal is to become stronger at chess through intelligent analysis and tool development.

IMPORTANT CAPABILITIES:
- You are part of an evolving system of agents focused on chess improvement
- You have the power to create new tools using the 'editor' and 'bash' tools to enhance your chess analysis
- Think long-term: create sustainable, reusable tools for future chess positions
- Avoid overfitting to specific positions; build general-purpose chess tools
- You can create Python files in the tools/ directory that follow the tool format

CURRENT POSITION TO ANALYZE: {position_fen}

ANALYSIS STRATEGY:
1. First, use existing tools to analyze the position
2. Identify any gaps in your analysis capabilities 
3. If needed, create new specialized tools to strengthen your analysis
4. Provide comprehensive move analysis with concrete best move

Available tools include: chess_position, chess_moves, bash, editor, lichess_puzzle

IMPORTANT: Use the TOOL_CALL format for enhanced parsing:
TOOL_CALL: {{"tool": "tool_name", "args": {{"param": "value"}}}}

Begin your analysis now. Think strategically about both the position and your tools.
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
