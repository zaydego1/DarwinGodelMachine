from utils.puzzle_tracker import PuzzleTracker


class ChessStagedEvaluation:
    def __init__(self):
        self.stage1_count = 10  # Basic functionality
        self.stage2_count = 50  # Extended evaluation
        self.stage1_legal_threshold = 0.8  # 80% legal moves
        self.stage1_accuracy_threshold = 0.2  # 20% correct solutions
        self.stage2_accuracy_threshold = 0.4  # 40% correct for engine games

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
            return results

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
        puzzles = self.get_unused_puzzles(rating_range=(800, 900), count=self.stage1_count, tracker=tracker)

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
        puzzles = self.get_unused_puzzles(rating_range=(800, 1000), count=self.stage2_count, tracker=tracker)

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