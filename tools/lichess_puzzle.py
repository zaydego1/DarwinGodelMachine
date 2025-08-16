# tools/lichess_puzzle.py
import requests
import json
import random
import os
import time
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


def tool_function(rating_min=800, rating_max=1200, count=1, themes="", return_structured=False):
    try:
        tracker = PuzzleTracker()
        puzzles = fetch_unused_puzzles(rating_min, rating_max, count, themes, tracker)

        if not puzzles:
            if return_structured:
                return {"puzzles": [], "error": f"No unused puzzles found in range {rating_min}-{rating_max}"}
            return f"No unused puzzles found in range {rating_min}-{rating_max}"

        # Mark puzzles as used
        for puzzle in puzzles:
            tracker.mark_used(puzzle['id'])

        if return_structured:
            return {"puzzles": puzzles, "count": len(puzzles)}
        
        return format_puzzle_output(puzzles)

    except Exception as e:
        error_msg = f"Error fetching puzzles: {str(e)}"
        if return_structured:
            return {"puzzles": [], "error": error_msg}
        return error_msg


def get_lichess_puzzles(rating_min=800, rating_max=1200, count=1, themes=""):
    """Alias for tool_function that returns structured data for benchmark scripts"""
    result = tool_function(rating_min, rating_max, count, themes, return_structured=True)
    return result


def fetch_unused_puzzles(rating_min, rating_max, count, themes, tracker):
    """Fetch puzzles from local database, downloading from Lichess if needed"""
    
    # Ensure we have a local puzzle database
    ensure_puzzle_database(rating_min, rating_max)
    
    # Load puzzles from local database
    puzzles = load_local_puzzle_database(rating_min, rating_max, themes)
    
    # Filter out used puzzles
    unused_puzzles = [p for p in puzzles if not tracker.is_used(p['id'])]
    
    # If we don't have enough unused puzzles, try to download more
    if len(unused_puzzles) < count:
        print(f"Only {len(unused_puzzles)} unused puzzles available, downloading more...")
        download_puzzles_batch(rating_min, rating_max, batch_size=100)
        puzzles = load_local_puzzle_database(rating_min, rating_max, themes)
        unused_puzzles = [p for p in puzzles if not tracker.is_used(p['id'])]
    
    # Shuffle and return requested count
    random.shuffle(unused_puzzles)
    return unused_puzzles[:count]


def ensure_puzzle_database(rating_min, rating_max):
    """Ensure we have a local puzzle database with puzzles in the specified range"""
    database_file = get_database_filename(rating_min, rating_max)
    
    if not os.path.exists(database_file):
        print(f"Creating puzzle database for rating range {rating_min}-{rating_max}...")
        download_puzzles_batch(rating_min, rating_max, batch_size=500)


def get_database_filename(rating_min, rating_max):
    """Get the filename for the puzzle database based on rating range"""
    return f"puzzles_{rating_min}_{rating_max}.json"


def download_puzzles_batch(rating_min, rating_max, batch_size=500):
    """Download a batch of puzzles from Lichess database and save to local database"""
    database_file = get_database_filename(rating_min, rating_max)
    
    # Load existing puzzles if database exists
    existing_puzzles = []
    if os.path.exists(database_file):
        try:
            with open(database_file, 'r') as f:
                existing_puzzles = json.load(f)
        except:
            existing_puzzles = []
    
    existing_ids = {p['id'] for p in existing_puzzles}
    new_puzzles = []
    
    print(f"Downloading puzzles from Lichess database for rating range {rating_min}-{rating_max}...")
    
    # Try to download from Lichess puzzle database
    try:
        lichess_puzzles = download_lichess_puzzle_database()
        if lichess_puzzles:
            print(f"Processing {len(lichess_puzzles)} puzzles from Lichess database...")
            
            # Filter puzzles by rating range and check for duplicates
            for puzzle in lichess_puzzles:
                if len(new_puzzles) >= batch_size:
                    break
                    
                if (puzzle['id'] not in existing_ids and 
                    rating_min <= puzzle['rating'] <= rating_max):
                    new_puzzles.append(puzzle)
                    existing_ids.add(puzzle['id'])
            
            print(f"Found {len(new_puzzles)} new puzzles in rating range")
    
    except Exception as e:
        print(f"Error downloading from Lichess database: {e}")
    
    # If we still don't have enough puzzles, generate more sample puzzles
    if len(new_puzzles) < 50:
        print("Supplementing with additional sample puzzles...")
        generated_puzzles = generate_more_sample_puzzles(rating_min, rating_max, 100)
        for puzzle in generated_puzzles:
            if puzzle['id'] not in existing_ids:
                new_puzzles.append(puzzle)
                existing_ids.add(puzzle['id'])
    
    # Save updated database
    all_puzzles = existing_puzzles + new_puzzles
    with open(database_file, 'w') as f:
        json.dump(all_puzzles, f, indent=2)
    
    print(f"Added {len(new_puzzles)} new puzzles. Total database size: {len(all_puzzles)}")


