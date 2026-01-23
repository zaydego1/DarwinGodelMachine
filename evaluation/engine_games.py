# evaluation/engine_games.py
import requests
import chess
import chess.engine
import random
import time


class ChessComEngineGames:
    def __init__(self, target_elo=1000):
        self.target_elo = target_elo
        self.engine_path = self._find_stockfish()

    def _find_stockfish(self):
        import os
        import shutil

        possible_paths = [
            "/usr/games/stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
            "stockfish"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
            if shutil.which(path):
                return shutil.which(path)

        return None

    def play_games_vs_engine(self, agent, num_games=20):
        if self.engine_path is None:
            print("WARNING: Stockfish not found. Skipping engine games.")
            print("Install with: brew install stockfish (macOS) or apt-get install stockfish (Linux)")
            return {
                'win_rate': 0.0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'errors': 0,
                'total_games': 0,
                'results': [],
                'skipped': True,
                'reason': 'stockfish_not_found'
            }

        results = []

        for game_num in range(num_games):
            game_result = self.play_single_game(agent, game_num)
            results.append(game_result)

            time.sleep(1)

        return self.calculate_performance(results)

    def play_single_game(self, agent, game_num):
        """Play one complete game"""
        board = chess.Board()
        agent_color = chess.WHITE if game_num % 2 == 0 else chess.BLACK
        moves_played = []
        move_count = 0
        max_moves = 200  # Prevent infinite games

        try:
            with chess.engine.SimpleEngine.popen_uci(self.engine_path) as engine:
                while not board.is_game_over() and move_count < max_moves:
                    if board.turn == agent_color:
                        # Agent's turn
                        move_result = self.get_agent_move(agent, board)

                        if move_result['status'] == 'illegal':
                            return {
                                'result': 'loss',
                                'reason': 'illegal_move',
                                'moves': moves_played,
                                'agent_color': 'white' if agent_color else 'black',
                                'game_num': game_num
                            }

                        move = move_result['move']
                        board.push(move)
                        moves_played.append(board.san(move))

                    else:
                        # Engine's turn
                        engine_move = self.get_engine_move(engine, board)
                        board.push(engine_move)
                        moves_played.append(board.san(engine_move))

                    move_count += 1

                # Game finished - determine result
                return self.determine_game_result(board, agent_color, moves_played, game_num)

        except Exception as e:
            return {
                'result': 'error',
                'reason': str(e),
                'moves': moves_played,
                'agent_color': 'white' if agent_color else 'black',
                'game_num': game_num
            }

    def get_agent_move(self, agent, board):
        """Get move from chess agent"""
        try:
            color_name = "White" if board.turn else "Black"
            move_prompt = f"You are playing as {color_name}. Current position: {board.fen()}\nFind your best move."

            response = agent.forward(move_prompt)
            suggested_move = self.extract_move_from_response(response, board.fen())

            # Validate move
            if suggested_move and suggested_move in [board.san(m) for m in board.legal_moves]:
                move_obj = board.parse_san(suggested_move)
                return {'status': 'legal', 'move': move_obj}
            else:
                return {'status': 'illegal', 'move': None}

        except Exception as e:
            return {'status': 'error', 'move': None}

    def get_engine_move(self, engine, board):
        """Get move from Stockfish at target ELO strength"""
        # Limit engine strength to simulate target ELO
        time_limit = self.elo_to_time_limit(self.target_elo)
        depth_limit = self.elo_to_depth_limit(self.target_elo)

        result = engine.play(
            board,
            chess.engine.Limit(time=time_limit, depth=depth_limit)
        )
        return result.move

    def elo_to_time_limit(self, elo):
        """Convert ELO to appropriate time limit for engine"""
        if elo <= 1000:
            return 0.1  # 100ms
        elif elo <= 1200:
            return 0.2  # 200ms  
        elif elo <= 1400:
            return 0.5  # 500ms
        else:
            return 1.0  # 1s

    def elo_to_depth_limit(self, elo):
        if elo <= 1000:
            return 8
        elif elo <= 1200:
            return 10
        elif elo <= 1400:
            return 12
        else:
            return 15

    def extract_move_from_response(self, response, fen):
        import re

        move_patterns = [
            r'MOVE:\s*([a-h][1-8][a-h][1-8][qrbn]?)',
            r'best move is\s+([a-h][1-8][a-h][1-8][qrbn]?)',
            r'I (?:suggest|recommend|play)\s+([a-h][1-8][a-h][1-8][qrbn]?)',
            r'\b([NBRQK]?[a-h]?[1-8]?x?[a-h][1-8](?:=[NBRQ])?[+#]?)\b'
        ]

        for pattern in move_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def determine_game_result(self, board, agent_color, moves_played, game_num):
        outcome = board.outcome()

        if outcome is None:
            result = 'draw'
            reason = 'max_moves_reached'
        elif outcome.winner is None:
            result = 'draw'
            reason = outcome.termination.name.lower()
        elif outcome.winner == agent_color:
            result = 'win'
            reason = outcome.termination.name.lower()
        else:
            result = 'loss'
            reason = outcome.termination.name.lower()

        return {
            'result': result,
            'reason': reason,
            'moves': moves_played,
            'agent_color': 'white' if agent_color == chess.WHITE else 'black',
            'game_num': game_num,
            'total_moves': len(moves_played)
        }

    def calculate_performance(self, results):
        wins = sum(1 for r in results if r['result'] == 'win')
        losses = sum(1 for r in results if r['result'] == 'loss')
        draws = sum(1 for r in results if r['result'] == 'draw')
        errors = sum(1 for r in results if r['result'] == 'error')

        total_games = len(results)
        win_rate = wins / total_games if total_games > 0 else 0.0

        return {
            'win_rate': win_rate,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'errors': errors,
            'total_games': total_games,
            'results': results
        }