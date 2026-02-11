from unsloth import FastLanguageModel

# Load model + adapter (PEFT)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "/home/harshil/Harshil-PoCs/Finetuning/training_outputs/h100_run/lora_model", # Your output dir
    max_seq_length = 16384,
    dtype = None,
    load_in_4bit = False,
)
FastLanguageModel.for_inference(model)

# Test Prompt (Use a sample from your test set)
prompt = """<|im_start|>user
Write a Java function to handle connection timeouts in Motadata context engine.<|im_end|>
<|im_start|>assistant
"""

inputs = tokenizer([prompt], return_tensors = "pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens = 200)
print(tokenizer.decode(outputs[0]))
