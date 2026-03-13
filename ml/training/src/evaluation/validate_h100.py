from unsloth import FastLanguageModel
import torch

# CONFIGURATION
# Update this path to where train_h100.py saved the adapter
ADAPTER_PATH = "/home/harshil/Harshil-PoCs/Finetuning/training_outputs/h100_run/lora_model" 
MAX_SEQ_LENGTH = 4096

print(f"🔄 Loading Adapter from: {ADAPTER_PATH}")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = ADAPTER_PATH,
    max_seq_length = MAX_SEQ_LENGTH,
    dtype = None,
    load_in_4bit = True,
)
FastLanguageModel.for_inference(model)

def run_test(name, messages):
    print(f"\n{'='*20} TEST: {name} {'='*20}")
    print(f"❓ User: {messages[-1]['content']}")
    
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize = True,
        add_generation_prompt = True,
        return_tensors = "pt",
    ).to("cuda")

    outputs = model.generate(
        input_ids = inputs,
        max_new_tokens = 256,
        use_cache = True,
        temperature = 0.1, # Low temp for deterministic checks
    )
    
    response = tokenizer.batch_decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)[0]
    print(f"🤖 Model:\n{response}")
    print("="*50)

# --- TEST CASES ---

# 1. The "Hallucination Check" (Type A)
# We re-run the prompt that failed earlier to see if H100 training fixed it.
# EXPECTATION: Should name a real class (e.g., AbstractApiVerticle) OR provide a specific Motadata pattern.
run_test("REST API Base Class", [
    {"role": "system", "content": "You are a Principal Software Engineer at Motadata."},
    {"role": "user", "content": "I need to create a new REST API. What base class should I use?"}
])

# 2. Tool Usage (Type C)
# EXPECTATION: Should output a VALID JSON tool call, not text.
run_test("Tool Call - Method Search", [
    {"role": "system", "content": "You are a code assistant with access to codebase search tools."},
    {"role": "user", "content": "Find all methods in FlowSettingsConfigStore that are related to 'update'."}
])

# 3. Patch Generation (Type B)
# EXPECTATION: Should output a valid Unified Diff (header, chunks) and NOT markdown text.
run_test("Patch Generation", [
    {"role": "system", "content": "You are a senior developer providing code patches."},
    {"role": "user", "content": "File: com/mindarray/util/Logger.java\nInstruction: Change the default log level from INFO to DEBUG."}
])
