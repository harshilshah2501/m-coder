# Enhanced RAG Implementation Guide

## Overview

This implementation provides **Option 3 (Enhanced RAG)** as a stepping stone to **Option 1 (Agentic Wrapper)**.

### What This Solves

Your fine-tuned model is excellent at generating diffs but struggles with:
- ❌ Determining which files to create vs modify
- ❌ Finding reference patterns autonomously
- ❌ Understanding task context without explicit guidance

This enhanced RAG system adds:
- ✅ **Intent Detection**: Classifies queries as CREATE, MODIFY, REFACTOR, etc.
- ✅ **Smart Context Gathering**: Fetches ALL relevant files based on intent
- ✅ **Explicit File Lists**: Tells the model exactly what to create/modify
- ✅ **Reference Patterns**: Provides templates from similar entities

---

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Enhanced RAG Service                                        │
│                                                             │
│  1. Intent Detector                                         │
│     ├─ Detects: CREATE, MODIFY, REFACTOR, EXPLAIN, DEBUG   │
│     ├─ Extracts: Entities (CorrectionProfile)              │
│     └─ Identifies: Task type (api, configstore, schema)    │
│                                                             │
│  2. Context Gatherer                                        │
│     ├─ Finds similar entities (CredentialProfile)          │
│     ├─ Reads reference files (API, Store, Schema)          │
│     ├─ Extracts patterns (registration, initialization)    │
│     └─ Builds file lists (create vs modify)                │
│                                                             │
│  3. Prompt Builder                                          │
│     ├─ Creates intent-specific prompts                     │
│     ├─ Includes explicit file lists                        │
│     ├─ Provides reference code                             │
│     └─ Specifies output format                             │
└─────────────────────────────────────────────────────────────┘
    ↓
Optimized Prompt → Your Fine-tuned Model → High-quality Diffs
```

---

## Components

### 1. Intent Detector (`intent_detector.py`)

**Purpose**: Classify user queries into actionable intents

**Intents Supported**:
- `CREATE`: Create new classes/files
- `MODIFY`: Modify existing code
- `REFACTOR`: Improve code quality
- `EXPLAIN`: Explain how code works
- `DEBUG`: Fix bugs/issues
- `SEARCH`: Find code

**Example**:
```python
detector = IntentDetector()
result = detector.detect("Create CorrectionProfile API")

# Output:
# Intent: CREATE (confidence: 0.9)
# Entities: ['CorrectionProfile']
# Task Type: 'api'
```

### 2. Context Gatherer (`context_gatherer.py`)

**Purpose**: Fetch comprehensive context based on intent

**For CREATE tasks**:
- Finds similar entities (e.g., CredentialProfile for CorrectionProfile)
- Reads reference files (API class, ConfigStore, Schema)
- Extracts registration patterns from APIRouter
- Builds explicit file lists

**For MODIFY tasks**:
- Locates existing files
- Reads current code
- Identifies dependencies

**Example**:
```python
gatherer = ContextGatherer(qdrant_client, "/path/to/codebase")
context = gatherer.gather(intent_result, query)

# Output:
# {
#   'files_to_create': [
#     'src/main/java/com/mindarray/api/CorrectionProfile.java',
#     'src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java',
#     'src/main/resources/entity-schemas/correction-profiles.json'
#   ],
#   'files_to_modify': [
#     'src/main/java/com/mindarray/api/APIRouter.java'
#   ],
#   'reference_files': {
#     'api_class': '[CredentialProfile.java content]',
#     'config_store': '[CredentialProfileConfigStore.java content]',
#     'schema': '[credential-profiles.json content]'
#   },
#   'patterns': {
#     'registration': 'new CredentialProfile().init(settingsAPIRouter);'
#   }
# }
```

### 3. Prompt Builder (`prompt_builder.py`)

**Purpose**: Build intent-specific prompts with explicit instructions

**Key Features**:
- Different templates for CREATE vs MODIFY vs REFACTOR
- Explicit file lists (no guessing!)
- Reference code snippets
- Clear output format requirements

**Example Prompt Structure** (CREATE):
```
**USER REQUEST**: Create CorrectionProfile API

