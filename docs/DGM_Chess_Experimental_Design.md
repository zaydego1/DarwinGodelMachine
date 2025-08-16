# DGM-Chess Experimental Design

## Overview

This document details the experimental design for applying the Darwin-Gödel Machine (DGM) to chess domain, including all variations from the original paper and our specific implementation choices.

## Table of Contents

1. [Variations from Original Experiment](#variations-from-original-experiment)
2. [Model Architecture & Context Strategy](#model-architecture--context-strategy)
3. [Tool Ecosystem](#tool-ecosystem)
4. [Evolution Strategy](#evolution-strategy)
5. [Evaluation Framework](#evaluation-framework)
6. [Benchmarking Methodology](#benchmarking-methodology)

---

## Variations from Original Experiment

### Core Domain Shift: Software Engineering → Chess

| Aspect | Original Paper | DGM-Chess |
|--------|---------------|-----------|
| **Domain** | Software repositories (SWE-bench, Polyglot) | Chess puzzles and positions |
| **Problem Type** | Fix bugs, implement features | Solve tactical puzzles, find best moves |
| **Success Metric** | Test passing rate | Puzzle accuracy, engine evaluation |
| **Knowledge Base** | Programming languages, frameworks | Chess theory, tactics, strategy |

### Model Configuration

| Component | Original Paper | DGM-Chess | Rationale |
|-----------|---------------|-----------|-----------|
| **Self-Modification Model** | Claude 3.5 Sonnet (New) | DeepSeek R1:14b | Cost efficiency, local deployment |
| **Evaluation Model** | Claude 3.5 Sonnet / o3-mini | DeepSeek R1:14b | Consistency across pipeline |
| **Context Window** | ~200K tokens | 128K tokens | DeepSeek R1 limitation |
| **Context Management** | Standard | Enhanced with priority caching | Manage chess analysis depth |

### Tool Ecosystem Comparison

#### Original Paper Tools
```
1. Bash tool - Execute system commands
2. Edit tool - View/modify entire files
Total: 2 tools
```

#### DGM-Chess Tools
```
1. bash - Execute system commands (inherited)
2. editor - View/create/edit files (enhanced version)
3. chess_position - Analyze chess positions (FEN → evaluation)
4. chess_moves - Generate/validate legal moves
5. lichess_puzzle - Fetch puzzles by rating/theme
Total: 5 tools + agent-created tools
```

**Tool Creation Capability**: Agents can create specialized chess analysis tools during evolution, enabling domain-specific improvements.

### Evolution Strategy Differences

| Parameter | Original Paper | DGM-Chess | Notes |
|-----------|---------------|-----------|-------|
| **Iterations** | 80 | 80 | Maintained |
| **Parallel Agents** | 2 (SWE-bench), 4 (Polyglot) | 2-3 | RAM-constrained (48GB) |
| **Population Strategy** | Single lineage | Single lineage | Maintained |
| **Mutation Scope** | Code + prompts | Code + prompts + tools | Enhanced scope |
| **Validation Gate** | Test passing | Chess functionality + puzzle solving | Domain-specific validation |

---

## Model Architecture & Context Strategy

### DeepSeek R1:14b Specifications
```
- Parameters: 14 billion
- Context Window: 128,000 tokens
- Architecture: Mixture of Experts (MoE)
- Deployment: Local via Ollama
- Memory Usage: ~12GB RAM per instance
```

### Enhanced Context Management

**Challenge**: Chess analysis requires deep tactical calculation that can consume significant context.

**Solution**: Priority-based context caching system
```python
class ContextManager:
    def __init__(self, model="deepseek-r1:14b"):
        self.max_tokens = 128000
        self.compression_threshold = int(self.max_tokens * 0.85)
        self.recent_turns_count = 12
        self.max_cache_tokens = 8000
        
    def add_to_cache(self, content, content_type="general", priority=1):
        # Cache important chess patterns, tool results, evaluations
```

**Caching Priorities**:
1. **Priority 3 (High)**: Chess positions, correct solutions, tool results
2. **Priority 2 (Medium)**: Analysis patterns, tactical motifs  
3. **Priority 1 (Low)**: General conversation context

### Prompt Engineering Strategy

**Original Format** (XML-style):
```xml
<tool_use>
{'tool_name': 'bash', 'tool_input': {'command': 'ls'}}
</tool_use>
```

**Enhanced Format** (JSON-structured):
```json
TOOL_CALL: {"tool": "chess_position", "args": {"fen": "rnbqk...", "analysis_type": "tactical"}}
```

**Benefits**:
- 70% token reduction in tool descriptions
- Better parsing reliability for DeepSeek R1
- Structured format improves tool chaining

---

## Tool Ecosystem

### Chess-Specific Tools

#### 1. chess_position
```python
def tool_info():
    return {
        "name": "chess_position",
        "description": "Analyze chess position - material, threats, evaluation",
        "input_schema": {
            "properties": {
                "fen": {"type": "string", "description": "Position in FEN notation"},
                "analysis_type": {"type": "string", "enum": ["basic", "detailed", "tactical"]}
            }
        }
    }
```

#### 2. chess_moves  
```python
def tool_info():
    return {
        "name": "chess_moves",
        "description": "Generate legal moves and validate move notation",
        "input_schema": {
            "properties": {
                "fen": {"type": "string", "description": "Position in FEN notation"},
                "move_san": {"type": "string", "description": "Move in algebraic notation"},
                "move_type": {"type": "string", "enum": ["all", "captures", "checks"]}
            }
        }
    }
```

#### 3. lichess_puzzle
```python
def tool_info():
    return {
        "name": "lichess_puzzle",
        "description": "Fetch chess puzzles by rating and theme",
        "input_schema": {
            "properties": {
                "rating_min": {"type": "integer", "minimum": 600},
                "rating_max": {"type": "integer", "maximum": 2800},
                "count": {"type": "integer", "default": 10},
                "themes": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
```

### Tool Creation Framework

Agents can create specialized tools following this template:
```python
# Example: Opening database tool created by agent
def tool_info():
    return {
        "name": "opening_database",
        "description": "Query opening theory and common continuations",
        "input_schema": {
            "properties": {
                "fen": {"type": "string"},
                "depth": {"type": "integer", "default": 5}
            }
        }
    }

def tool_function(fen, depth=5):
    # Agent-implemented opening analysis logic
    pass
```

**Tool Creation Guidelines for Agents**:
- Must follow standard `tool_info()` and `tool_function()` pattern
- Should be general-purpose, not position-specific
- Focus on reusable chess analysis capabilities
- Examples: pawn structure analysis, endgame evaluation, tactical pattern recognition

---

## Evolution Strategy

### Parent Selection Algorithm
```python
class ChessParentSelector:
    def select_parents(self, archive):
        # Paper-exact algorithm:
        # 1. Calculate selection probabilities based on:
        #    - Performance score (puzzle accuracy)
        #    - Functioning children count
        # 2. Sample parents with replacement
        # 3. Return k_parallel parents for this generation
```

### Self-Modification Process

1. **Performance Analysis**: Evaluate on Lichess puzzles (rating 800-1000)
2. **Failure Identification**: Collect incorrectly solved puzzles with solutions
3. **Improvement Generation**: Agent analyzes failures and proposes code changes
4. **Implementation**: Agent modifies its own code/prompts/tools
5. **Validation**: Verify agent still functions correctly

### Mutation Constraints

**Allowed Modifications**:
- Agent code (`chess_agent.py`)
- Analysis prompts and strategies
- Tool creation and modification
- Chess-specific heuristics

**Forbidden Modifications**:
- Evolution framework (`chess_dgm_outer.py`)
- Parent selection logic (`utils/parent_selection.py`)
- Evaluation system (`evaluation/`)
- Agent management (`utils/agent_management.py`)

**Safety Checks**:
```python
def validate_agent(agent):
    # 1. Can agent make legal moves? (>80% legal move rate)
    # 2. Can agent solve basic puzzles? (>20% accuracy on 800-900 rated)
    # 3. Does agent respond appropriately to tool calls?
    # 4. Can agent still modify its own code?
```

---

## Evaluation Framework

### Three-Stage Evaluation Process

#### Stage 1: Basic Functionality (Gate)
```
- Puzzle Count: 10 puzzles (rating 800-900)
- Legal Move Threshold: 80%
- Accuracy Threshold: 20%
- Purpose: Eliminate non-functional agents
```

#### Stage 2: Extended Evaluation
```
- Puzzle Count: 50 puzzles (rating 800-1000)  
- Accuracy Threshold: 40% (to advance to Stage 3)
- Purpose: Measure chess problem-solving ability
```

#### Stage 3: Engine Games (Optional)
```
- Opponent: Stockfish at reduced strength
- Game Count: 10 games
- Purpose: Evaluate practical chess playing ability
```

### Performance Metrics

**Primary Metric**: Stage 2 puzzle accuracy (0.0 to 1.0)
**Secondary Metrics**:
- Legal move rate
- Engine game win rate (if applicable)
- Tool usage patterns
- Code complexity metrics

---

## Benchmarking Methodology

### Baseline Comparisons

We will measure performance across these configurations:

1. **DeepSeek R1 Base Model**
   - No tools, no evolution
   - Standard chess analysis prompts

2. **DeepSeek R1 + Enhanced Tools (No Evolution)**
   - With chess tools (chess_position, chess_moves, lichess_puzzle)
   - Enhanced prompt engineering
   - No self-modification

3. **DeepSeek R1 + Tools + Evolution**
   - Full DGM system
   - Self-modification enabled
   - Tool creation capability

4. **Original Paper Baseline (Simulated)**
   - Claude 3.5 Sonnet with chess adaptation
   - Original XML tool format
   - For comparison purposes

### Evaluation Timeline

**Pre-Training**: Establish baselines on fixed test set
**During Training**: Track performance every 10 generations  
**Post-Training**: Comprehensive evaluation on held-out puzzles

### Test Set Design

**Training Set**: Lichess puzzles (rating 800-1000, themes: mixed)
**Validation Set**: Lichess puzzles (rating 1000-1200, themes: mixed)
**Test Set**: Curated puzzle collection (rating 800-1400, diverse themes)

**Puzzle Themes Include**:
- Tactical: pins, forks, skewers, discovered attacks
- Strategic: pawn structure, piece activity, king safety
- Endgame: basic checkmate patterns, pawn endgames

---

## Hardware Requirements

```
Total RAM: 48GB
Per DeepSeek R1 Instance: ~12GB
Max Parallel Agents: 3
Operating System: macOS
Deployment: Local via Ollama
```

## Expected Outcomes

**Hypothesis**: Chess-specialized DGM agents will:
1. Develop sophisticated chess analysis capabilities
2. Create specialized tools for tactical pattern recognition
3. Show measurable improvement over base model performance  
4. Demonstrate emergent chess understanding through tool creation

**Success Criteria**:
- Final generation agents achieve >60% accuracy on test puzzles
- Evidence of meaningful tool creation and specialization
- Performance improvement trajectory over 80 generations
- Agents maintain chess functionality throughout evolution

---

*Last Updated: [Date]*
*Version: 1.0*
