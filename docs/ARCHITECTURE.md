# Chess DGM System Architecture

**Purpose:** This document explains how the Chess DGM system is SUPPOSED to work when fully functional.

---

## System Overview

The Chess DGM (Darwin Gödel Machine) is a self-improving chess agent that:
1. Plays chess puzzles
2. Evaluates its own performance
3. Modifies its own code to address weaknesses
4. Evolves over generations using a parent selection algorithm

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVOLUTION OUTER LOOP                          │
│  (chess_dgm_outer.py - ChessDGMEvolution)                       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │  Generation N: Select Parents → Create Children     │        │
│  │                                                       │        │
│  │  ┌──────────────────────────────────────────┐       │        │
│  │  │  SELF-IMPROVEMENT LOOP                   │       │        │
│  │  │  (chess_self_improve.py)                  │       │        │
│  │  │                                            │       │        │
│  │  │  ┌──────────────────────────────┐         │       │        │
│  │  │  │  AGENT EXECUTION              │         │       │        │
│  │  │  │  (chess_agent.py)             │         │       │        │
│  │  │  │                                │         │       │        │
│  │  │  │  ┌────────────────────┐       │         │       │        │
│  │  │  │  │  TOOL CALLING      │       │         │       │        │
│  │  │  │  │  (llm_withtools.py)│       │         │       │        │
│  │  │  │  │                    │       │         │       │        │
│  │  │  │  │  ┌──────────┐     │       │         │       │        │
│  │  │  │  │  │ LLM      │     │       │         │       │        │
│  │  │  │  │  │ (llm.py) │     │       │         │       │        │
│  │  │  │  │  └──────────┘     │       │         │       │        │
│  │  │  │  │       ↕            │       │         │       │        │
│  │  │  │  │  ┌──────────┐     │       │         │       │        │
│  │  │  │  │  │  TOOLS   │     │       │         │       │        │
│  │  │  │  │  │ (tools/) │     │       │         │       │        │
│  │  │  │  │  └──────────┘     │       │         │       │        │
│  │  │  │  └────────────────────┘       │         │       │        │
│  │  │  └──────────────────────────────┘         │       │        │
│  │  │                                            │       │        │
│  │  │  Evaluation → Identify Weaknesses        │       │        │
│  │  │  → Create Tools → Modify Code             │       │        │
│  │  └──────────────────────────────────────────┘       │        │
│  │                                                       │        │
│  │  Evaluate All Children → Update Archive             │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                   │
│  Next Generation...                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Evolution Outer Loop (`chess_dgm_outer.py`)

**Purpose:** Manages the evolutionary process across generations.

**Key Classes:**
- `ChessDGMEvolution` - Main evolution controller

**Process:**
```
For each generation:
  1. Select k best-performing parents from archive
  2. Create k child agents (copies with potential improvements)
  3. Run self-improvement on each child in parallel
  4. Evaluate each improved child
  5. Add successful children to archive
  6. Update parent fitness scores
  7. Save generation state
```

**Selection Algorithm:**
- Uses ALPS-based parent selection
- Balances exploitation (good agents) and exploration (diverse agents)
- Tracks "functioning children count" as fitness metric

**Parallelization:**
- Runs `k` agents in parallel (default k=2)
- Uses ThreadPoolExecutor for parallel improvement
- Each agent has 1 hour timeout

---

### 2. Self-Improvement Loop (`chess_self_improve.py`)

**Purpose:** Enables agents to improve themselves based on evaluation results.

**Key Classes:**
- `ChessSelfImprove` - Orchestrates improvement process

**Two Strategies:**

#### A. Traditional Self-Improvement
```
1. Evaluate agent on puzzles
2. Identify failed puzzles
3. Analyze failure patterns
4. Generate improvement prompt
5. Agent modifies its own code
6. Validate improvements
```

#### B. Enhanced Self-Improvement (with Tool Creation)
```
1. Evaluate agent on puzzles (by theme)
2. Identify weak themes (e.g., tactics, material, pins)
3. Create compensatory tools for weak themes
4. Integrate tools into agent
5. Validate improvements
```

**Tool Creation Process:**
- `ToolCreationEngine` creates tools from templates
- `ToolIntegrationManager` modifies agent code to use tools
- Tools saved in `archive/{agent_id}/tools/`

---