**REFERENCE PATTERNS**:
[CredentialProfile.java code]
[CredentialProfileConfigStore.java code]

**FILES TO CREATE** (3 files):
1. src/main/java/com/mindarray/api/CorrectionProfile.java
2. src/main/java/com/mindarray/store/CorrectionProfileConfigStore.java
3. src/main/resources/entity-schemas/correction-profiles.json

**FILES TO MODIFY** (1 file):
1. src/main/java/com/mindarray/api/APIRouter.java

**REGISTRATION PATTERN**:
new CredentialProfile().init(settingsAPIRouter);

**OUTPUT FORMAT**:
<thinking>
[analysis]
</thinking>

<code>
[complete code for new files]
[diffs for modified files]
</code>
```

### 4. Enhanced RAG Service (`enhanced_rag_service.py`)

**Purpose**: Orchestrate the entire pipeline

**Usage**:
```python
service = EnhancedRAGService(qdrant_client, codebase_root)

# Process query
response = service.process_query("Create CorrectionProfile API")

# Get optimized prompt
prompt = response['prompt']

# Send to your fine-tuned model
model_output = your_model.generate(prompt)
```

---

## Integration Steps

### Week 1: Phase 1 - Enhanced RAG

#### Step 1: Install Dependencies
```bash
pip install qdrant-client
```

#### Step 2: Configure Paths
Edit `context_gatherer.py` to match your codebase structure:
```python
self.patterns = {
    'api': 'src/main/java/com/mindarray/api',
    'store': 'src/main/java/com/mindarray/store',
    'schema': 'src/main/resources/entity-schemas',
    'router': 'src/main/java/com/mindarray/api/APIRouter.java',
}
```

#### Step 3: Test Intent Detection
```bash
python test_enhanced_rag.py
```

#### Step 4: Integrate with Your Model
```python
from enhanced_rag_service import EnhancedRAGService

# Initialize
service = EnhancedRAGService(qdrant_client, "/path/to/motadata")

# Process query
response = service.process_query(user_query)

# Send to model
model_output = your_finetuned_model.generate(response['prompt'])
```

#### Step 5: Evaluate Improvement
Compare before/after on your test cases:
- CorrectionProfile creation
- Multi-file modifications
- Complex refactoring tasks

---

## Expected Improvements

### Before (Current V14)
```
User: "Create CorrectionProfile API"

Model receives:
- Generic RAG context (maybe CredentialProfile.java)
- No explicit file list
- No task structure

