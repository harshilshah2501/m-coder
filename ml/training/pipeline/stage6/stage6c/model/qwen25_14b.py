from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from vllm import LLM, SamplingParams

try:
    from vllm.lora.request import LoRARequest
except Exception as _lora_import_error:  # pragma: no cover - env-dependent import
    LoRARequest = None
else:
    _lora_import_error = None

from .adapter import AdapterConfig, ModelAdapter


class Qwen25_14B_InstructAdapter(ModelAdapter):
    def __init__(
        self,
        model_path: str,
        max_tokens: int = 512,
    ) -> None:
        self._model_path = model_path
        self._max_tokens = int(max_tokens)
        self._lora_request = None
        self._lora_dirname = ""
        self._tokenizer = None

        debug_enabled = (os.environ.get("STAGE6C_DEBUG") or "").strip() == "1"
        eager_enabled = (os.environ.get("STAGE6C_EAGER") or "").strip() == "1"
        lora_path_raw = (os.environ.get("STAGE6C_LORA_PATH") or "").strip()

        lora_path: Path | None = None
        if lora_path_raw:
            candidate = Path(lora_path_raw)
            adapter_weights = candidate / "adapter_model.safetensors"
            adapter_config = candidate / "adapter_config.json"
            if (
                candidate.is_absolute()
                and candidate.is_dir()
                and adapter_weights.exists()
                and adapter_config.exists()
                and LoRARequest is not None
            ):
                lora_path = candidate

        if lora_path is not None:
            self._llm = LLM(
                model=model_path,
                dtype="bfloat16",
                tensor_parallel_size=1,
                enable_lora=True,
                max_loras=1,
                max_lora_rank=64,
                enforce_eager=eager_enabled,
            )
            self._lora_request = LoRARequest("stage08D", 1, lora_path=str(lora_path))
            self._lora_dirname = lora_path.name
        else:
            self._llm = LLM(
                model=model_path,
                dtype="bfloat16",
                tensor_parallel_size=1,
                enforce_eager=eager_enabled,
            )

        if debug_enabled:
            if self._lora_request is not None:
                print(f"[STAGE6C][QWEN25] lora_enabled=1 path={lora_path_raw}")
            else:
                print("[STAGE6C][QWEN25] lora_enabled=0 path=<none>")

        # Cache tokenizer once (important)
        try:
            self._tokenizer = self._llm.get_tokenizer()
        except Exception:
            self._tokenizer = None

        self._sampling = SamplingParams(
            temperature=0.0,
            top_p=1.0,
            top_k=-1,
            repetition_penalty=1.0,
            max_tokens=self._max_tokens,
            seed=0,
        )

    def model_id(self) -> str:
        if self._lora_request is not None and self._lora_dirname:
            return (
                f"qwen2.5-14b-instruct|vllm|bf16|max={self._max_tokens}"
                f"|lora={self._lora_dirname}"
            )
        return f"qwen2.5-14b-instruct|vllm|bf16|max={self._max_tokens}|base"

    def get_config(self) -> AdapterConfig:
        return AdapterConfig(
            temperature=0.0,
            top_p=1.0,
            max_tokens=self._max_tokens,
        )

    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        tokenizer = self._tokenizer

        if tokenizer is not None and hasattr(tokenizer, "apply_chat_template"):
            clean_messages = [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in messages
            ]
            prompt = tokenizer.apply_chat_template(
                clean_messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt = "".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}\n"
                for m in messages
            )

        # TEMP DEBUG: print prompt once (disable after confirmation)
        if not getattr(self, "_printed_prompt", False):
            self._printed_prompt = True
            print("=== STAGE6C_PROMPT_DEBUG_START ===")
            print(prompt[:2500])
            print("=== STAGE6C_PROMPT_DEBUG_END ===")
        
        if self._lora_request is not None:
            outputs = self._llm.generate(
                [prompt],
                self._sampling,
                lora_request=self._lora_request,
            )
        else:
            outputs = self._llm.generate([prompt], self._sampling)

        if not outputs or not outputs[0].outputs:
            raise RuntimeError("vLLM returned empty output")

        result = outputs[0].outputs[0]

        return {
            "content": result.text.strip(),
            "model": self.model_id(),
            "tokens": len(result.token_ids),
        }