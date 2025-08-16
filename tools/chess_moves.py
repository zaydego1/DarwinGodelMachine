import chess

def tool_info():
    return {
        "name": "chess_moves",
        "description": "Generate legal moves and validate move notation",
        "input_schema": {
            "type": "object",
            "properties": {
                "fen": {"type": "string", "description": "Position in FEN notation"},
                "move_san": {"type": "string", "description": "Move in algebraic notation (optional)"},
                "move_type": {"type": "string", "enum": ["all", "captures", "checks"], "default": "all"}
            },
            "required": ["fen"]
        }
    }

def tool_function(fen, move_san=None, move_type="all"):
    try:
        board = chess.Board(fen)
        
        if move_san:
            # Validate specific move
            return validate_move(board, move_san)
        else:
            # Generate moves
            return generate_moves(board, move_type)
            
    except Exception as e:
        return f"Error with chess moves: {str(e)}"

def validate_move(board, move_san):
    """Validate if a move is legal"""
    try:
        move = board.parse_san(move_san)
        if move in board.legal_moves:
            # Make the move to see what happens
            board_copy = board.copy()
            board_copy.push(move)
            
            result = f"✅ Legal move: {move_san}"
            if board_copy.is_check():
                result += " (gives check)"
            if board.is_capture(move):
                result += " (capture)"
            
            return result
        else:
            return f"❌ Illegal move: {move_san}"
    except:
        return f"❌ Invalid notation: {move_san}"

def generate_moves(board, move_type):
    """Generate legal moves by category"""
    legal_moves = list(board.legal_moves)
    
    if move_type == "captures":
        moves = [board.san(move) for move in legal_moves if board.is_capture(move)]
        return f"Captures ({len(moves)}): {', '.join(moves[:10])}"
    
    elif move_type == "checks":
        checking_moves = []
        for move in legal_moves:
            board_copy = board.copy()
            board_copy.push(move)
            if board_copy.is_check():
                checking_moves.append(board.san(move))
        return f"Checking moves ({len(checking_moves)}): {', '.join(checking_moves[:10])}"
    
    else:  # all moves
        moves = [board.san(move) for move in legal_moves]
        if len(moves) > 15:
            return f"Legal moves ({len(moves)}): {', '.join(moves[:15])}..."
        else:
            return f"Legal moves ({len(moves)}): {', '.join(moves)}"