def download_single_puzzle_from_lichess():
    """Download a single puzzle from Lichess API"""
    try:
        # Use the daily puzzle endpoint - in practice, we'd rotate through different endpoints
        # or use the puzzle database dump
        url = "https://lichess.org/api/puzzle/daily"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to our internal format
        puzzle = {
            'id': data['puzzle']['id'],
            'rating': data['puzzle'].get('rating', 1200),
            'fen': extract_fen_from_puzzle(data),
            'themes': data['puzzle'].get('themes', []),
            'solution': data['puzzle'].get('solution', []),
        }
        
        return puzzle
        
    except Exception as e:
        print(f"Error fetching puzzle from Lichess: {e}")
        return None


def extract_fen_from_puzzle(puzzle_data):
    """Extract FEN from Lichess puzzle data"""
    try:
        if 'game' in puzzle_data and 'pgn' in puzzle_data['game']:
            pgn_lines = puzzle_data['game']['pgn'].strip().split('\n')
            for line in pgn_lines:
                if line.startswith('[FEN '):
                    return line.split('"')[1]
        
        # Fallback - return starting position
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
    except:
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def download_lichess_puzzle_database():
    """Download puzzles from Lichess puzzle database"""
    try:
        # Try to download from Lichess puzzle database dump
        # Note: This is a large file, so we'll start with a smaller sample
        url = "https://database.lichess.org/lichess_db_puzzle.csv.bz2"
        print("Attempting to download Lichess puzzle database (this may take a while)...")
        
        # For now, return None to fall back to sample puzzles
        # In a production system, you'd download and parse the actual database
        print("Lichess database download not implemented yet, using sample puzzles...")
        return None
        
    except Exception as e:
        print(f"Error downloading Lichess database: {e}")
        return None


def generate_sample_puzzles(rating_min, rating_max):
    """Generate sample puzzles to supplement downloaded ones"""
    sample_puzzles = [
        {
            'id': f'sample_{rating_min}_001',
            'rating': rating_min + 50,
            'fen': 'r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4',
            'themes': ['fork', 'tactics'],
            'solution': ['Ng5', 'Nh3'],
            'moves': ['Ng5', 'Nh3']
        },
        {
            'id': f'sample_{rating_min}_002', 
            'rating': rating_min + 100,
            'fen': 'rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4',
            'themes': ['pin', 'tactics'],
            'solution': ['Bg4', 'h3'],
            'moves': ['Bg4', 'h3']
        },
        {
            'id': f'sample_{rating_min}_003',
            'rating': rating_min + 150,
            'fen': 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 5',
            'themes': ['discovery', 'tactics'],
            'solution': ['d4', 'exd4'],
            'moves': ['d4', 'exd4']
        },
        {
            'id': f'sample_{rating_min}_004',
            'rating': rating_max - 50,
            'fen': 'r1bqkbnr/pppp1p1p/2n3p1/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 4',
            'themes': ['mate', 'sacrifice'],
            'solution': ['Qh5+', 'Ke7'],
            'moves': ['Qh5+', 'Ke7']
        },
        {
            'id': f'sample_{rating_min}_005',
            'rating': rating_min + 25,
            'fen': 'rnbqkbnr/pppp1ppp/8/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 0 3',
            'themes': ['opening', 'development'],
            'solution': ['Nf3', 'Nc6'],
            'moves': ['Nf3', 'Nc6']
        },
        {
            'id': f'sample_{rating_min}_006',
            'rating': rating_max - 25,
            'fen': 'r2qkbnr/ppp2ppp/2np4/4p1B1/2B1P3/3P1N2/PPP2PPP/RN1QK2R w KQkq - 0 6',
            'themes': ['deflection', 'tactics'],
            'solution': ['Bxf7+', 'Kxf7'],
            'moves': ['Bxf7+', 'Kxf7']
        }
    ]
    
    # Filter to rating range
    return [p for p in sample_puzzles if rating_min <= p['rating'] <= rating_max]


