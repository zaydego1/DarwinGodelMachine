#!/usr/bin/env python3
"""
Baseline Collection: DeepSeek R1 + Enhanced Tools (No Evolution)

This script collects baseline performance for DeepSeek R1 with the enhanced
tool integration system, but without evolution capabilities. This measures
the performance improvement from tool integration alone.
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.lichess_puzzle import get_lichess_puzzles
from llm_withtools import chat_with_agent
from monitoring.metrics_collector import MetricsCollector
import chess
import chess.engine

class EnhancedToolsBaselineCollector:
    """Collect baseline performance for DeepSeek R1 with enhanced tools"""
    
    def __init__(self, output_dir: str = "baselines"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics_collector = MetricsCollector()
        
    def collect_enhanced_tools_baseline(self, puzzle_count: int = 200, rating_range: tuple = (800, 1200)) -> Dict:
        """
        Collect baseline performance for DeepSeek R1 with enhanced tools
        
        Args:
            puzzle_count: Number of puzzles to test with
            rating_range: (min_rating, max_rating) for puzzles
            
        Returns:
            Dictionary containing baseline results
        """
        
        print(f"🎯 Collecting DeepSeek R1 + Enhanced Tools Baseline")
        print(f"📊 Testing {puzzle_count} puzzles (rating {rating_range[0]}-{rating_range[1]})")
        print("🔧 Configuration: Enhanced tools enabled, no evolution")
        print("🛠️ Available tools: chess_position, chess_moves, lichess_puzzle, bash, editor")
        print("="*80)
        
        start_time = datetime.now()
        results = {
            'configuration': 'deepseek_enhanced_tools',
            'model': 'deepseek-r1:14b',
            'tools_enabled': True,
            'available_tools': ['chess_position', 'chess_moves', 'lichess_puzzle', 'bash', 'editor'],
            'evolution_enabled': False,
            'test_start': start_time.isoformat(),
            'puzzle_count': puzzle_count,
            'rating_range': rating_range,
            'individual_results': [],
            'tool_usage_stats': {
                'total_tool_calls': 0,
                'tool_usage_by_type': {},
                'puzzles_using_tools': 0
            },
            'summary_stats': {}
        }
        
        # Get puzzles for testing
        print("📥 Fetching puzzles from Lichess...")
        puzzles = self._get_test_puzzles(puzzle_count, rating_range)
        
        if not puzzles:
            print("❌ Failed to fetch puzzles")
            return results
            
        print(f"✅ Fetched {len(puzzles)} puzzles")
        print("\n🧠 Starting chess analysis with enhanced tools...")
        
        # Test each puzzle
        correct_count = 0
        legal_move_count = 0
        total_response_time = 0
        total_tool_calls = 0
        puzzles_using_tools = 0
        tool_usage_by_type = {}
        
        for i, puzzle in enumerate(puzzles):
            print(f"\r⏳ Progress: {i+1}/{len(puzzles)} ({(i+1)/len(puzzles)*100:.1f}%)", end='', flush=True)
            
            puzzle_result = self._test_single_puzzle(puzzle)
            results['individual_results'].append(puzzle_result)
            
            # Update counters
            if puzzle_result['is_correct']:
                correct_count += 1
            if puzzle_result['is_legal_move']:
                legal_move_count += 1
            total_response_time += puzzle_result['response_time']
            
            # Track tool usage
            tool_calls = puzzle_result.get('tool_calls_made', [])
            if tool_calls:
                puzzles_using_tools += 1
                total_tool_calls += len(tool_calls)
                
                for tool_call in tool_calls:
                    tool_name = tool_call.get('tool_name', 'unknown')
                    tool_usage_by_type[tool_name] = tool_usage_by_type.get(tool_name, 0) + 1
            
            # Brief pause to avoid overwhelming the model
            time.sleep(0.1)
        
        print()  # New line after progress
        
        # Calculate summary statistics
        total_puzzles = len(puzzles)
        accuracy = correct_count / total_puzzles if total_puzzles > 0 else 0
        legal_move_rate = legal_move_count / total_puzzles if total_puzzles > 0 else 0
        avg_response_time = total_response_time / total_puzzles if total_puzzles > 0 else 0
        tool_usage_rate = puzzles_using_tools / total_puzzles if total_puzzles > 0 else 0
        avg_tools_per_puzzle = total_tool_calls / total_puzzles if total_puzzles > 0 else 0
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        results['summary_stats'] = {
            'total_puzzles': total_puzzles,
            'correct_answers': correct_count,
            'accuracy': accuracy,
            'legal_moves': legal_move_count,
            'legal_move_rate': legal_move_rate,
            'avg_response_time_seconds': avg_response_time,
            'total_duration_seconds': total_duration,
            'puzzles_per_minute': (total_puzzles / total_duration) * 60 if total_duration > 0 else 0
        }
        
        results['tool_usage_stats'] = {
            'total_tool_calls': total_tool_calls,
            'tool_usage_by_type': tool_usage_by_type,
            'puzzles_using_tools': puzzles_using_tools,
            'tool_usage_rate': tool_usage_rate,
            'avg_tools_per_puzzle': avg_tools_per_puzzle
        }
        
        results['test_end'] = end_time.isoformat()
        
        # Save results
        self._save_baseline_results(results)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _get_test_puzzles(self, count: int, rating_range: tuple) -> List[Dict]:
        """Fetch test puzzles from Lichess"""
        
        try:
            # Use our lichess_puzzle tool to get puzzles
            puzzles_data = get_lichess_puzzles(
                rating_min=rating_range[0],
                rating_max=rating_range[1],
                count=count,
                themes="tactics"  # Mixed themes for general baseline
            )
            
            if isinstance(puzzles_data, dict) and 'puzzles' in puzzles_data:
                return puzzles_data['puzzles']
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error fetching puzzles: {e}")
            return []
    
    def _test_single_puzzle(self, puzzle: Dict) -> Dict:
        """Test the enhanced tools system on a single puzzle"""
        
        start_time = time.time()
        
        # Create enhanced chess analysis prompt with tool instructions
        prompt = f"""You are analyzing a chess position with access to specialized chess tools. 
