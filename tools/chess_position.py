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
            return "Invalid chess position"
        
        # Basic analysis
        analysis = []
        analysis.append(f"Position: {fen}")
        analysis.append(f"To move: {'White' if board.turn else 'Black'}")
        analysis.append(f"Legal moves: {len(list(board.legal_moves))}")
        analysis.append(f"In check: {board.is_check()}")
        
        # Material count
        material_balance = calculate_material_balance(board)
        analysis.append(f"Material balance: {material_balance:+d} (White perspective)")
        
        if analysis_type == "detailed":
            # Add more detailed analysis
            analysis.append(f"Castling rights: {get_castling_rights(board)}")
            analysis.append(f"En passant: {board.ep_square if board.ep_square else 'None'}")
        
        return "\n".join(analysis)
        
    except Exception as e:
        return f"Error analyzing position: {str(e)}"

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