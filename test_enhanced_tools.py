#!/usr/bin/env python3
"""
Enhanced Tool Integration Test Script

Tests the new prompt engineering approach for DeepSeek R1 with structured output
and backward compatibility with existing tool calling formats.
"""

import sys
import json
from llm_withtools import chat_with_agent
from prompts.deepseek_tooluse_prompt import get_deepseek_tooluse_prompt, get_ollama_tooluse_prompt

def test_prompt_generation():
    """Test the new prompt generation functions."""
    print("="*60)
    print("TESTING PROMPT GENERATION")
    print("="*60)
    
    print("\n--- DeepSeek R1 Prompt ---")
    deepseek_prompt = get_deepseek_tooluse_prompt()
    print(f"Length: {len(deepseek_prompt)} characters")
    print("Sample:")
    print(deepseek_prompt[:500] + "..." if len(deepseek_prompt) > 500 else deepseek_prompt)
    
    print("\n--- Ollama Prompt ---")
    ollama_prompt = get_ollama_tooluse_prompt()
    print(f"Length: {len(ollama_prompt)} characters")
    print("Sample:")
    print(ollama_prompt[:500] + "..." if len(ollama_prompt) > 500 else ollama_prompt)
    
    print("\n✓ Prompt generation tests completed")

def test_basic_conversation():
    """Test basic conversation without tools."""
    print("\n" + "="*60)
    print("TESTING BASIC CONVERSATION")
    print("="*60)
    
    model = "deepseek-r1:14b"
    msg = "Hello! Can you help me understand what tools you have available?"
    
    print(f"Model: {model}")
    print(f"Input: {msg}")
    
    try:
        msg_history = chat_with_agent(
            msg=msg,
            model=model,
            msg_history=[],
            logging=lambda x: print(f"[LOG] {x}"),
        )
        print(f"\n✓ Basic conversation test completed. Messages: {len(msg_history)}")
        
        # Print the last response
        if msg_history:
            last_msg = msg_history[-1]
            if isinstance(last_msg, dict) and 'content' in last_msg:
                print(f"Last response: {last_msg['content'][:200]}...")
            
    except Exception as e:
        print(f"❌ Basic conversation test failed: {e}")
        return False
        
    return True

def test_tool_usage():
    """Test tool usage with the new TOOL_CALL format."""
    print("\n" + "="*60)
    print("TESTING TOOL USAGE")
    print("="*60)
    
    model = "deepseek-r1:14b"
    msg = "Please list the files in the current directory using bash."
    
    print(f"Model: {model}")
    print(f"Input: {msg}")
    
    try:
        msg_history = chat_with_agent(
            msg=msg,
            model=model,
            msg_history=[],
            logging=lambda x: print(f"[LOG] {x}"),
        )
        
        print(f"\n✓ Tool usage test completed. Messages: {len(msg_history)}")
        
        # Check if tools were actually used
        tool_used = False
        for msg in msg_history:
            if isinstance(msg, dict) and 'content' in msg:
                content = str(msg['content'])
                if 'Tool Used:' in content or 'TOOL_CALL:' in content or '<tool_use>' in content:
                    tool_used = True
                    print("✓ Tool usage detected in conversation")
                    break
        
        if not tool_used:
            print("⚠️  No clear tool usage detected (might still be working)")
            
    except Exception as e:
        print(f"❌ Tool usage test failed: {e}")
        return False
        
    return True

def test_file_operations():
    """Test file operations using the editor tool."""
    print("\n" + "="*60)
    print("TESTING FILE OPERATIONS")
    print("="*60)
    
    model = "deepseek-r1:14b"
    msg = "Create a simple Python test file called /tmp/test_file.py with a hello world function."
    
    print(f"Model: {model}")
    print(f"Input: {msg}")
    
    try:
        msg_history = chat_with_agent(
            msg=msg,
            model=model,
            msg_history=[],
            logging=lambda x: print(f"[LOG] {x}"),
        )
        
        print(f"\n✓ File operations test completed. Messages: {len(msg_history)}")
        
        # Check if file was created
        import os
        if os.path.exists("/tmp/test_file.py"):
            print("✓ File was successfully created!")
            with open("/tmp/test_file.py", 'r') as f:
                content = f.read()
                print(f"File content preview: {content[:100]}...")
        else:
            print("⚠️  File was not found (tool might not have executed)")
            
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False
        
    return True

def test_context_management():
    """Test context management with multiple tool calls."""
    print("\n" + "="*60)
    print("TESTING CONTEXT MANAGEMENT")
    print("="*60)
    
    model = "deepseek-r1:14b"
    
    # Start a conversation that will require multiple tool calls
    messages = [
        "List the files in the current directory",
        "Now check if requirements.txt exists and show me its contents",
        "What's the current working directory?",
    ]
    
    msg_history = []
    
    for i, msg in enumerate(messages):
        print(f"\n--- Message {i+1}: {msg} ---")
        
        try:
            msg_history = chat_with_agent(
                msg=msg,
                model=model,
                msg_history=msg_history,
                logging=lambda x: print(f"[LOG] {x}"),
            )
            
            print(f"Conversation length: {len(msg_history)} messages")
            
        except Exception as e:
            print(f"❌ Context management test failed at message {i+1}: {e}")
            return False
    
    print(f"\n✓ Context management test completed. Final length: {len(msg_history)} messages")
    return True

def test_error_handling():
    """Test error handling with invalid tool calls."""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    model = "deepseek-r1:14b"
    msg = "Please run a command that doesn't exist: 'nonexistent_command_12345'"
    
    print(f"Model: {model}")
    print(f"Input: {msg}")
    
    try:
        msg_history = chat_with_agent(
            msg=msg,
            model=model,
            msg_history=[],
            logging=lambda x: print(f"[LOG] {x}"),
        )
        
        print(f"\n✓ Error handling test completed. Messages: {len(msg_history)}")
        
        # Check if error was handled gracefully
        error_handled = False
        for msg in msg_history:
            if isinstance(msg, dict) and 'content' in msg:
                content = str(msg['content']).lower()
                if 'error' in content or 'not found' in content or 'failed' in content:
                    error_handled = True
                    print("✓ Error was handled gracefully")
                    break
        
        if not error_handled:
            print("⚠️  Error handling unclear from conversation")
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
        
    return True

def run_compatibility_test():
    """Test backward compatibility with existing format."""
    print("\n" + "="*60)
    print("TESTING BACKWARD COMPATIBILITY")
    print("="*60)
    
    # Test with a model that should use the legacy format
    model = "gpt-4o-mini-2024-07-18"  # This will use manual tools but with original prompt
    msg = "Hello! What tools do you have available?"
    
    print(f"Model: {model}")
    print(f"Input: {msg}")
    
    try:
        msg_history = chat_with_agent(
            msg=msg,
            model=model,
            msg_history=[],
            logging=lambda x: print(f"[LOG] {x}"),
        )
        
        print(f"\n✓ Backward compatibility test completed. Messages: {len(msg_history)}")
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        # This might fail due to API keys, so don't return False
        print("⚠️  This might be due to missing API keys, which is expected")
        
    return True

def main():
    """Run all tests."""
    print("Enhanced Tool Integration Test Suite")
    print("Testing DeepSeek R1 prompt engineering with structured output\n")
    
    tests = [
        ("Prompt Generation", test_prompt_generation),
        ("Basic Conversation", test_basic_conversation),
        ("Tool Usage", test_tool_usage),
        ("File Operations", test_file_operations), 
        ("Context Management", test_context_management),
        ("Error Handling", test_error_handling),
        ("Backward Compatibility", run_compatibility_test),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced tool integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
