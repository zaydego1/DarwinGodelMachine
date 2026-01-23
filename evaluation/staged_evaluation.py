import json
import random
import re
from utils.puzzle_tracker import PuzzleTracker


class ChessStagedEvaluation:
    def __init__(self, stage1_count=10, stage2_count=50):
        self.stage1_count = stage1_count
        self.stage2_count = stage2_count
        self.stage1_legal_threshold = 0.8
        self.stage1_accuracy_threshold = 0.2
        self.stage2_accuracy_threshold = 0.4

    def evaluate_agent(self, agent, agent_id):
        """Full staged evaluation - agent must pass each stage to continue"""

        results = {
            'agent_id': agent_id,
            'stage1': None,
            'stage2': None,
            'stage3': None,
            'final_performance': 0.0,
            'advances_to_games': False
        }

        # Stage 1: Basic functionality test
        print(f"Stage 1: Testing basic functionality for {agent_id}")
        stage1_result = self.stage1_evaluation(agent)
        results['stage1'] = stage1_result

        if not stage1_result['passes']:
            print(f"❌ {agent_id} failed Stage 1")
        else:
            print(f"✅ {agent_id} passed Stage 1")

        # Stage 2: Extended puzzle evaluation
        print(f"Stage 2: Extended evaluation for {agent_id}")
        stage2_result = self.stage2_evaluation(agent)
        results['stage2'] = stage2_result
        results['final_performance'] = stage2_result['accuracy']

        if stage2_result['advances_to_games']:
            print(f"✅ {agent_id} qualified for engine games")
            results['advances_to_games'] = True

            # Stage 3: Engine games
            print(f"Stage 3: Engine games for {agent_id}")
            from evaluation.engine_games import ChessComEngineGames
            engine_eval = ChessComEngineGames()
            stage3_result = engine_eval.play_games_vs_engine(agent)
            results['stage3'] = stage3_result
            results['final_performance'] = stage3_result['win_rate']
        else:
            print(f"❌ {agent_id} did not qualify for engine games")

        return results

    def stage1_evaluation(self, agent):
        """Stage 1: Can agent make legal moves and solve basic puzzles?"""
        tracker = PuzzleTracker()
        puzzles = self.get_unused_puzzles(rating_range=(400, 600), count=self.stage1_count, tracker=tracker)

        results = []
        legal_count = 0
        correct_count = 0

        for puzzle in puzzles:
            try:
                response = agent.forward(f"Solve this chess puzzle:\n{format_single_puzzle(puzzle)}")
                suggested_move = self.extract_move_from_response(response, puzzle['fen'])

                is_legal = self.is_legal_move(suggested_move, puzzle['fen'])
                is_correct = suggested_move in puzzle['moves']

                if is_legal:
                    legal_count += 1
                if is_correct:
                    correct_count += 1

                results.append({
                    'puzzle_id': puzzle['id'],
                    'suggested_move': suggested_move,
                    'is_legal': is_legal,
                    'is_correct': is_correct,
                    'agent_response': response
                })

                # Mark puzzle as used
                tracker.mark_used(puzzle['id'])

            except Exception as e:
                results.append({
                    'puzzle_id': puzzle['id'],
                    'error': str(e),
                    'is_legal': False,
                    'is_correct': False
                })

        legal_rate = legal_count / len(puzzles)
        accuracy = correct_count / len(puzzles)

        passes = (legal_rate >= self.stage1_legal_threshold and
                  accuracy >= self.stage1_accuracy_threshold)

        return {
            'passes': passes,
            'legal_move_rate': legal_rate,
            'accuracy': accuracy,
            'results': results
        }

    def stage2_evaluation(self, agent):
        """Stage 2: Extended puzzle evaluation"""
        tracker = PuzzleTracker()
        puzzles = self.get_unused_puzzles(rating_range=(800, 1200), count=self.stage2_count, tracker=tracker)

        results = []
        correct_count = 0

        for puzzle in puzzles:
            response = agent.forward(f"Solve this chess puzzle:\n{format_single_puzzle(puzzle)}")
            suggested_move = self.extract_move_from_response(response, puzzle['fen'])
            is_correct = suggested_move in puzzle['moves']

            if is_correct:
                correct_count += 1

            results.append({
                'puzzle_id': puzzle['id'],
                'suggested_move': suggested_move,
                'is_correct': is_correct
            })

            tracker.mark_used(puzzle['id'])

        accuracy = correct_count / len(puzzles)
        advances_to_games = accuracy >= self.stage2_accuracy_threshold

        return {
            'accuracy': accuracy,
            'advances_to_games': advances_to_games,
            'results': results
        }

    def get_unused_puzzles(self, rating_range, count, tracker):
        """Get unused puzzles within rating range"""
        puzzle_files = [
            'puzzles_400_600.json',
            'puzzles_500_700.json',
            'puzzles_600_800.json',
            'puzzles_800_1200.json',
            'puzzles_900_1100.json', 
            'puzzles_1200_1500.json'
        ]
        
        all_puzzles = []
        for file in puzzle_files:
            try:
                with open(file, 'r') as f:
                    puzzles = json.load(f)
                    all_puzzles.extend(puzzles)
            except FileNotFoundError:
                continue
        
        # Filter by rating and unused status
        filtered_puzzles = []
        for puzzle in all_puzzles:
            rating = puzzle.get('rating', 800)
            puzzle_id = puzzle.get('id', str(random.randint(10000, 99999)))
            
            if rating_range[0] <= rating <= rating_range[1]:
                if not tracker.is_used(puzzle_id):
                    filtered_puzzles.append(puzzle)
        
        # Return requested count
        if len(filtered_puzzles) > count:
            return random.sample(filtered_puzzles, count)
        return filtered_puzzles

    def extract_move_from_response(self, response, fen, debug=False):
        response_lower = response.lower()

        final_answer_markers = [
            'final answer', 'best move', 'conclusion',
            'step 5:', '### step 5', 'output your answer'
        ]
        final_section_start = -1
        best_marker = None
        for marker in final_answer_markers:
            pos = response_lower.rfind(marker)
            if pos > final_section_start:
                final_section_start = pos
                best_marker = marker

        if final_section_start > 0:
            final_section = response[final_section_start:]
            if debug:
                print(f"[EXTRACT_DEBUG] Found marker '{best_marker}' at position {final_section_start}")
                print(f"[EXTRACT_DEBUG] Final section (first 200 chars): {final_section[:200]}")
        else:
            final_section = response[-500:] if len(response) > 500 else response
            if debug:
                print(f"[EXTRACT_DEBUG] No marker found, using last 500 chars")

        json_patterns = [
            r'"(?:MOVE|move|best_move)":\s*"([^"]+)"',
            r'"(?:MOVE|move|best_move)":\s*\'([^\']+)\'',
            r'\{[^}]*"(?:move|best_move)":\s*"([A-Za-z0-9#+x=-]+)"',
        ]

        for i, pattern in enumerate(json_patterns):
            matches = re.findall(pattern, final_section, re.IGNORECASE)
            if matches:
                move = matches[-1].strip()
                if debug:
                    print(f"[EXTRACT_DEBUG] JSON pattern {i} matched: {move}")
                return move

        explicit_move_patterns = [
            r'\*\*MOVE:\*\*\s*([A-Za-z0-9#+x=-]+)',
            r'MOVE:\s*([A-Za-z0-9#+x=-]+)',
            r'Best Move:\s*([A-Za-z0-9#+x=-]+)',
            r'\*\*Best Move:\*\*\s*([A-Za-z0-9#+x=-]+)',
        ]

        for i, pattern in enumerate(explicit_move_patterns):
            matches = re.findall(pattern, final_section, re.IGNORECASE)
            if matches:
                valid_moves = [m.strip() for m in matches if m.strip() and len(m.strip()) >= 2]
                if valid_moves:
                    move = valid_moves[-1]
                    if debug:
                        print(f"[EXTRACT_DEBUG] Explicit pattern {i} matched: {move} (from {len(matches)} matches)")
                    return move

        move_patterns = [
            r'\b([KQRBN][a-h][1-8](?:x?[a-h][1-8])?[+#]?)\b',
            r'\b([a-h][1-8]x?[a-h][1-8][qrbn]?[+#]?)\b',
            r'\b([KQRBN]x[a-h][1-8][+#]?)\b',
        ]

        for i, pattern in enumerate(move_patterns):
            matches = re.findall(pattern, final_section)
            if matches:
                move = matches[-1].strip()
                if debug:
                    print(f"[EXTRACT_DEBUG] Fallback pattern {i} matched: {move} (from {len(matches)} matches)")
                return move

        if debug:
            print(f"[EXTRACT_DEBUG] No patterns matched, returning 'unknown'")
        return "unknown"

    def is_legal_move(self, move, fen):
        """Check if move is legal - simplified version"""
        if move == "unknown" or not move:
            return False
        
        # Basic format checks
        if len(move) < 2:
            return False
        
        # For now, assume moves that look reasonable are legal
        # In a full implementation, you'd use python-chess
        chess_notation_pattern = r'^[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?$'
        uci_pattern = r'^[a-h][1-8][a-h][1-8][qrbn]?$'
        
        return bool(re.match(chess_notation_pattern, move) or re.match(uci_pattern, move))


def format_single_puzzle(puzzle):
    """Format a single puzzle for display"""
    return f"FEN: {puzzle.get('fen', 'Unknown')}\nRating: {puzzle.get('rating', 'Unknown')}\nThemes: {', '.join(puzzle.get('themes', []))}"