### 3. Agent Execution (`chess_agent.py`)

**Purpose:** The chess-playing agent that analyzes positions.

**Key Classes:**
- `ChessAgent` - Main agent class

**Process:**
```python
def forward(position_fen):
    1. Construct analysis prompt with position
    2. Call LLM with tool-calling enabled
    3. LLM generates response (possibly with tool calls)
    4. Tool calling system executes tools
    5. Tool results fed back to LLM
    6. LLM generates final move suggestion
    7. Return suggestion
```

**Key Features:**
- Maintains conversation history
- Uses systematic analysis framework
- Enforces move validation via tools

---

### 4. Tool Calling System (`llm_withtools.py`)

**Purpose:** Enables LLMs to use external tools for analysis.

**Key Functions:**
- `chat_with_agent()` - Main entry point, routes to appropriate backend
- `chat_with_agent_manualtools()` - For Ollama/DeepSeek (text-based tool calling)
- `chat_with_agent_claude()` - For Claude (native tool calling)
- `chat_with_agent_openai()` - For OpenAI (native tool calling)
- `check_for_tool_use()` - Parses tool calls from LLM responses
- `process_tool_call()` - Executes a tool and returns result

**Tool Calling Flow (for DeepSeek/Ollama):**
```
1. Send prompt to LLM
2. LLM responds with text including:
   "TOOL_CALL: {"tool": "chess_moves", "args": {...}}"
3. Parse response to extract tool call
4. Execute tool → get result
5. Send result back to LLM:
   "Tool Result: {result}"
6. LLM incorporates result and continues reasoning
7. Repeat until no more tool calls
8. Return final response
```

**Tool Call Format:**
```
TOOL_CALL: {"tool": "tool_name", "args": {"param1": "value1", ...}}
```

---

### 5. Tools (`tools/`)

**Purpose:** Provide chess analysis capabilities to the agent.

**Standard Tools:**
- `chess_position` - Analyze position (material, threats, etc.)
- `chess_moves` - Generate legal moves, validate move notation
- `lichess_puzzle` - Fetch puzzles from Lichess database
- `bash` - Execute shell commands
- `edit` - Edit code files

**Tool Structure:**
Each tool must have:
```python
def tool_info():
    return {
        "name": "tool_name",
        "description": "What the tool does",
        "input_schema": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }

def tool_function(**kwargs):
    # Tool implementation
    return result
```

**Tool Loading:**
- `load_all_tools()` scans `/tools/` directory
- Dynamically imports all .py files (except __init__)
- Validates each tool has required functions
- Returns list of tool dicts: `[{"info": ..., "function": ..., "name": ...}, ...]`

---

### 6. Evaluation System (`evaluation/`)

**Purpose:** Measure agent performance and identify weaknesses.

**Key Classes:**
- `ChessStagedEvaluation` - Staged evaluation pipeline
- `ChessFundamentalsEvaluation` - Theme-based evaluation

**Staged Evaluation Process:**

#### Stage 1: Basic Functionality (10 puzzles, 400-600 ELO)
**Pass Criteria:**
- 80% legal move rate (agent must suggest valid moves)
- 20% accuracy (solve some puzzles correctly)

**Purpose:** Filter out completely broken agents.

#### Stage 2: Extended Evaluation (50 puzzles, 400-800 ELO)
**Pass Criteria:**
- 40% accuracy to advance to Stage 3

**Purpose:** Measure puzzle-solving ability.

#### Stage 3: Engine Games
**Pass Criteria:**
- Win rate against chess engines

**Purpose:** Measure real-world chess strength.

**Fundamentals Evaluation:**
- Groups puzzles by theme (tactics, material, pins, forks, etc.)
- Calculates accuracy per theme
- Identifies weak themes
- Suggests compensatory tools for weak areas

---

### 7. Tool Creation Engine (`utils/tool_creation_engine.py`)

**Purpose:** Create specialized tools to compensate for agent weaknesses.

**Key Classes:**
- `ToolCreationEngine` - Creates tools from templates
- `ToolIntegrationManager` - Integrates tools into agents

**Tool Templates:**
- `MaterialCalculator` - Calculate material balance
- `TacticalPatternScanner` - Detect pins, forks, skewers
- `KingSafetyAnalyzer` - Evaluate king safety
- `PawnStructureEvaluator` - Analyze pawn structure

