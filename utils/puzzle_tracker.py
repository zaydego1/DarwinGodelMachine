# utils/puzzle_tracker.py
import json
import os
import threading


class PuzzleTracker:
    """Global tracker to ensure no puzzle is ever used twice"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.used_puzzles_file = "used_puzzles.json"
            self.used_puzzles = self.load_used_puzzles()
            self._initialized = True

    def load_used_puzzles(self):
        """Load set of already used puzzle IDs"""
        if os.path.exists(self.used_puzzles_file):
            try:
                with open(self.used_puzzles_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('used_puzzle_ids', []))
            except:
                return set()
        return set()

    def save_used_puzzles(self):
        """Save used puzzle IDs to file"""
        with open(self.used_puzzles_file, 'w') as f:
            json.dump({'used_puzzle_ids': list(self.used_puzzles)}, f)

    def is_used(self, puzzle_id):
        """Check if puzzle has been used before"""
        return puzzle_id in self.used_puzzles

    def mark_used(self, puzzle_id):
        """Mark puzzle as used"""
        with self._lock:
            self.used_puzzles.add(puzzle_id)
            self.save_used_puzzles()

    def get_usage_stats(self):
        """Get statistics about puzzle usage"""
        return {
            'total_used': len(self.used_puzzles),
            'used_puzzle_ids': list(self.used_puzzles)
        }

    def reset_usage(self):
        """Reset all puzzle usage (for testing)"""
        with self._lock:
            self.used_puzzles.clear()
            self.save_used_puzzles()