Find the best move for this puzzle.

Position (FEN): {puzzle['fen']}
Puzzle Rating: {puzzle.get('rating', 'Unknown')}
Themes: {', '.join(puzzle.get('themes', ['General']))}

Available tools:
- chess_position: Analyze the position for material, threats, and evaluation
- chess_moves: Generate and validate legal moves
- lichess_puzzle: Get additional puzzle information if needed

Use the tools strategically to analyze the position thoroughly, then provide your best move.

Response format:
Best move: [your move in algebraic notation]
Reasoning: [explain your analysis and why this move is best]
"""
        
        try:
            # Track tool calls made during this puzzle
            tool_calls_made = []
            
            def tool_logging(message):
                """Log tool calls for analysis"""
                if "TOOL_CALL:" in message:
                    try:
                        import json
                        import re
                        # Extract tool call information
                        tool_call_pattern = r'TOOL_CALL:\s*(\{.*?\})'
                        match = re.search(tool_call_pattern, message, re.DOTALL)
                        if match:
                            tool_data = json.loads(match.group(1))
                            tool_calls_made.append({
                                'tool_name': tool_data.get('tool', 'unknown'),
                                'args': tool_data.get('args', {}),
                                'timestamp': time.time()
                            })
                    except Exception:
                        pass
            
            # Get response from enhanced model with tools
            msg_history = chat_with_agent(
                msg=prompt,
                model="deepseek-r1:14b",
                msg_history=[],
                logging=tool_logging
            )
            
            # Get the final response
            if msg_history:
                response = msg_history[-1].get('content', '')
            else:
                response = ''
            
            response_time = time.time() - start_time
            
            # Extract suggested move from response
            suggested_move = self._extract_move_from_response(response, puzzle['fen'])
            
            # Check if move is legal
            is_legal_move = self._is_legal_move(suggested_move, puzzle['fen'])
            
            # Check if move is correct (in puzzle solution)
            correct_moves = puzzle.get('moves', [])
            is_correct = suggested_move in correct_moves if suggested_move else False
            
            return {
                'puzzle_id': puzzle.get('id', 'unknown'),
                'fen': puzzle['fen'],
                'rating': puzzle.get('rating'),
                'themes': puzzle.get('themes', []),
                'correct_moves': correct_moves,
                'suggested_move': suggested_move,
                'is_legal_move': is_legal_move,
                'is_correct': is_correct,
                'response_time': response_time,
                'tool_calls_made': tool_calls_made,
                'used_tools': len(tool_calls_made) > 0,
                'full_response': response[:1000],  # More space for tool-enhanced responses
                'error': None
            }
            
        except Exception as e:
            return {
                'puzzle_id': puzzle.get('id', 'unknown'),
                'fen': puzzle['fen'],
                'rating': puzzle.get('rating'),
                'themes': puzzle.get('themes', []),
                'correct_moves': puzzle.get('moves', []),
                'suggested_move': None,
                'is_legal_move': False,
                'is_correct': False,
                'response_time': time.time() - start_time,
                'tool_calls_made': [],
                'used_tools': False,
                'full_response': '',
                'error': str(e)
            }
    
    def _extract_move_from_response(self, response: str, fen: str) -> str:
        """Extract chess move from model response"""
        
        import re
        
        # Try to find move after "Best move:" pattern
        best_move_pattern = r'Best move:\s*([A-Za-z0-9+#=\-]+)'
        match = re.search(best_move_pattern, response, re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: look for common chess move patterns
        move_patterns = [
            r'\b([NBRQK]?[a-h]?[1-8]?x?[a-h][1-8](?:\=[NBRQ])?[+#]?)\b',  # Standard moves
            r'\b(O-O-O|O-O)\b',  # Castling
        ]
        
        for pattern in move_patterns:
            matches = re.findall(pattern, response)
            if matches:
                # Return the first plausible move found
                return matches[0]
        
        return None
    
    def _is_legal_move(self, move: str, fen: str) -> bool:
        """Check if a move is legal in the given position"""
        
        if not move:
            return False
            
        try:
            board = chess.Board(fen)
            
            # Try to parse the move
            try:
                chess_move = board.parse_san(move)
                return chess_move in board.legal_moves
            except ValueError:
                # Try parsing as UCI format
                try:
                    chess_move = chess.Move.from_uci(move)
                    return chess_move in board.legal_moves
                except ValueError:
                    return False
                    
        except Exception:
            return False
    
    def _save_baseline_results(self, results: Dict):
        """Save baseline results to file"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"deepseek_tools_baseline_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filepath}")
    
    def _print_summary(self, results: Dict):
        """Print summary of baseline collection"""
        
        stats = results['summary_stats']
        tool_stats = results['tool_usage_stats']
        config = results['configuration']
        
        print("\n" + "="*80)
        print("📊 ENHANCED TOOLS BASELINE SUMMARY")
        print("="*80)
        print(f"Configuration: {config}")
        print(f"Model: {results['model']}")
        print(f"Tools: {'Enabled' if results['tools_enabled'] else 'Disabled'}")
        print(f"Available Tools: {', '.join(results['available_tools'])}")
        print(f"Evolution: {'Enabled' if results['evolution_enabled'] else 'Disabled'}")
        print()
        print("🎯 PERFORMANCE RESULTS:")
        print(f"  Total Puzzles: {stats['total_puzzles']}")
        print(f"  Correct Answers: {stats['correct_answers']}")
        print(f"  Accuracy: {stats['accuracy']:.1%}")
        print(f"  Legal Moves: {stats['legal_moves']}")
        print(f"  Legal Move Rate: {stats['legal_move_rate']:.1%}")
        print()
        print("🔧 TOOL USAGE RESULTS:")
        print(f"  Puzzles Using Tools: {tool_stats['puzzles_using_tools']}/{stats['total_puzzles']}")
        print(f"  Tool Usage Rate: {tool_stats['tool_usage_rate']:.1%}")
        print(f"  Total Tool Calls: {tool_stats['total_tool_calls']}")
        print(f"  Avg Tools per Puzzle: {tool_stats['avg_tools_per_puzzle']:.1f}")
        
        if tool_stats['tool_usage_by_type']:
            print("  Tool Usage Breakdown:")
            for tool_name, count in sorted(tool_stats['tool_usage_by_type'].items()):
                percentage = (count / tool_stats['total_tool_calls']) * 100 if tool_stats['total_tool_calls'] > 0 else 0
                print(f"    {tool_name}: {count} calls ({percentage:.1f}%)")
        
        print()
        print("⏱️ TIMING RESULTS:")
        print(f"  Total Duration: {stats['total_duration_seconds']:.1f}s")
        print(f"  Avg Response Time: {stats['avg_response_time_seconds']:.2f}s")
        print(f"  Puzzles per Minute: {stats['puzzles_per_minute']:.1f}")
        print()
        
        # Performance assessment
        accuracy = stats['accuracy']
        legal_rate = stats['legal_move_rate']
        tool_usage = tool_stats['tool_usage_rate']
        
        print("🔍 ASSESSMENT:")
        if accuracy >= 0.45:
            print("  ✅ Accuracy: Excellent with tools (45%+)")
        elif accuracy >= 0.35:
            print("  ✅ Accuracy: Good improvement with tools (35-45%)")
        elif accuracy >= 0.25:
            print("  🟡 Accuracy: Some improvement with tools (25-35%)")
        else:
            print("  ❌ Accuracy: Limited improvement with tools (<25%)")
            
        if legal_rate >= 0.90:
            print("  ✅ Legal Move Rate: Excellent (90%+)")
        elif legal_rate >= 0.85:
            print("  ✅ Legal Move Rate: Good (85-90%)")
        else:
            print("  🟡 Legal Move Rate: Needs improvement (<85%)")
        
        if tool_usage >= 0.60:
            print("  ✅ Tool Usage: High utilization (60%+)")
        elif tool_usage >= 0.30:
            print("  🟡 Tool Usage: Moderate utilization (30-60%)")
        else:
            print("  ❌ Tool Usage: Low utilization (<30%)")
        
        print("="*80)

def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect DeepSeek R1 + Enhanced Tools baseline")
    parser.add_argument('--puzzles', type=int, default=200, help='Number of puzzles to test')
    parser.add_argument('--rating-min', type=int, default=800, help='Minimum puzzle rating')
    parser.add_argument('--rating-max', type=int, default=1200, help='Maximum puzzle rating')
    parser.add_argument('--output-dir', default='baselines', help='Output directory')
    
    args = parser.parse_args()
    
    collector = EnhancedToolsBaselineCollector(output_dir=args.output_dir)
    
    results = collector.collect_enhanced_tools_baseline(
        puzzle_count=args.puzzles,
        rating_range=(args.rating_min, args.rating_max)
    )
    
    print("\n🎉 Enhanced tools baseline collection completed!")
    print(f"📊 Accuracy: {results['summary_stats']['accuracy']:.1%}")
    print(f"⚖️ Legal Move Rate: {results['summary_stats']['legal_move_rate']:.1%}")
    print(f"🔧 Tool Usage Rate: {results['tool_usage_stats']['tool_usage_rate']:.1%}")

if __name__ == "__main__":
    main()