**Process:**
```
1. Evaluate agent → identify weak theme (e.g., "tactics")
2. Look up tool template for theme
3. Generate tool code from template
4. Save to archive/{agent_id}/tools/
5. Update tool registry
6. Modify agent code to import and use tool
```

---

## Data Flow: Single Puzzle Attempt

```
1. EVALUATION initiates puzzle
   ↓
2. AGENT.forward(fen) called with position
   ↓
3. AGENT constructs prompt with analysis instructions
   ↓
4. TOOL CALLING SYSTEM sends prompt to LLM
   ↓
5. LLM (DeepSeek) generates response:
   "Let me analyze... TOOL_CALL: {\"tool\": \"chess_position\", ...}"
   ↓
6. TOOL CALLING SYSTEM parses response, finds tool call
   ↓
7. TOOL CALLING SYSTEM executes chess_position tool
   ↓
8. chess_position returns: {"material_balance": +1, ...}
   ↓
9. TOOL CALLING SYSTEM sends result back to LLM:
   "Tool Result: {material_balance: +1, ...}"
   ↓
10. LLM continues: "Based on material advantage...
    TOOL_CALL: {\"tool\": \"chess_moves\", \"args\": {\"move_san\": \"Nf3\"}}"
   ↓
11. TOOL CALLING SYSTEM executes chess_moves validation
   ↓
12. chess_moves returns: {"is_legal": true, ...}
   ↓
13. TOOL CALLING SYSTEM sends result back
   ↓
14. LLM concludes: "The move Nf3 is legal and best. ANSWER: Nf3"
   ↓
15. TOOL CALLING SYSTEM detects no more tool calls
   ↓
16. AGENT.forward() returns final response
   ↓
17. EVALUATION extracts move "Nf3"
   ↓
18. EVALUATION validates against correct answer
   ↓
19. EVALUATION records result (legal: yes, correct: yes/no)
```

---

## Data Flow: Self-Improvement Cycle

```
1. EVOLUTION selects parent agent from archive
   ↓
2. EVOLUTION creates child agent (copy of parent)
   ↓
3. SELF-IMPROVEMENT evaluates child on 10 puzzles
   ↓
4. EVALUATION returns results with failures
   ↓
5. SELF-IMPROVEMENT analyzes failure patterns:
   - Legal move rate: 60% (below 80% threshold)
   - Weak themes: [tactics, pins]
   ↓
6. TOOL CREATION ENGINE creates tools:
   - TacticalPatternScanner for tactics weakness
   ↓
7. TOOL INTEGRATION modifies child agent code:
   - Adds import for TacticalPatternScanner
   - Updates forward() to use tool
   ↓
8. SELF-IMPROVEMENT validates improved child
   ↓
9. EVALUATION re-tests child
   ↓
10. If improved: EVOLUTION adds to archive
    If not: EVOLUTION discards child
   ↓
11. EVOLUTION updates parent's fitness score
```

---

## File Organization

```
dgm/
├── chess_dgm_outer.py           # Evolution loop
├── chess_self_improve.py        # Self-improvement logic
├── chess_agent.py               # Agent definition
├── llm_withtools.py             # Tool calling system
├── llm.py                       # LLM clients
├── tools/
│   ├── __init__.py             # Tool loader
│   ├── chess_position.py       # Position analysis
│   ├── chess_moves.py          # Move generation/validation
│   ├── lichess_puzzle.py       # Puzzle database
│   ├── bash.py                 # Shell execution
│   └── edit.py                 # File editing
├── evaluation/
│   ├── staged_evaluation.py    # Main evaluation
│   ├── chess_fundamentals_evaluation.py  # Theme-based eval
│   └── engine_games.py         # Engine game evaluation
├── utils/
│   ├── tool_creation_engine.py # Tool generation
│   ├── agent_management.py     # Agent lifecycle
│   ├── parent_selection.py     # ALPS selection
│   └── puzzle_tracker.py       # Puzzle usage tracking
├── prompts/
│   ├── deepseek_tooluse_prompt.py    # Tool use instructions
│   └── chess_improvement_prompt.py   # Self-improvement prompts
├── archive/
│   ├── initial/                # Initial agent
│   ├── agent_001/              # First generation
│   │   ├── chess_agent.py      # Agent code
│   │   ├── tools/              # Agent-specific tools
│   │   │   └── materialcalculator.py
│   │   ├── tool_registry.json  # Tool metadata
│   │   └── metadata.json       # Performance data
│   └── agent_002/              # Second generation
│       └── ...
└── baselines/                  # Test results
    └── deepseek_tools_baseline_*.json
```

