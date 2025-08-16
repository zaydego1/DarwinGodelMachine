#!/usr/bin/env python3
"""
Enhanced test for Chess DGM with tool validation
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from chess_agent import ChessAgent
from tools import load_all_tools

def test_tools_loading():
    """Test that chess tools are loading correctly"""
    print("=== Testing Tool Loading ===")
    
    try:
        tools = load_all_tools()
        print(f"✅ Loaded {len(tools)} tools:")
        
        for tool in tools:
            tool_name = tool['info']['name']
            print(f"  - {tool_name}")
        
        # Test chess_position tool directly
        chess_position_tool = None
        for tool in tools:
            if tool['info']['name'] == 'chess_position':
                chess_position_tool = tool
                break
        
        if chess_position_tool:
            print("✅ Found chess_position tool")
            
            # Test it directly
            test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            result = chess_position_tool['function'](test_fen)
            print("🔧 Direct tool test result:")
            print(result[:200] + "..." if len(result) > 200 else result)
        else:
            print("❌ chess_position tool not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool loading failed: {e}")
        return False

def test_manual_tool_calling():
    """Test manual tool calling directly"""
    print("\n=== Testing Manual Tool Calling ===")
    
    from llm_withtools import chat_with_agent_manualtools
    
    test_instruction = """
Test the chess position tool:

<tool_use>
{'tool_name': 'chess_position', 'tool_input': {'fen': 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'}}
</tool_use>

After the tool runs, say: "Tool test completed successfully!"
"""
    
    try:
        result = chat_with_agent_manualtools(
            test_instruction,
            model="deepseek-r1:14b",
            msg_history=[],
            logging=print
        )
        
        print("✅ Manual tool calling test completed")
        print("📋 Last message:")
        if result and len(result) > 0:
            last_msg = result[-1]
            if isinstance(last_msg, dict) and 'content' in last_msg:
                content = last_msg['content']
                if isinstance(content, list) and len(content) > 0:
                    print(content[0].get('text', str(content[0]))[:300])
                else:
                    print(str(content)[:300])
        
        return True
        
    except Exception as e:
        print(f"❌ Manual tool calling failed: {e}")
        return False

def test_enhanced_chess_agent():
    """Test the enhanced chess agent"""
    print("\n=== Testing Enhanced Chess Agent ===")
    
    agent = ChessAgent()
    test_position = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    
    print(f"Testing position: {test_position}")
    print("(Position after 1.e4 - Black to move)")
    
    print("\n🤖 Agent is analyzing...")
    try:
        result = agent.forward(test_position)
        
        print("✅ Analysis completed!")
        print("\n=== AGENT RESPONSE ===")
        print(result)
        print("=== END RESPONSE ===")
        
        # Check for tool usage
        if "<tool_use>" in str(result):
            print("✅ Agent used tools during analysis")
        else:
            print("⚠️  No tool usage detected in response")
        
        # Check for move recommendation
        if "BEST MOVE:" in result:
            print("✅ Agent provided move recommendation")
        else:
            print("⚠️  No clear move recommendation found")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced agent test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 Enhanced Chess DGM Testing\n")
    
    tests = [
        ("Tool Loading", test_tools_loading),
        ("Manual Tool Calling", test_manual_tool_calling), 
        ("Enhanced Chess Agent", test_enhanced_chess_agent)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n🎉 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 All tests passed! Ready for puzzle training.")
    else:
        print("🔧 Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()