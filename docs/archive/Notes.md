🚀 Starting Motadata Finetuned Model Evaluation...
   Running 10 test cases

[1/10] Running: Query Class Methods... ❌ Score: 2/5 (9928ms)
[2/10] Running: AbstractConfigStore Knowledge... ✅ Score: 5/5 (676ms)
[3/10] Running: EventBus Architecture... ❌ Score: 2/5 (112ms)
[4/10] Running: Create Full API Feature... ❌ Score: 1/5 (19754ms)
[5/10] Running: New Monitor Plugin... ❌ Score: 1/5 (350ms)
[6/10] Running: NullPointer RCA... ✅ Score: 5/5 (546ms)
[7/10] Running: Timeout RCA... ❌ Score: 2/5 (399ms)
[8/10] Running: API Pattern Review... ❌ Score: 2/5 (284ms)
[9/10] Running: ConfigStore Review... ❌ Score: 2/5 (1892ms)
[10/10] Running: Memory Leak Analysis... ✅ Score: 5/5 (2166ms)

📄 Report saved to: /home/harshil/Harshil-PoCs/Finetuning/finetuning_evaluation_report.json

======================================================================
   MOTADATA FINETUNED MODEL EVALUATION REPORT
======================================================================

Generated: 2025-12-11T10:33:38.799404
Endpoint: http://localhost:8080/v1/chat/completions

----------------------------------------------------------------------
SUMMARY
----------------------------------------------------------------------
  Overall Pass Rate:    3/10 (30.0%)
  Average Score:        2.70/5
  Tool Obsession Rate:  20.0%
  Repetition Rate:      20.0%
  Avg Response Time:    3610ms

  ⚠️  CRITICAL ISSUES:
      • LOW QUALITY: Average score 2.70/5 is below threshold

----------------------------------------------------------------------
CATEGORY BREAKDOWN
----------------------------------------------------------------------
  ❌ TYPE_A_KNOWLEDGE: 1/3 passed, avg score: 3.00/5
  ❌ TYPE_B_MULTIFILE: 0/2 passed, avg score: 1.00/5
  ⚠️ RCA_DEBUGGING: 1/2 passed, avg score: 3.50/5
  ❌ CODE_REVIEW: 0/2 passed, avg score: 2.00/5
  ✅ DIRECT_REASONING: 1/1 passed, avg score: 5.00/5

----------------------------------------------------------------------
DETAILED RESULTS
----------------------------------------------------------------------
  ❌ [A1] Query Class Methods: 2/5
       ⚠️ REPETITION_LOOP: Response contains repeated phrases/patterns
  ✅ [A2] AbstractConfigStore Knowledge: 5/5
  ❌ [A3] EventBus Architecture: 2/5
  ❌ [B1] Create Full API Feature: 1/5
       ⚠️ REPETITION_LOOP: Response contains repeated phrases/patterns
  ❌ [B2] New Monitor Plugin: 1/5
       ⚠️ TOOL_OBSESSION: Response contains tool/XML calls instead of direct answer
  ✅ [R1] NullPointer RCA: 5/5
  ❌ [R2] Timeout RCA: 2/5
       ⚠️ TOOL_OBSESSION: Response contains tool/XML calls instead of direct answer
  ❌ [C1] API Pattern Review: 2/5
  ❌ [C2] ConfigStore Review: 2/5
  ✅ [D1] Memory Leak Analysis: 5/5

----------------------------------------------------------------------
RECOMMENDATIONS
----------------------------------------------------------------------

  [HIGH] Tool Obsession
      Problem: 2 tests showed tool/XML output instead of direct answers
      Fix: Add 50-100 Dataset D examples (direct reasoning, no tools). Update system prompt to explicitly forbid tool calls.

  [HIGH] Repetition Loops
      Problem: 2 tests showed repeated content patterns
      Fix: Review training data for duplicates. Add repetition_penalty=1.2 to generation config.

  [MEDIUM] Low TYPE_A_KNOWLEDGE Performance
      Problem: Only 33.3% pass rate in TYPE_A_KNOWLEDGE
      Fix: Add more training examples for TYPE_A_KNOWLEDGE category

  [MEDIUM] Low TYPE_B_MULTIFILE Performance
      Problem: Only 0.0% pass rate in TYPE_B_MULTIFILE
      Fix: Add more training examples for TYPE_B_MULTIFILE category

  [MEDIUM] Low CODE_REVIEW Performance
      Problem: Only 0.0% pass rate in CODE_REVIEW
      Fix: Add more training examples for CODE_REVIEW category

  [HIGH] Knowledge Gaps / Hallucinations
      Problem: Model struggling with factual accuracy
      Fix: Implement RAG with Qdrant to ground responses in actual codebase

