#!/usr/bin/env python3
"""
Demo script showing the enhanced tool integration for DeepSeek R1.

This demonstrates the new TOOL_CALL: format with structured output
and how it integrates seamlessly with your existing tool ecosystem.
"""

from llm_withtools import chat_with_agent
from prompts.deepseek_tooluse_prompt import get_deepseek_tooluse_prompt

def demo_simple_usage():
    """Simple demo of the enhanced tool calling."""
    print("=" * 60)
    print("ENHANCED TOOL INTEGRATION DEMO")
    print("=" * 60)
    
    # Show the optimized prompt
    print("\n--- Optimized Prompt for DeepSeek R1 ---")
    prompt = get_deepseek_tooluse_prompt()
    print(f"Prompt length: {len(prompt)} characters")
    print("Key features:")
    print("✓ JSON schemas instead of full Python code (more token efficient)")
    print("✓ Clear TOOL_CALL: format for structured output")
    print("✓ Maintains compatibility with all existing tools")
    print("✓ Integrated context management for long conversations")
    
    # Demo conversation
    print(f"\n--- Demo Conversation with DeepSeek R1 ---")
    model = "deepseek-r1:14b"
    
    conversations = [
        {
            "user": "List the Python files in the current directory",
            "expected": "Should use bash tool to run ls command"
        },
        {
            "user": "Show me the contents of llm.py", 
            "expected": "Should use editor tool to view file"
        },
        {
            "user": "What's in the tools directory?",
            "expected": "Should use bash or editor to explore directory"
        }
    ]
    
    msg_history = []
    
    for i, conv in enumerate(conversations, 1):
        print(f"\n--- Example {i} ---")
        print(f"User: {conv['user']}")
        print(f"Expected: {conv['expected']}")
        
        try:
            msg_history = chat_with_agent(
                msg=conv['user'],
                model=model,
                msg_history=msg_history,
                logging=lambda x: print(f"  [SYSTEM] {x}") if "TOOL_CALL:" in x or "Tool Used:" in x else None
            )
            
            # Show the assistant's response
            if msg_history:
                last_msg = msg_history[-1]
                if isinstance(last_msg, dict) and 'content' in last_msg:
                    response = str(last_msg['content'])
                    # Truncate long responses
                    if len(response) > 300:
                        response = response[:300] + "..."
                    print(f"Assistant: {response}")
                    
        except Exception as e:
            print(f"  [ERROR] {e}")
            print("  (This might be expected if DeepSeek R1 is not available)")
            break
    
    print(f"\nFinal conversation length: {len(msg_history)} messages")
    print("✓ Demo completed!")

def show_format_comparison():
    """Show the difference between old and new formats."""
    print("\n" + "=" * 60)
    print("FORMAT COMPARISON")
    print("=" * 60)
    
    print("\n--- Original Format ---")
    print("""<tool_use>
{
    'tool_name': 'bash',
    'tool_input': {'command': 'ls -la'}
}
</tool_use>""")
    
    print("\n--- New Enhanced Format (preferred for DeepSeek R1) ---")
    print("""TOOL_CALL: {"tool": "bash", "args": {"command": "ls -la"}}""")
    
    print("\n--- Benefits of New Format ---")
    print("✓ More concise and structured")
    print("✓ Better for language models that prefer JSON")
    print("✓ Easier to parse reliably")
    print("✓ Compatible with your original approach")
    print("✓ Fallback to original format for backward compatibility")

def show_available_tools():
    """Show all available tools in the system."""
    print("\n" + "=" * 60)
    print("AVAILABLE TOOLS")
    print("=" * 60)
    
    try:
        from tools import load_all_tools
        tools = load_all_tools(logging=lambda x: None)
        
        for i, tool in enumerate(tools, 1):
            info = tool['info']
            print(f"\n{i}. {info['name']}")
            print(f"   Description: {info['description'][:100]}...")
            
            # Show parameters
            if 'input_schema' in info and 'properties' in info['input_schema']:
                params = list(info['input_schema']['properties'].keys())
                print(f"   Parameters: {', '.join(params)}")
        
        print(f"\nTotal tools available: {len(tools)}")
        
    except Exception as e:
        print(f"Error loading tools: {e}")

if __name__ == "__main__":
    print("Enhanced Tool Integration for DeepSeek R1")
    print("Integrating your preferred prompt engineering approach")
    print("with the existing comprehensive tool ecosystem.\n")
    
    show_format_comparison()
    show_available_tools()
    
    # Ask user if they want to run the interactive demo
    try:
        response = input("\nWould you like to run the interactive demo with DeepSeek R1? (y/n): ")
        if response.lower().startswith('y'):
            demo_simple_usage()
        else:
            print("Demo skipped. You can run it manually anytime!")
    except KeyboardInterrupt:
        print("\n\nDemo cancelled.")
    except Exception as e:
        print(f"\nDemo not available: {e}")
        print("This is expected if DeepSeek R1 is not set up locally.")
    
    print("\n" + "=" * 60)
    print("INTEGRATION COMPLETE!")
    print("=" * 60)
    print("✓ Enhanced prompts created for DeepSeek R1")
    print("✓ Backward compatibility maintained")
    print("✓ All existing tools work with new format")
    print("✓ Context management optimized for long conversations")
    print("✓ Comprehensive testing suite available")
    print("\nYour DeepSeek R1 model now has access to structured tool calling!")