Model outputs:
❌ Tries to modify CorrectionProfile.java (doesn't exist!)
❌ Misses ConfigStore creation
❌ Forgets APIRouter registration
❌ No schema file
```

### After (Enhanced RAG)
```
User: "Create CorrectionProfile API"

Model receives:
- Intent: CREATE (confidence: 0.9)
- Entities: [CorrectionProfile]
- Files to CREATE: [3 files listed explicitly]
- Files to MODIFY: [APIRouter.java]
- Reference code: [CredentialProfile patterns]
- Registration pattern: [exact code to copy]

Model outputs:
✅ Creates CorrectionProfile.java (complete code)
✅ Creates CorrectionProfileConfigStore.java (complete code)
✅ Creates correction-profiles.json (complete schema)
✅ Modifies APIRouter.java (proper diff with registration)
```

---

## Phase 2: Evolution to Agentic Wrapper (Weeks 2-4)

Once Phase 1 is working, evolve to a true agentic system:

### Architecture
```python
class AgenticCodeAssistant:
    def __init__(self, finetuned_model, enhanced_rag):
        self.model = finetuned_model
        self.rag = enhanced_rag
        self.tools = {
            'list_files': self.list_files,
            'read_file': self.read_file,
            'search_code': self.search_code,
            'generate_code': self.model.generate,
        }

    def process_request(self, user_query):
        # Phase 1: Planning
        plan = self._create_plan(user_query)

        # Phase 2: Exploration
        context = self._explore(plan)

        # Phase 3: Generation
        code = self._generate(plan, context)

        # Phase 4: Validation
        validated = self._validate(code)

        return validated

    def _create_plan(self, query):
        """Use model to create step-by-step plan"""
        planning_prompt = f"""
        Analyze this request and create a plan:
        {query}

        Output format:
        1. [Step 1]
        2. [Step 2]
        ...
        """
        return self.model.generate(planning_prompt)

    def _explore(self, plan):
        """Execute exploration steps"""
        context = {}
        for step in plan.steps:
            if step.requires_file_list:
                context['files'] = self.list_files(step.directory)
            if step.requires_file_read:
                context['code'] = self.read_file(step.file_path)
            if step.requires_search:
                context['search_results'] = self.search_code(step.query)
        return context

    def _generate(self, plan, context):
        """Generate code using enhanced RAG"""
        response = self.rag.process_query(plan.original_query)
        prompt = response['prompt']

        # Add exploration context
        prompt += f"\n\n**EXPLORATION RESULTS**:\n{context}"

        return self.model.generate(prompt)

    def _validate(self, code):
        """Validate generated code"""
        # Check syntax, imports, consistency
        return code
```

### Benefits of Agentic Wrapper
- ✅ Multi-step reasoning
- ✅ Dynamic exploration
- ✅ Self-correction
- ✅ Validation loops
- ✅ True autonomy

---

## Metrics to Track

### Phase 1 (Enhanced RAG)
- **Intent Detection Accuracy**: % of queries correctly classified
- **File List Accuracy**: % of correct files identified
- **Reference Quality**: % of relevant reference code retrieved
- **Model Success Rate**: % of tasks completed correctly

### Phase 2 (Agentic Wrapper)
- **Planning Quality**: % of plans that lead to success
- **Exploration Efficiency**: Avg. number of tool calls per task
- **Self-Correction Rate**: % of errors caught and fixed
- **End-to-End Success**: % of tasks completed without human intervention

---

## Troubleshooting

### Issue: Intent detection is wrong
**Solution**: Add more patterns to `IntentDetector.CREATE_PATTERNS`, etc.

### Issue: Can't find similar entities
**Solution**: Improve `_similarity_score()` in `ContextGatherer`

### Issue: Model still generates wrong files
**Solution**: Make file lists more explicit in prompt template

### Issue: Reference code is too long
**Solution**: Truncate reference files to key sections (imports, class signature, key methods)

---

## Next Steps

1. **Week 1**: Implement and test Enhanced RAG
2. **Week 2**: Evaluate on 20 diverse tasks
3. **Week 3**: Iterate on prompt templates
4. **Week 4**: Begin agentic wrapper development

---

## Success Criteria

### Phase 1 Complete When:
- ✅ 80%+ intent detection accuracy
- ✅ 90%+ correct file lists for CREATE tasks
- ✅ 70%+ model success rate (up from ~40% current)

### Phase 2 Complete When:
- ✅ 90%+ model success rate
- ✅ Handles complex multi-step tasks
- ✅ Self-corrects common errors
- ✅ Matches Claude-level performance on your use cases

---

## Conclusion

**You don't need to retrain your model.** Your fine-tuned model is excellent at diff generation. You just need to:

1. **Give it better context** (Phase 1: Enhanced RAG)
2. **Add agentic capabilities** (Phase 2: Wrapper)

This approach:
- ✅ Leverages your existing investment
- ✅ Delivers quick wins (1 week)
- ✅ Provides clear evolution path
- ✅ Achieves your goals without massive retraining

**Start with Phase 1 this week. You'll see immediate improvement.**


