# SFT Dataset Configuration

## Instruction Data Sources
data_sources:
  - source: "motadata_docs"
    path: "./raw/motadata_instructions.jsonl"
    format: "instruction_response"
    
  - source: "code_patterns"
    path: "./raw/code_patterns.jsonl"
    format: "instruction_response"

## Data Format Expected
```json
{
  "instruction": "Complete the Motadata EventRouter class...",
  "response": "public void route(Event event) { eventBus.publish(event); }",
  "category": "class_completion"
}
```

## Processing Pipeline
1. Load raw instruction data
2. Validate instruction-response pairs
3. Tokenize and truncate to max_length
4. Split into train/validation (e.g., 90/10)
5. Save as JSONL with prepared data

## Statistics
- Expected train samples: TBD
- Expected validation samples: TBD
- Max sequence length: 512 tokens
- Format: JSONL (one JSON per line)

## Notes
- Instructions should be clear and actionable
- Responses should demonstrate Motadata patterns
- Include diverse categories: class, method, registration, handler, async
