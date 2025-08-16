import os
import json
from tools import load_all_tools

def get_deepseek_tooluse_prompt():
    """
    Enhanced prompt for DeepSeek R1 using structured TOOL_CALL format.
    More token-efficient than including full Python code.
    """
    try:
        # Load tools and create JSON schemas
        all_tools = load_all_tools(logging=lambda x: None)  # Suppress logging
        
        available_tools = {}
        for tool in all_tools:
            tool_info = tool['info']
            available_tools[tool_info['name']] = {
                "description": tool_info['description'],
                "parameters": tool_info['input_schema']
            }
        
        tooluse_prompt = f"""You are an AI assistant with access to these tools:
{json.dumps(available_tools, indent=2)}

When you need to use a tool, respond with:
TOOL_CALL: {{"tool": "tool_name", "args": {{"param": "value"}}}}

Otherwise, respond normally. You can use multiple tools in sequence if needed.

Guidelines:
- Choose the most appropriate tool for each task
- Provide clear reasoning for your actions
- Handle errors gracefully and try alternative approaches
- For bash commands, be concise and avoid overly complex operations
- For file operations, use absolute paths when possible
"""
        
        return tooluse_prompt.strip()
        
    except Exception as e:
        # Fallback to basic prompt if tool loading fails
        return """You are an AI assistant with access to tools. When you need to use a tool, respond with:
TOOL_CALL: {"tool": "tool_name", "args": {"param": "value"}}

Available tools: bash, editor, chess_moves, chess_position, lichess_puzzle"""

def get_ollama_tooluse_prompt():
    """
    Alternative prompt format for Ollama models that prefer the <tool_use> XML format.
    Maintains compatibility with existing system.
    """
    try:
        # Load tools and create JSON schemas  
        all_tools = load_all_tools(logging=lambda x: None)
        
        available_tools = {}
        for tool in all_tools:
            tool_info = tool['info']
            available_tools[tool_info['name']] = {
                "description": tool_info['description'],
                "parameters": tool_info['input_schema']
            }
            
        tooluse_prompt = f"""You are an AI assistant with access to these tools:
{json.dumps(available_tools, indent=2)}

Use the available tools in this format:
<tool_use>
{{
    'tool_name': 'tool_name',
    'tool_input': {{'param': 'value'}}
}}
</tool_use>
"""
        return tooluse_prompt.strip()
        
    except Exception as e:
        return """You are an AI assistant with access to tools. Use this format:
<tool_use>
{'tool_name': 'tool_name', 'tool_input': {'param': 'value'}}
</tool_use>"""

if __name__ == "__main__":
    # Test the prompts
    print("=== DeepSeek Prompt ===")
    print(get_deepseek_tooluse_prompt())
    print("\n=== Ollama Prompt ===") 
    print(get_ollama_tooluse_prompt())
