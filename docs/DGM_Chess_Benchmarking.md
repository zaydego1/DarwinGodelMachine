# DGM-Chess Benchmarking Framework

## Overview

This document defines the comprehensive benchmarking methodology for measuring DGM-Chess performance across multiple configurations and establishing baseline comparisons.

## Table of Contents

1. [Benchmark Configurations](#benchmark-configurations)
2. [Test Sets & Data](#test-sets--data)
3. [Performance Metrics](#performance-metrics)
4. [Baseline Establishment](#baseline-establishment)
5. [Evaluation Schedule](#evaluation-schedule)
6. [Statistical Analysis](#statistical-analysis)

---

## Benchmark Configurations

### Primary Test Configurations

We will evaluate performance across these distinct configurations:

#### 1. DeepSeek R1 Base Model
**Configuration**: `baseline_deepseek_base`
```python
- Model: DeepSeek R1:14b
- Tools: None
- Evolution: Disabled
- Prompt: Basic chess analysis prompt
- Context Management: Standard
```
**Purpose**: Establish base model chess capability

#### 2. DeepSeek R1 + Enhanced Tools (No Evolution)
**Configuration**: `deepseek_tools_no_evolution`
```python
- Model: DeepSeek R1:14b
- Tools: chess_position, chess_moves, lichess_puzzle, bash, editor
- Evolution: Disabled
- Prompt: Enhanced TOOL_CALL format
- Context Management: Priority-based caching
```
**Purpose**: Measure tool integration impact

#### 3. DeepSeek R1 + Tools + Evolution (Full DGM)
**Configuration**: `deepseek_dgm_full`
```python
- Model: DeepSeek R1:14b
- Tools: 5 base tools + agent-created tools
- Evolution: Enabled (80 generations)
- Prompt: Enhanced + self-modification capabilities
- Context Management: Full priority caching system
```
**Purpose**: Measure complete DGM system performance

#### 4. Original Paper Simulation
**Configuration**: `paper_baseline_simulation`
```python
- Model: Claude 3.5 Sonnet (if available)
- Tools: bash, edit (adapted for chess)
- Evolution: Paper-exact algorithm
- Prompt: XML-style tool format
- Context Management: Standard
```
**Purpose**: Compare against original paper methodology

---

## Test Sets & Data

### Puzzle Collection Strategy

#### Training Set
**Source**: Lichess Puzzle Database
```
- Rating Range: 800-1000
- Puzzle Count: 1000 puzzles
- Themes: Mixed (tactical, strategic, endgame)
- Usage: Agent evaluation during evolution
- Refresh: Every 10 generations to prevent overfitting
```

#### Validation Set  
**Source**: Lichess Puzzle Database
```
- Rating Range: 1000-1200  
- Puzzle Count: 500 puzzles
- Themes: Mixed
- Usage: Performance tracking during evolution
- Refresh: Never (consistent comparison)
```

#### Test Set (Hold-out)
**Source**: Curated collection
```
- Rating Range: 800-1400
- Puzzle Count: 200 puzzles
- Themes: Balanced distribution
- Usage: Final evaluation only
- Composition:
  * 50 puzzles: Tactical (pins, forks, skewers)
  * 50 puzzles: Strategic (pawn structure, piece activity)
  * 50 puzzles: Endgame (checkmate patterns, pawn endings)
  * 50 puzzles: Mixed complexity
```

### Puzzle Theme Distribution

| Theme | Training % | Validation % | Test % |
|-------|------------|--------------|--------|
| **Tactical** | 40% | 40% | 25% |
| - Fork | 10% | 10% | 8% |
| - Pin | 10% | 10% | 8% |
| - Skewer | 8% | 8% | 4% |
| - Discovery | 12% | 12% | 5% |
| **Strategic** | 35% | 35% | 25% |
| - Pawn Structure | 15% | 15% | 10% |
| - Piece Activity | 12% | 12% | 8% |
| - King Safety | 8% | 8% | 7% |
| **Endgame** | 20% | 20% | 25% |
| - Checkmate | 12% | 12% | 15% |
| - Pawn Endings | 8% | 8% | 10% |
| **Mixed** | 5% | 5% | 25% |

### Engine Game Benchmarks

#### Stockfish Levels
```
Level 1: ELO ~800  (10 games per agent)
Level 3: ELO ~1200 (10 games per agent) 
Level 5: ELO ~1600 (5 games per agent)
```

#### Game Conditions
```
- Time Control: 5+3 (5 minutes + 3 second increment)
- Opening Book: Disabled
- Endgame Tablebase: 3-4 piece tablebases only
- Agent Color: Alternating (50% white, 50% black)
```

---

## Performance Metrics

### Primary Metrics

#### 1. Puzzle Accuracy
```python
accuracy = correct_solutions / total_puzzles
```
**Range**: 0.0 to 1.0
**Target**: >0.60 for evolved agents

#### 2. Legal Move Rate
```python
legal_move_rate = legal_moves / total_moves
```
**Range**: 0.0 to 1.0
**Minimum**: 0.80 for functional agents

#### 3. Engine Win Rate
```python
engine_win_rate = wins / total_games
```
**Range**: 0.0 to 1.0
**Baseline**: ~0.15 for Stockfish Level 3

### Secondary Metrics

#### 4. Tool Usage Efficiency
```python
tool_usage_rate = puzzles_with_tool_use / total_puzzles
relevant_tool_rate = relevant_tool_calls / total_tool_calls
```

#### 5. Analysis Depth
```python
analysis_depth = average_words_per_response
calculation_depth = average_variations_considered
```

#### 6. Response Quality
```python
response_coherence = manual_evaluation_score  # 1-5 scale
chess_terminology_usage = chess_terms / total_words
```

### Evolution-Specific Metrics

#### 7. Improvement Rate
```python
generation_improvement = (gen_n_performance - gen_n-1_performance) / gen_n-1_performance
```

#### 8. Tool Creation Rate
```python
tools_per_generation = new_tools_created / generation
tool_usefulness = tools_actually_used / tools_created
```

#### 9. Code Complexity Evolution
```python
code_lines = total_lines_of_code
cyclomatic_complexity = complexity_metric
```

---

## Baseline Establishment

### Pre-Training Baseline Collection

#### Phase 1: Base Model Performance (Day 1)
```
Test: DeepSeek R1 base model on test set
- 200 chess puzzles (no tools, no evolution)
- Standard chess analysis prompt
- Single-shot evaluation (no retries)
- Record: accuracy, legal move rate, response time
```

#### Phase 2: Tool Integration Impact (Day 2)  
```
Test: DeepSeek R1 + enhanced tools (no evolution)
- Same 200 puzzle test set
- Enhanced TOOL_CALL prompts
- All 5 chess tools available
- Record: accuracy, legal move rate, tool usage patterns
```

#### Phase 3: Prompt Engineering Impact (Day 3)
```
Test: Original XML format vs Enhanced TOOL_CALL format
- Same DeepSeek R1 + tools configuration
- A/B test on 100 puzzle subset
- Compare: accuracy, parsing reliability, response time
```

### Baseline Performance Targets

**Expected Baseline Performance**:
```
DeepSeek R1 Base:               25% ± 5% puzzle accuracy
DeepSeek R1 + Tools:           35% ± 5% puzzle accuracy  
DeepSeek R1 + Enhanced Prompts: 40% ± 5% puzzle accuracy
```

**Target DGM Improvement**:
```
Generation 20:  45% ± 5% puzzle accuracy
Generation 40:  50% ± 5% puzzle accuracy  
Generation 60:  55% ± 5% puzzle accuracy
Generation 80:  60% ± 5% puzzle accuracy (success criteria)
```

---

## Evaluation Schedule

### During Evolution Training

#### Continuous Monitoring (Every Generation)
- Agent functionality validation (Stage 1 evaluation)
- Performance tracking on training set
- Tool creation logging
- Resource usage monitoring

#### Validation Checkpoints (Every 10 Generations)
```
Generations: 10, 20, 30, 40, 50, 60, 70, 80
Test: Best agent from each checkpoint on validation set
Record: All primary and secondary metrics
Compare: Against baseline and previous checkpoints
```

#### Deep Analysis (Every 20 Generations)
```
Generations: 20, 40, 60, 80
Test: Top 3 agents on engine games
Analysis: Tool usage patterns, code evolution
Documentation: Qualitative changes and emergent behaviors
```

### Post-Training Evaluation

#### Final Test Set Evaluation
```
Test: Best agent from each configuration on hold-out test set
Duration: 1 week after evolution completion
Analysis: Statistical significance, effect sizes
Report: Complete performance comparison
```

#### Cross-Configuration Analysis
```
Compare: All 4 configurations on identical test conditions
Metrics: All primary and secondary metrics
Statistics: ANOVA, post-hoc tests, confidence intervals
```

---

## Statistical Analysis

### Significance Testing

#### Puzzle Accuracy Comparisons
```python
# Compare configurations using McNemar's test for paired binary outcomes
from scipy.stats import mcnemar

def compare_configurations(config_a_results, config_b_results):
    """Compare puzzle-solving accuracy between configurations"""
    contingency_table = create_2x2_table(config_a_results, config_b_results)
    statistic, p_value = mcnemar(contingency_table)
    return statistic, p_value

# Effect size calculation
def cohens_h(p1, p2):
    """Effect size for proportion differences"""
    return 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
```

#### Evolution Progress Analysis
```python
# Time series analysis of improvement over generations
from scipy.stats import linregress

def analyze_improvement_trend(generation_scores):
    """Analyze linear trend in performance over generations"""
    generations = range(len(generation_scores))
    slope, intercept, r_value, p_value, std_err = linregress(generations, generation_scores)
    return {
        'improvement_rate': slope,
        'r_squared': r_value**2,
        'significance': p_value,
        'confidence_interval': (slope - 1.96*std_err, slope + 1.96*std_err)
    }
```

### Confidence Intervals

#### Performance Metrics
```python
# Bootstrap confidence intervals for accuracy
def bootstrap_ci(data, n_bootstrap=10000, ci_level=0.95):
    """Calculate bootstrap confidence interval for accuracy"""
    bootstrap_accuracies = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_accuracies.append(np.mean(sample))
    
    alpha = 1 - ci_level
    lower = np.percentile(bootstrap_accuracies, 100 * alpha/2)
    upper = np.percentile(bootstrap_accuracies, 100 * (1 - alpha/2))
    return lower, upper
```

### Power Analysis

#### Sample Size Justification
```python
# Power analysis for detecting meaningful differences
def calculate_required_sample_size(effect_size=0.1, alpha=0.05, power=0.8):
    """Calculate required puzzle count for detecting 10% accuracy difference"""
    from statsmodels.stats.power import ttest_power
    
    # For proportion test
    required_n = smp.zt_ind_solve_power(
        effect_size=effect_size, 
        alpha=alpha, 
        power=power
    )
    return math.ceil(required_n)

# Result: ~200 puzzles needed for 80% power to detect 10% difference
```

### Reporting Framework

#### Performance Report Template
```markdown
# DGM-Chess Benchmark Results

## Configuration Performance
| Configuration | Puzzle Accuracy | 95% CI | Legal Move Rate | Engine Win Rate |
|---------------|-----------------|--------|------------------|-----------------|
| Base Model    | 27.3%          | [22.1%, 32.5%] | 89.2% | 8.1% |
| + Tools       | 38.7%          | [33.2%, 44.2%] | 94.6% | 12.4% |
| + Evolution   | 58.9%          | [53.1%, 64.7%] | 96.8% | 23.7% |

## Statistical Comparisons
- Base vs Tools: p < 0.001, Cohen's h = 0.24 (small-medium effect)
- Tools vs Evolution: p < 0.001, Cohen's h = 0.41 (medium-large effect)
- Base vs Evolution: p < 0.001, Cohen's h = 0.65 (large effect)

## Evolution Analysis
- Average improvement per generation: +0.31% ± 0.08%
- Linear trend significance: p < 0.001, R² = 0.67
- Tools created: 23 total, 18 actively used (78% usefulness)
```

---

## Data Collection Automation

### Benchmark Execution Scripts

#### Baseline Collection
```bash
# scripts/collect_baselines.sh
python3 benchmark_base_model.py --output baseline_results.json
python3 benchmark_tools_only.py --output tools_results.json  
python3 benchmark_prompt_comparison.py --output prompt_results.json
```

#### Evolution Monitoring
```python
# benchmark_monitor.py
class EvolutionBenchmark:
    def __init__(self):
        self.validation_puzzles = load_validation_set()
        self.test_puzzles = load_test_set()
        
    def checkpoint_evaluation(self, generation, agent_id):
        """Evaluate agent at generation checkpoint"""
        results = {
            'generation': generation,
            'agent_id': agent_id,
            'timestamp': datetime.now().isoformat(),
            'validation_accuracy': self.evaluate_on_validation(agent_id),
            'tool_usage': self.analyze_tool_usage(agent_id),
            'code_complexity': self.measure_complexity(agent_id)
        }
        
        self.save_checkpoint_results(results)
        return results
```

---

*Last Updated: [Date]*
*Version: 1.0*
