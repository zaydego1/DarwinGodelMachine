#!/usr/bin/env python3
"""
Baseline Collection: DeepSeek R1 Base Model (No Tools, No Evolution)

This script collects baseline performance for the bare DeepSeek R1 model
without any tools or evolution capabilities, to establish the foundation
performance level for comparison.
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
from llm import chat_with_model
from monitoring.metrics_collector import MetricsCollector
import chess
import chess.engine

class BaselineCollector:
    """Collect baseline performance for DeepSeek R1 without tools"""
    
    def __init__(self, output_dir: str = "baselines"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics_collector = MetricsCollector()
        
    def collect_base_model_baseline(self, puzzle_count: int = 200, rating_range: tuple = (800, 1200)) -> Dict:
        """
        Collect baseline performance for DeepSeek R1 base model
        
        Args:
            puzzle_count: Number of puzzles to test with
            rating_range: (min_rating, max_rating) for puzzles
            
        Returns:
            Dictionary containing baseline results
        """
        
        print(f"🎯 Collecting DeepSeek R1 Base Model Baseline")
        print(f"📊 Testing {puzzle_count} puzzles (rating {rating_range[0]}-{rating_range[1]})")
        print("🔧 Configuration: No tools, no evolution, basic chess analysis")
        print("="*80)
        
        start_time = datetime.now()
        results = {
            'configuration': 'deepseek_base_model',
            'model': 'deepseek-r1:14b',
            'tools_enabled': False,
            'evolution_enabled': False,
            'test_start': start_time.isoformat(),
            'puzzle_count': puzzle_count,
            'rating_range': rating_range,
            'individual_results': [],
            'summary_stats': {}
        }
        
        # Get puzzles for testing
        print("📥 Fetching puzzles from Lichess...")
        puzzles = self._get_test_puzzles(puzzle_count, rating_range)
        
        if not puzzles:
            print("❌ Failed to fetch puzzles")
            return results
            
        print(f"✅ Fetched {len(puzzles)} puzzles")
        print("\n🧠 Starting chess analysis with base DeepSeek R1...")
        
        # Test each puzzle
        correct_count = 0
        legal_move_count = 0
        total_response_time = 0
        
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
            
            # Brief pause to avoid overwhelming the model
            time.sleep(0.1)
        
        print()  # New line after progress
        
        # Calculate summary statistics
        total_puzzles = len(puzzles)
        accuracy = correct_count / total_puzzles if total_puzzles > 0 else 0
        legal_move_rate = legal_move_count / total_puzzles if total_puzzles > 0 else 0
        avg_response_time = total_response_time / total_puzzles if total_puzzles > 0 else 0
        
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
        """Test the base model on a single puzzle"""
        
        start_time = time.time()
        
        # Create basic chess analysis prompt (no tool instructions)
        prompt = f"""You are analyzing a chess position. Look at this position and find the best move.

Position (FEN): {puzzle['fen']}
Puzzle Rating: {puzzle.get('rating', 'Unknown')}

Analyze the position and provide your best move in standard algebraic notation (like Nf3, Qxd5, O-O, etc.).

Response format:
Best move: [your move here]
Reasoning: [brief explanation]
"""
        
        try:
            # Get response from base model (no tools)
            response = chat_with_model(
                msg=prompt,
                model="deepseek-r1:14b",
                msg_history=[],
                system_message="You are a chess analysis assistant. Analyze positions and suggest the best moves."
            )
            
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
                'full_response': response[:500],  # Truncate for storage
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
        filename = f"deepseek_base_baseline_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {filepath}")
    
    def _print_summary(self, results: Dict):
        """Print summary of baseline collection"""
        
        stats = results['summary_stats']
        config = results['configuration']
        
        print("\n" + "="*80)
        print("📊 BASELINE COLLECTION SUMMARY")
        print("="*80)
        print(f"Configuration: {config}")
        print(f"Model: {results['model']}")
        print(f"Tools: {'Enabled' if results['tools_enabled'] else 'Disabled'}")
        print(f"Evolution: {'Enabled' if results['evolution_enabled'] else 'Disabled'}")
        print()
        print("🎯 PERFORMANCE RESULTS:")
        print(f"  Total Puzzles: {stats['total_puzzles']}")
        print(f"  Correct Answers: {stats['correct_answers']}")
        print(f"  Accuracy: {stats['accuracy']:.1%}")
        print(f"  Legal Moves: {stats['legal_moves']}")
        print(f"  Legal Move Rate: {stats['legal_move_rate']:.1%}")
        print()
        print("⏱️ TIMING RESULTS:")
        print(f"  Total Duration: {stats['total_duration_seconds']:.1f}s")
        print(f"  Avg Response Time: {stats['avg_response_time_seconds']:.2f}s")
        print(f"  Puzzles per Minute: {stats['puzzles_per_minute']:.1f}")
        print()
        
        # Performance assessment
        accuracy = stats['accuracy']
        legal_rate = stats['legal_move_rate']
        
        print("🔍 ASSESSMENT:")
        if accuracy >= 0.30:
            print("  ✅ Accuracy: Above expected baseline (30%+)")
        elif accuracy >= 0.20:
            print("  🟡 Accuracy: Within expected range (20-30%)")
        else:
            print("  ❌ Accuracy: Below expected baseline (<20%)")
            
        if legal_rate >= 0.85:
            print("  ✅ Legal Move Rate: Good (85%+)")
        elif legal_rate >= 0.70:
            print("  🟡 Legal Move Rate: Acceptable (70-85%)")
        else:
            print("  ❌ Legal Move Rate: Poor (<70%)")
        
        print("="*80)

def main():
    """Main function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect DeepSeek R1 base model baseline")
    parser.add_argument('--puzzles', type=int, default=200, help='Number of puzzles to test')
    parser.add_argument('--rating-min', type=int, default=800, help='Minimum puzzle rating')
    parser.add_argument('--rating-max', type=int, default=1200, help='Maximum puzzle rating')
    parser.add_argument('--output-dir', default='baselines', help='Output directory')
    
    args = parser.parse_args()
    
    collector = BaselineCollector(output_dir=args.output_dir)
    
    results = collector.collect_base_model_baseline(
        puzzle_count=args.puzzles,
        rating_range=(args.rating_min, args.rating_max)
    )
    
    print("\n🎉 Baseline collection completed!")
    if 'accuracy' in results['summary_stats']:
        print(f"📊 Accuracy: {results['summary_stats']['accuracy']:.1%}")
        print(f"⚖️ Legal Move Rate: {results['summary_stats']['legal_move_rate']:.1%}")
    else:
        print("❌ No results generated - check puzzle fetching")

if __name__ == "__main__":
    main()
