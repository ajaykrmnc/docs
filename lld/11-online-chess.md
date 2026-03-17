# Design an Online Chess Game
**Difficulty:** Hard | **Companies:** Meta, Google, Microsoft, Amazon

---

## Problem Statement

Design a real-time multiplayer chess game system with move validation, game state management, time controls, and spectator support.

---

## Requirements

### Functional Requirements
1. Two players can play a chess game
2. Valid move validation for all piece types
3. Detect check, checkmate, stalemate, draw conditions
4. Time control (Fischer, Increment, Blitz modes)
5. Undo/redo functionality (in casual games)
6. Game replay and move history (PGN format)
7. Spectator mode

### Non-Functional Requirements
1. Real-time move synchronization
2. Low latency
3. Concurrent game support

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Game                                   │
├─────────────────────────────────────────────────────────────────┤
│ - gameId: String                                                │
│ - board: Board                                                  │
│ - players: Map<Color, Player>                                   │
│ - currentTurn: Color                                            │
│ - status: GameStatus                                            │
│ - moveHistory: List<Move>                                       │
│ - timer: GameTimer                                              │
│ - observers: List<GameObserver>                                 │
├─────────────────────────────────────────────────────────────────┤
│ + makeMove(from: Position, to: Position): MoveResult            │
│ + resign(color: Color): void                                    │
│ + offerDraw(color: Color): void                                 │
│ + undo(): boolean                                               │
│ + getValidMoves(position: Position): List<Position>             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         Board                                   │
├─────────────────────────────────────────────────────────────────┤
│ - squares: Piece[8][8]                                          │
│ - enPassantTarget: Position                                     │
│ - castlingRights: CastlingRights                                │
│ - halfMoveClock: int                                            │
│ - fullMoveNumber: int                                           │
├─────────────────────────────────────────────────────────────────┤
│ + getPiece(pos: Position): Piece                                │
│ + movePiece(from: Position, to: Position): void                 │
│ + isSquareAttacked(pos: Position, by: Color): boolean           │
│ + getKingPosition(color: Color): Position                       │
│ + clone(): Board                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    <<abstract>> Piece                           │
├─────────────────────────────────────────────────────────────────┤
│ - color: Color                                                  │
│ - type: PieceType                                               │
│ - hasMoved: boolean                                             │
├─────────────────────────────────────────────────────────────────┤
│ + getValidMoves(board: Board, pos: Position): List<Position>    │
│ + canAttack(board: Board, from: Position, to: Position): bool   │
└─────────────────────────────────────────────────────────────────┘
         △
    ┌────┴────┬────────┬────────┬────────┬────────┐
    │         │        │        │        │        │
  King     Queen    Rook    Bishop   Knight    Pawn
```

---

## Class Implementations

### 1. Position and Move
```java
public class Position {
    private final int row;  // 0-7 (ranks 1-8)
    private final int col;  // 0-7 (files a-h)
    
    public Position(int row, int col) {
        this.row = row;
        this.col = col;
    }
    
    public static Position fromAlgebraic(String notation) {
        int col = notation.charAt(0) - 'a';
        int row = notation.charAt(1) - '1';
        return new Position(row, col);
    }
    
    public String toAlgebraic() {
        return String.valueOf((char)('a' + col)) + (row + 1);
    }
    
    public boolean isValid() {
        return row >= 0 && row < 8 && col >= 0 && col < 8;
    }
}

public class Move {
    private final Position from;
    private final Position to;
    private final Piece piece;
    private final Piece capturedPiece;
    private final MoveType type;
    private final PieceType promotionPiece;
    
    public enum MoveType {
        NORMAL, CAPTURE, CASTLE_KINGSIDE, CASTLE_QUEENSIDE,
        EN_PASSANT, PROMOTION, PROMOTION_CAPTURE
    }
    
    public String toAlgebraic() {
        StringBuilder sb = new StringBuilder();
        if (type == MoveType.CASTLE_KINGSIDE) return "O-O";
        if (type == MoveType.CASTLE_QUEENSIDE) return "O-O-O";
        
        if (piece.getType() != PieceType.PAWN) {
            sb.append(piece.getType().getSymbol());
        }
        if (capturedPiece != null) {
            if (piece.getType() == PieceType.PAWN) {
                sb.append(from.toAlgebraic().charAt(0));
            }
            sb.append('x');
        }
        sb.append(to.toAlgebraic());
        if (promotionPiece != null) {
            sb.append('=').append(promotionPiece.getSymbol());
        }
        return sb.toString();
    }
}
```

### 2. Piece Implementations
```java
public abstract class Piece {
    protected final Color color;
    protected final PieceType type;
    protected boolean hasMoved;
    
