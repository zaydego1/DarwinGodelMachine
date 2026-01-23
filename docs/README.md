# Chess DGM Documentation

This directory contains comprehensive documentation for the Chess DGM (Darwin Gödel Machine) project.

---

## Document Overview

### 📋 [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
**Read this first for implementation details.**

Complete implementation plan with:
- Detailed root cause analysis
- Phase-by-phase implementation steps
- Exact code changes required
- Testing procedures
- Success criteria

**Use when:** You need detailed instructions for what to implement and how.

---

### 🚀 [SESSION_RESUME.md](./SESSION_RESUME.md)
**Quick reference for resuming work.**

Fast reference guide with:
- 30-second status check
- Quick tests
- Next actions for current phase
- Common issues & solutions
- File map

**Use when:** Starting a new session and need to quickly get oriented.

---

### 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md)
**Understanding how the system works.**

System architecture documentation:
- Component descriptions
- Data flow diagrams
- Design decisions
- Expected behavior
- Performance expectations

**Use when:** You need to understand how the system is supposed to work (when fixed).

---

### 📊 [Baseline_Results.md](./Baseline_Results.md)
**Current performance data.**

Baseline test results showing:
- Tool calling attempts vs successes
- Legal move rates
- Puzzle accuracy
- Evidence of current issues

**Use when:** You need data about current system performance.

---

## Quick Start Guide

### If You're New to This Project
1. Read **ARCHITECTURE.md** first (understand the system)
2. Read **IMPLEMENTATION_PLAN.md** (understand what's broken and how to fix it)
3. Bookmark **SESSION_RESUME.md** (use this every session)

### If You're Continuing Work
1. Open **SESSION_RESUME.md**
2. Check "Current Phase" at the top
3. Run the quick tests
4. Go to relevant section in **IMPLEMENTATION_PLAN.md**
5. Continue implementation

### If You're Debugging
1. Check **SESSION_RESUME.md** "Common Issues" section
2. Check **ARCHITECTURE.md** "Debugging Guide" section
3. Add diagnostic logging per **IMPLEMENTATION_PLAN.md** Phase 1.1

---

## Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| IMPLEMENTATION_PLAN.md | ✅ Complete | 2025-11-15 |
| SESSION_RESUME.md | ✅ Complete | 2025-11-15 |
| ARCHITECTURE.md | ✅ Complete | 2025-11-15 |
| Baseline_Results.md | ⚠️ Needs update | - |

---

## Current Project Status

**Phase:** Analysis Complete, Ready for Implementation
**Priority:** Phase 1 - Fix Tool Execution
**Status:** 🔴 Tool calling broken

**Next Action:** Implement Phase 1.1 (Add Diagnostic Logging)

See [SESSION_RESUME.md](./SESSION_RESUME.md) for details.

---

## Contributing to Documentation

When updating these documents:

1. **Update "Last Updated" date** at the top of each document
2. **Update this README** if you add new documents
3. **Keep documents synchronized**:
   - If you complete a phase, update both IMPLEMENTATION_PLAN.md and SESSION_RESUME.md
   - If you discover new issues, document them in all relevant files
4. **Add test results** to Baseline_Results.md after running tests

---

## Document Relationships

```
┌──────────────────────┐
│   ARCHITECTURE.md    │  ← How system SHOULD work
│  (System Design)     │
└──────────────────────┘
           │
           ↓
┌──────────────────────┐
│IMPLEMENTATION_PLAN.md│  ← How to FIX the system
│   (Detailed Plan)    │
└──────────────────────┘
           │
           ↓
┌──────────────────────┐
│  SESSION_RESUME.md   │  ← Where to START today
│  (Quick Reference)   │
└──────────────────────┘
           │
           ↓
┌──────────────────────┐
│ Baseline_Results.md  │  ← Evidence of current state
│   (Test Results)     │
└──────────────────────┘
```

---

## External Resources

- **Original DGM Paper:** https://arxiv.org/abs/2505.22954
- **Project Repository:** https://github.com/jennyzzt/dgm
- **DeepSeek R1 Documentation:** https://github.com/deepseek-ai/DeepSeek-R1
- **Chess Library (python-chess):** https://python-chess.readthedocs.io/

---

## Key Concepts

### Darwin Gödel Machine (DGM)
A self-improving system that iteratively modifies its own code and validates changes empirically.

### Tool Calling
The mechanism by which LLMs can execute external functions (tools) to augment their capabilities.

### Staged Evaluation
Progressive evaluation system:
- Stage 1: Basic functionality (80% legal moves)
- Stage 2: Extended puzzles (40% accuracy)
- Stage 3: Engine games (win rate)

### Tool Creation
Creating specialized tools to compensate for LLM weaknesses identified through evaluation.

### ALPS Selection
Age-Layered Population Structure - evolutionary algorithm that maintains diversity.

---

## Troubleshooting Documentation

**Can't find what you need?**
1. Check the table of contents in each document
2. Use Ctrl+F to search for keywords
3. Check SESSION_RESUME.md "Common Issues" section
4. Check IMPLEMENTATION_PLAN.md "Root Cause Analysis" section

**Documents out of sync?**
- The "Last Updated" date shows which is most recent
- SESSION_RESUME.md should always reflect current state
- Report inconsistencies for fixing

---

## Maintenance

### After Completing a Phase
1. Update "Current Phase" in SESSION_RESUME.md
2. Check off completed items in IMPLEMENTATION_PLAN.md
3. Add any new learnings or issues discovered
4. Run tests and update Baseline_Results.md

### After Major Changes
1. Update ARCHITECTURE.md if behavior changes
2. Update IMPLEMENTATION_PLAN.md with new steps
3. Update SESSION_RESUME.md "Next Actions"

### Periodically
- Review all documents for consistency
- Update examples if code changes
- Add new debugging tips discovered
- Update performance expectations if improved

---

**Last Updated:** 2025-11-15
