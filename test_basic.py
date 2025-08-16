#!/usr/bin/env python3
"""
Basic functionality test for Chess DGM
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from chess_agent import ChessAgent

def test_basic_functionality():
    """Test basic chess agent functionality"""
    
    print("=== Chess DGM Basic Functionality Test ===\n")
    
    # Create agent
    print("1. Creating chess agent...")
    agent = ChessAgent()
    print("✅ Chess agent created successfully\n")
    
    # Test position: Opening position after 1.e4
    test_position = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    print(f"2. Testing with position: {test_position}")
    print("   (This is the position after 1.e4)\n")
    
    print("3. Running chess analysis...")
    try:
        result = agent.forward(test_position)
        print("✅ Analysis completed successfully!\n")
        
        print("=== AGENT RESPONSE ===")
        print(result)
        print("=== END RESPONSE ===\n")
        
        # Check if response contains expected elements
        if "BEST MOVE:" in result:
            print("✅ Agent provided a move recommendation")
        else:
            print("⚠️  Agent did not provide clear move recommendation")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("🎉 Basic functionality test PASSED!")
        print("\nNext steps:")
        print("- Run more complex position tests")
        print("- Implement puzzle evaluation")
        print("- Set up evolution pipeline")
    else:
        print("💥 Basic functionality test FAILED!")
        print("Check your DGM base files and model configuration")