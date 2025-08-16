# tools/lichess_puzzle.py
import requests
import json
import random
from utils.puzzle_tracker import PuzzleTracker


def tool_info():
    return {
        "name": "lichess_puzzle",
        "description": "Fetch chess puzzles from Lichess API by rating range",
        "input_schema": {
            "type": "object",
            "properties": {
                "rating_min": {"type": "integer", "default": 800},
                "rating_max": {"type": "integer", "default": 1200},
                "count": {"type": "integer", "default": 1},
                "themes": {"type": "string", "description": "Comma-separated themes (optional)"}
            },
            "required": []
        }
    }


def tool_function(rating_min=800, rating_max=1200, count=1, themes=""):
    try:
        tracker = PuzzleTracker()
        puzzles = fetch_unused_puzzles(rating_min, rating_max, count, themes, tracker)

        if not puzzles:
            return f"No unused puzzles found in range {rating_min}-{rating_max}"

        # Mark puzzles as used
        for puzzle in puzzles:
            tracker.mark_used(puzzle['id'])

        return format_puzzle_output(puzzles)

    except Exception as e:
        return f"Error fetching puzzles: {str(e)}"


def fetch_unused_puzzles(rating_min, rating_max, count, themes, tracker):
    """Fetch puzzles from Lichess API, ensuring no repeats"""

    # Lichess puzzle database endpoint
    url = "https://lichess.org/api/puzzle/daily"  # Daily puzzle
    # For batch access, we'll need to use database dumps or build local cache

    # For now, simulate with local puzzle database
    # In production, download Lichess puzzle database and query locally
    puzzles = load_local_puzzle_database(rating_min, rating_max, themes)

    # Filter out used puzzles
    unused_puzzles = [p for p in puzzles if not tracker.is_used(p['id'])]

    # Shuffle and return requested count
    random.shuffle(unused_puzzles)
    return unused_puzzles[:count]


def load_local_puzzle_database(rating_min, rating_max, themes):
    """Load puzzles from local Lichess database dump"""
    # This would load from downloaded Lichess puzzle database
    # For prototype, return sample puzzles

    sample_puzzles = [
        {
            "id": "00008",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            "moves": ["Qxf7#"],
            "rating": 840,
            "themes": ["mate", "mateIn1", "sacrifice"],
            "solution": "Qxf7#"
        },
        {
            "id": "00009",
            "fen": "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
            "moves": ["exd5", "Nf3"],
            "rating": 820,
            "themes": ["opening", "center"],
            "solution": "exd5"
        }
        # Add more sample puzzles...
    ]

    # Filter by rating
    filtered = [p for p in sample_puzzles
                if rating_min <= p['rating'] <= rating_max]

    # Filter by themes if specified
    if themes:
        theme_list = [t.strip() for t in themes.split(',')]
        filtered = [p for p in filtered
                    if any(theme in p['themes'] for theme in theme_list)]

    return filtered


def format_puzzle_output(puzzles):
    """Format puzzles for agent consumption"""
    output = f"Retrieved {len(puzzles)} puzzle(s):\n\n"

    for i, puzzle in enumerate(puzzles, 1):
        output += f"Puzzle {i}:\n"
        output += f"ID: {puzzle['id']}\n"
        output += f"Rating: {puzzle['rating']}\n"
        output += f"Position (FEN): {puzzle['fen']}\n"
        output += f"Themes: {', '.join(puzzle['themes'])}\n"
        output += f"Find the best move!\n\n"

    return output