    public abstract List<Position> getValidMoves(Board board, Position from);
    
    protected List<Position> getSlidingMoves(Board board, Position from, int[][] directions) {
        List<Position> moves = new ArrayList<>();
        for (int[] dir : directions) {
            int row = from.getRow() + dir[0];
            int col = from.getCol() + dir[1];
            
            while (isValid(row, col)) {
                Position pos = new Position(row, col);
                Piece target = board.getPiece(pos);
                
                if (target == null) {
                    moves.add(pos);
                } else {
                    if (target.getColor() != this.color) {
                        moves.add(pos);  // Capture
                    }
                    break;
                }
                row += dir[0];
                col += dir[1];
            }
        }
        return moves;
    }
}

public class Knight extends Piece {
    private static final int[][] MOVES = {
        {-2, -1}, {-2, 1}, {-1, -2}, {-1, 2},
        {1, -2}, {1, 2}, {2, -1}, {2, 1}
    };
    
    @Override
    public List<Position> getValidMoves(Board board, Position from) {
        List<Position> moves = new ArrayList<>();
        for (int[] offset : MOVES) {
            Position to = new Position(from.getRow() + offset[0], 
                                       from.getCol() + offset[1]);
            if (to.isValid()) {
                Piece target = board.getPiece(to);
                if (target == null || target.getColor() != this.color) {
                    moves.add(to);
                }
            }
        }
        return moves;
    }
}

public class King extends Piece {
    @Override
    public List<Position> getValidMoves(Board board, Position from) {
        List<Position> moves = new ArrayList<>();
        int[][] directions = {
            {-1,-1}, {-1,0}, {-1,1}, {0,-1}, {0,1}, {1,-1}, {1,0}, {1,1}
        };
        
        for (int[] dir : directions) {
            Position to = new Position(from.getRow() + dir[0], from.getCol() + dir[1]);
            if (to.isValid() && !board.isSquareAttacked(to, color.opposite())) {
                Piece target = board.getPiece(to);
                if (target == null || target.getColor() != this.color) {
                    moves.add(to);
                }
            }
        }
        
        // Castling
        if (!hasMoved && !board.isSquareAttacked(from, color.opposite())) {
            addCastlingMoves(board, from, moves);
        }
        
        return moves;
    }
}
```

### 3. MoveValidator
```java
public class MoveValidator {
    public MoveResult validate(Game game, Position from, Position to) {
        Board board = game.getBoard();
        Piece piece = board.getPiece(from);
        
        if (piece == null) {
            return MoveResult.invalid("No piece at source");
        }
        
        if (piece.getColor() != game.getCurrentTurn()) {
            return MoveResult.invalid("Not your turn");
        }
        
        List<Position> validMoves = piece.getValidMoves(board, from);
        if (!validMoves.contains(to)) {
            return MoveResult.invalid("Invalid move for this piece");
        }
        
        // Simulate move and check if king is in check
        Board simulated = board.clone();
        simulated.movePiece(from, to);
        Position kingPos = simulated.getKingPosition(piece.getColor());
        
        if (simulated.isSquareAttacked(kingPos, piece.getColor().opposite())) {
            return MoveResult.invalid("Move leaves king in check");
        }
        
        return MoveResult.valid(createMove(board, from, to, piece));
    }
}
```

### 4. GameTimer
```java
public class GameTimer {
    private final Map<Color, AtomicLong> remainingTime;
    private final long incrementMs;
    private volatile Color activeColor;
    private volatile long lastTickTime;
    private final ScheduledExecutorService scheduler;
    
    public GameTimer(Duration initialTime, Duration increment) {
        this.remainingTime = new EnumMap<>(Color.class);
        remainingTime.put(Color.WHITE, new AtomicLong(initialTime.toMillis()));
        remainingTime.put(Color.BLACK, new AtomicLong(initialTime.toMillis()));
        this.incrementMs = increment.toMillis();
        this.scheduler = Executors.newSingleThreadScheduledExecutor();
    }
    
    public void switchTurn(Color newActive) {
        if (activeColor != null) {
            remainingTime.get(activeColor).addAndGet(incrementMs);
        }
        this.activeColor = newActive;
        this.lastTickTime = System.currentTimeMillis();
    }
    
    public boolean isTimeUp(Color color) {
        updateTime();
        return remainingTime.get(color).get() <= 0;
    }
    
    private void updateTime() {
        if (activeColor == null) return;
        long now = System.currentTimeMillis();
        long elapsed = now - lastTickTime;
        remainingTime.get(activeColor).addAndGet(-elapsed);
        lastTickTime = now;
    }
}
```