---

## Current vs. Intended State

### What Currently Works ✅
1. Evolution loop structure
2. Agent can communicate with DeepSeek R1
3. Tool definitions and schemas
4. Evaluation pipeline (identifies legal/illegal moves)
5. Tool creation templates
6. Parent selection algorithm

### What's Broken ❌
1. **Tool execution** - Tools detected but not executed
2. **Agent validation** - Can't validate moves without tools
3. **Improvement feedback** - No data on why moves fail
4. **Tool integration** - Created tools not loaded

### What Needs to Happen 🔧
1. **Fix tool execution loop** in `llm_withtools.py`
2. **Fix response parsing** for Ollama responses
3. **Verify feedback loop** (tool results → LLM)
4. **Simplify prompts** for better tool usage
5. **Fix tool loading** to include agent-specific tools
6. **Add metrics** to track tool usage

---

## Key Design Decisions

### Why Text-Based Tool Calling for DeepSeek?
- DeepSeek R1 via Ollama doesn't support native function calling
- Must use "prompt engineering" approach:
  - Prompt describes tool format
  - LLM outputs tool calls as text
  - System parses and executes
  - Results sent back as text

### Why ALPS-Based Parent Selection?
- Encourages diversity (don't always pick best)
- Age-layering prevents premature convergence
- Balances exploration vs. exploitation

### Why Staged Evaluation?
- Saves computation (don't test broken agents extensively)
- Clear progression path (basic → puzzles → games)
- Early filtering of non-functional agents

### Why Tool Creation vs. Code Modification?
- Tools are safer (isolated, testable)
- Tools are reusable across agents
- Tools compensate for LLM weaknesses without retraining
- Agents can combine multiple tools

### Why Local DeepSeek R1 14B?
- Free (no API costs)
- Private (data stays local)
- Good reasoning capabilities
- Fast enough for experimentation

---

## Performance Expectations

### Initial Agent (Generation 0)
- Legal move rate: ~50-70%
- Accuracy: ~10-20%
- Tool usage: Minimal (prompts request but tools don't execute)

### After Tool Execution Fixed (Generation 0 with tools)
- Legal move rate: ~80-90% (mandatory validation)
- Accuracy: ~20-30% (better analysis)
- Tool usage: 2-3 tools per puzzle

### After Evolution (Generation 5-10)
- Legal move rate: ~95%+ (always validated)
- Accuracy: ~40-60% (learned patterns)
- Tool usage: 3-5 tools per puzzle (created specialized tools)

### Long-term Goal (Generation 50+)
- Pass Stage 2 consistently
- Advance to Stage 3 (engine games)
- Win some games against weak engines

---

## Debugging Guide

### If Agent Doesn't Respond
1. Check Ollama is running: `ollama list`
2. Check model exists: `ollama pull deepseek-r1:14b`
3. Check logs for errors in LLM client

### If Tools Don't Execute
1. Add diagnostic logging in `llm_withtools.py`
2. Check `tool_use` dict is populated
3. Verify while loop is entered
4. Check tool results are generated

### If Agent Suggests Illegal Moves
1. Check if chess_moves tool is being called
2. Check if validation results are being used
3. Check if agent code has validation logic

### If Improvement Doesn't Work
1. Check if evaluation identifies failures
2. Check if tools are created
3. Check if tools are integrated
4. Check if improved agent is validated

---

## Success Metrics

### System-Level
- [ ] 80%+ agents pass Stage 1
- [ ] 40%+ agents pass Stage 2
- [ ] Performance improves over generations
- [ ] Tool diversity increases over time

### Tool-Level
- [ ] 95%+ tool calls execute successfully
- [ ] Tool results improve move accuracy
- [ ] Created tools are used by agents

### Agent-Level
- [ ] 90%+ legal move rate
- [ ] 30%+ puzzle accuracy
- [ ] Uses 2+ tools per puzzle

---

**This architecture represents the INTENDED design. The implementation plan in `IMPLEMENTATION_PLAN.md` details how to achieve this state.**
