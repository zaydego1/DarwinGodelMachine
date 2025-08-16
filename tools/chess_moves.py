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
        return {"error": f"Error with chess moves: {str(e)}", "success": False}

def validate_move(board, move_san):
    """Validate if a move is legal"""
    try:
        move = board.parse_san(move_san)
        if move in board.legal_moves:
            # Make the move to see what happens
            board_copy = board.copy()
            board_copy.push(move)
            
            return {
                "success": True,
                "is_legal": True,
                "move": move_san,
                "gives_check": board_copy.is_check(),
                "is_capture": board.is_capture(move),
                "is_checkmate": board_copy.is_checkmate(),
                "resulting_fen": board_copy.fen()
            }
        else:
            return {
                "success": True,
                "is_legal": False,
                "move": move_san,
                "error": "Move is not legal in this position"
            }
    except Exception as e:
        return {
            "success": True,
            "is_legal": False,
            "move": move_san,
            "error": f"Invalid notation or parse error: {str(e)}"
        }

def generate_moves(board, move_type):
    """Generate legal moves by category"""
    legal_moves = list(board.legal_moves)
    
    if move_type == "captures":
        moves = [board.san(move) for move in legal_moves if board.is_capture(move)]
        return {
            "success": True,
            "move_type": "captures",
            "count": len(moves),
            "moves": moves[:10],  # Limit to 10 for brevity
            "truncated": len(moves) > 10
        }
    
    elif move_type == "checks":
        checking_moves = []
        for move in legal_moves:
            board_copy = board.copy()
            board_copy.push(move)
            if board_copy.is_check():
                checking_moves.append(board.san(move))
        return {
            "success": True,
            "move_type": "checks",
            "count": len(checking_moves),
            "moves": checking_moves[:10],  # Limit to 10 for brevity
            "truncated": len(checking_moves) > 10
        }
    
    else:  # all moves
        moves = [board.san(move) for move in legal_moves]
        return {
            "success": True,
            "move_type": "all",
            "count": len(moves),
            "moves": moves[:15] if len(moves) > 15 else moves,  # Limit to 15 for brevity
            "truncated": len(moves) > 15,
            "total_legal_moves": len(moves)
        }
