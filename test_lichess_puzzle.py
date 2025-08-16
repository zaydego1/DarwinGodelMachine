#!/usr/bin/env python3
"""Test script for lichess_puzzle tool"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.lichess_puzzle import tool_function, tool_info

def test_tool_info():
    """Test that tool info is properly formatted"""
    print("=" * 60)
    print("Testing Tool Info")
    print("=" * 60)
    
    info = tool_info()
    print("Tool Info:")
    print(f"Name: {info['name']}")
    print(f"Description: {info['description']}")
    print("Input Schema:", info['input_schema'])
    print()

def test_basic_puzzle_fetch():
    """Test basic puzzle fetching"""
    print("=" * 60)
    print("Testing Basic Puzzle Fetch (1 puzzle, rating 800-1200)")
    print("=" * 60)
    
    result = tool_function()
    print(result)
    print()

def test_multiple_puzzles():
    """Test fetching multiple puzzles"""
    print("=" * 60)
    print("Testing Multiple Puzzle Fetch (3 puzzles, rating 900-1100)")
    print("=" * 60)
    
    result = tool_function(rating_min=900, rating_max=1100, count=3)
    print(result)
    print()

def test_themed_puzzles():
    """Test fetching puzzles with specific themes"""
    print("=" * 60)
    print("Testing Themed Puzzle Fetch (tactics theme)")
    print("=" * 60)
    
    result = tool_function(rating_min=800, rating_max=1300, count=2, themes="tactics")
    print(result)
    print()

def test_high_rating_puzzles():
    """Test fetching higher rated puzzles"""
    print("=" * 60)
    print("Testing High Rating Puzzles (1200-1500)")
    print("=" * 60)
    
    result = tool_function(rating_min=1200, rating_max=1500, count=2)
    print(result)
    print()

def test_puzzle_tracking():
    """Test that puzzles are properly tracked to avoid repeats"""
    print("=" * 60)
    print("Testing Puzzle Tracking (repeated calls should not repeat puzzles)")
    print("=" * 60)
    
    print("First call:")
    result1 = tool_function(rating_min=800, rating_max=1200, count=2)
    print(result1)
    
    print("\nSecond call:")
    result2 = tool_function(rating_min=800, rating_max=1200, count=2)
    print(result2)
    
    print("\nThird call:")
    result3 = tool_function(rating_min=800, rating_max=1200, count=2)
    print(result3)
    print()

def check_database_files():
    """Check what database files were created"""
    print("=" * 60)
    print("Checking Database Files Created")
    print("=" * 60)
    
    import glob
    puzzle_files = glob.glob("puzzles_*.json")
    
    if puzzle_files:
        for file in puzzle_files:
            file_size = os.path.getsize(file)
            print(f"Database file: {file} (size: {file_size} bytes)")
    else:
        print("No puzzle database files found")
    
    # Check used puzzles file
    if os.path.exists("used_puzzles.json"):
        file_size = os.path.getsize("used_puzzles.json")
        print(f"Used puzzles file: used_puzzles.json (size: {file_size} bytes)")
    else:
        print("No used puzzles file found")
    
    print()

if __name__ == "__main__":
    print("Testing Lichess Puzzle Tool")
    print("This will create local database files and track puzzle usage")
    print()
    
    test_tool_info()
    test_basic_puzzle_fetch()
    test_multiple_puzzles()
    test_themed_puzzles()
    test_high_rating_puzzles()
    test_puzzle_tracking()
    check_database_files()
    
    print("All tests completed!")
    print("\nNote: The first run may take longer as it downloads/creates the puzzle database.")
    print("Subsequent runs should be faster using the cached puzzles.")
