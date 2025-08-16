import chess

def tool_info():
    return {
        "name": "chess_position",
        "description": "Analyze a chess position - material, threats, basic evaluation",
        "input_schema": {
            "type": "object",
            "properties": {
                "fen": {"type": "string", "description": "Position in FEN notation"},
                "analysis_type": {"type": "string", "enum": ["basic", "detailed"], "default": "basic"}
            },
            "required": ["fen"]
        }
    }

def tool_function(fen, analysis_type="basic"):
    try:
        board = chess.Board(fen)
        
        if not board.is_valid():
            return {"error": "Invalid chess position", "success": False}
        
        # Material count
        material_balance = calculate_material_balance(board)
        
        # Basic analysis
        result = {
            "success": True,
            "position": fen,
            "to_move": "White" if board.turn else "Black",
            "legal_moves_count": len(list(board.legal_moves)),
            "in_check": board.is_check(),
            "material_balance": material_balance,
            "analysis_summary": f"{'White' if board.turn else 'Black'} to move, {len(list(board.legal_moves))} legal moves"
        }
        
        if analysis_type == "detailed":
            # Add more detailed analysis
            result.update({
                "castling_rights": get_castling_rights(board),
                "en_passant": str(board.ep_square) if board.ep_square else None,
                "is_endgame": is_endgame(board),
                "piece_count": count_pieces(board)
            })
        
        return result
        
    except Exception as e:
        return {"error": f"Error analyzing position: {str(e)}", "success": False}

def calculate_material_balance(board):
    """Calculate material balance (positive = White advantage)"""
    piece_values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
    }
    
    balance = 0
    for square, piece in board.piece_map().items():
        value = piece_values[piece.piece_type]
        if piece.color == chess.WHITE:
            balance += value
        else:
            balance -= value
    
    return balance

def get_castling_rights(board):
    """Get castling rights description"""
    rights = []
    if board.has_kingside_castling_rights(chess.WHITE):
        rights.append("K")
    if board.has_queenside_castling_rights(chess.WHITE):
        rights.append("Q")
    if board.has_kingside_castling_rights(chess.BLACK):
        rights.append("k")
    if board.has_queenside_castling_rights(chess.BLACK):
        rights.append("q")
    
    return "".join(rights) if rights else "None"

def is_endgame(board):
    """Determine if position is in endgame (simple heuristic)"""
    piece_count = len(board.piece_map())
    return piece_count <= 10  # Simple heuristic: <= 10 pieces total

def count_pieces(board):
    """Count pieces by type and color"""
    piece_count = {
        'white_pawns': len(board.pieces(chess.PAWN, chess.WHITE)),
        'black_pawns': len(board.pieces(chess.PAWN, chess.BLACK)),
        'white_pieces': len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE)) + 
                       len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.WHITE)),
        'black_pieces': len(board.pieces(chess.KNIGHT, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK)) + 
                       len(board.pieces(chess.ROOK, chess.BLACK)) + len(board.pieces(chess.QUEEN, chess.BLACK)),
        'total': len(board.piece_map())
    }
    return piece_count