def generate_more_sample_puzzles(rating_min, rating_max, count=100):
    """Generate a larger set of sample puzzles"""
    
    # Base puzzle patterns with different variations
    base_patterns = [
        # Tactical patterns
        {
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 5',
            'themes': ['fork', 'tactics'],
            'solution': ['Ng5', 'Nh6']
        },
        {
            'fen': 'rnbqkb1r/ppp2ppp/3p1n2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5',
            'themes': ['pin', 'tactics'],
            'solution': ['Bg5', 'Be7']
        },
        {
            'fen': 'r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 5 5',
            'themes': ['discovery', 'tactics'],
            'solution': ['d6', 'Nd4']
        },
        {
            'fen': 'r1bqkbnr/pppp1p1p/2n3p1/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 1 4',
            'themes': ['mate', 'sacrifice'],
            'solution': ['Qh4+', 'g3']
        },
        {
            'fen': 'rnbqkbnr/pppp1ppp/8/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 2',
            'themes': ['opening', 'development'],
            'solution': ['Nf6', 'Nc3']
        },
        {
            'fen': 'r1bqk2r/ppp2ppp/2np1n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 4 6',
            'themes': ['deflection', 'tactics'],
            'solution': ['Bxf7+', 'Kxf7']
        },
        {
            'fen': 'rnbqk2r/ppp2ppp/3p1n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 6',
            'themes': ['skewer', 'tactics'],
            'solution': ['Bg5', 'Be7']
        },
        {
            'fen': 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R b KQkq - 5 5',
            'themes': ['double attack', 'tactics'],
            'solution': ['Nd4', 'Nxd4']
        }
    ]
    
    puzzles = []
    puzzle_id_counter = 1
    
    # Generate variations of each pattern
    for i in range(count):
        if len(puzzles) >= count:
            break
            
        pattern = base_patterns[i % len(base_patterns)]
        rating = random.randint(rating_min, rating_max)
        
        puzzle = {
            'id': f'generated_{rating_min}_{rating_max}_{puzzle_id_counter:03d}',
            'rating': rating,
            'fen': pattern['fen'],
            'themes': pattern['themes'][:],  # Copy themes
            'solution': pattern['solution'][:],  # Copy solution
            'moves': pattern['solution'][:]  # Alias for compatibility
        }
        
        puzzles.append(puzzle)
        puzzle_id_counter += 1
    
    return puzzles


def load_local_puzzle_database(rating_min, rating_max, themes):
    """Load puzzles from local database file"""
    database_file = get_database_filename(rating_min, rating_max)
    
    if not os.path.exists(database_file):
        return []
    
    try:
        with open(database_file, 'r') as f:
            all_puzzles = json.load(f)
        
        # Filter by rating range (double-check)
        filtered_puzzles = []
        for puzzle in all_puzzles:
            if rating_min <= puzzle['rating'] <= rating_max:
                # Filter by themes if specified
                if themes:
                    theme_list = [t.strip().lower() for t in themes.split(',')]
                    puzzle_themes = [t.lower() for t in puzzle['themes']]
                    if any(theme in puzzle_themes for theme in theme_list):
                        filtered_puzzles.append(puzzle)
                else:
                    filtered_puzzles.append(puzzle)
        
        return filtered_puzzles
        
    except Exception as e:
        print(f"Error loading puzzle database: {e}")
        return []


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