======================================================================

🚀 Starting Motadata Finetuned Model Evaluation...
   Running 10 test cases

[1/10] Running: Query Class Methods... ✅ Score: 3/5 (217ms)
[2/10] Running: AbstractConfigStore Knowledge... ✅ Score: 5/5 (890ms)
[3/10] Running: EventBus Architecture... ❌ Score: 2/5 (409ms)
[4/10] Running: Create Full API Feature... ✅ Score: 5/5 (3453ms)
[5/10] Running: New Monitor Plugin... ❌ Score: 1/5 (43ms)
[6/10] Running: NullPointer RCA... ✅ Score: 5/5 (541ms)
[7/10] Running: Timeout RCA... ❌ Score: 1/5 (43ms)
[8/10] Running: API Pattern Review... ❌ Score: 1/5 (52ms)
[9/10] Running: ConfigStore Review... ❌ Score: 1/5 (9998ms)
[10/10] Running: Memory Leak Analysis... ✅ Score: 5/5 (2116ms)

📄 Report saved to: /home/harshil/Harshil-PoCs/Finetuning/finetuning_evaluation_report.json

======================================================================
   MOTADATA FINETUNED MODEL EVALUATION REPORT
======================================================================

Generated: 2025-12-11T10:50:43.030301
Endpoint: http://localhost:8080/v1/chat/completions

----------------------------------------------------------------------
SUMMARY
----------------------------------------------------------------------
  Overall Pass Rate:    5/10 (50.0%)
  Average Score:        2.90/5
  Tool Obsession Rate:  0.0%
  Repetition Rate:      0.0%
  Avg Response Time:    1776ms

  ⚠️  CRITICAL ISSUES:
      • LOW QUALITY: Average score 2.90/5 is below threshold

----------------------------------------------------------------------
CATEGORY BREAKDOWN
----------------------------------------------------------------------
  ⚠️ TYPE_A_KNOWLEDGE: 2/3 passed, avg score: 3.33/5
  ⚠️ TYPE_B_MULTIFILE: 1/2 passed, avg score: 3.00/5
  ⚠️ RCA_DEBUGGING: 1/2 passed, avg score: 3.00/5
  ❌ CODE_REVIEW: 0/2 passed, avg score: 1.00/5
  ✅ DIRECT_REASONING: 1/1 passed, avg score: 5.00/5

----------------------------------------------------------------------
DETAILED RESULTS
----------------------------------------------------------------------
  ✅ [A1] Query Class Methods: 3/5
  ✅ [A2] AbstractConfigStore Knowledge: 5/5
  ❌ [A3] EventBus Architecture: 2/5
  ✅ [B1] Create Full API Feature: 5/5
  ❌ [B2] New Monitor Plugin: 1/5
       ⚠️ MINIMAL_RESPONSE: Response too short/empty
  ✅ [R1] NullPointer RCA: 5/5
  ❌ [R2] Timeout RCA: 1/5
       ⚠️ MINIMAL_RESPONSE: Response too short/empty
  ❌ [C1] API Pattern Review: 1/5
       ⚠️ MINIMAL_RESPONSE: Response too short/empty
  ❌ [C2] ConfigStore Review: 1/5
  ✅ [D1] Memory Leak Analysis: 5/5

----------------------------------------------------------------------
RECOMMENDATIONS
----------------------------------------------------------------------

  [MEDIUM] Low CODE_REVIEW Performance
      Problem: Only 0.0% pass rate in CODE_REVIEW
      Fix: Add more training examples for CODE_REVIEW category

  [HIGH] Knowledge Gaps / Hallucinations
      Problem: Model struggling with factual accuracy
      Fix: Implement RAG with Qdrant to ground responses in actual codebase

=====================================================================

Help design Dataset D (direct reasoning samples) to further improve quality?
Update the EVALUATION_SUMMARY.md with these new results?
Investigate the empty responses for tests B2 and R2?