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
from .ref_sanitizer import (
    conf_sanitize,
    ref_sanitize,
    should_apply_conf_sanitizer,
    should_apply_ref_sanitizer,
)


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
        self._debug_enabled = (os.environ.get("STAGE6C_DEBUG") or "").strip() == "1"
        self._ref_fail_closed = (os.environ.get("STAGE6C_REF_FAIL_CLOSED") or "").strip() == "1"

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

        if self._debug_enabled:
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

    def generate(
        self,
        messages: List[Dict[str, Any]],
        expected_phase: str | None = None,
        boundary_string: str | None = None,
    ) -> Dict[str, Any]:
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
        if self._debug_enabled and not getattr(self, "_printed_prompt", False):
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
        content = result.text.strip()

        apply_sanitizer, gate_path, expected_phase_seen = should_apply_ref_sanitizer(
            messages,
            expected_phase=expected_phase,
            fail_closed=self._ref_fail_closed,
        )
        ref_sanitize_reasons: List[str] = []
        ref_sanitized = False
        if apply_sanitizer:
            content, ref_sanitized, ref_sanitize_reasons = ref_sanitize(content)
            if self._debug_enabled and ref_sanitized:
                print(
                    "[STAGE6C][QWEN25][REF_SANITIZER] "
                    f"triggered=1 gate={gate_path} expected_phase={expected_phase_seen or 'missing'} "
                    f"reasons={','.join(ref_sanitize_reasons)}"
                )

        apply_conf_sanitizer, conf_gate_path, expected_phase_seen_conf = should_apply_conf_sanitizer(
            messages,
            expected_phase=expected_phase,
        )
        conf_sanitize_reasons: List[str] = []
        conf_sanitized = False
        if apply_conf_sanitizer:
            content, conf_sanitized, conf_sanitize_reasons = conf_sanitize(content)
            if self._debug_enabled and conf_sanitized:
                print(
                    "[STAGE6C][QWEN25][CONF_SANITIZER] "
                    f"triggered=1 gate={conf_gate_path} expected_phase={expected_phase_seen_conf or 'missing'} "
                    f"reasons={','.join(conf_sanitize_reasons)}"
                )

        phase_for_boundary = expected_phase_seen_conf or expected_phase_seen
        boundary = (boundary_string or "").strip()
        if phase_for_boundary in ("REF", "CONF") and boundary:
            if boundary not in content:
                content = f"{boundary}\n{content}"
                if self._debug_enabled:
                    print(
                        "[STAGE6C][QWEN25][BOUNDARY_PREFIX] "
                        f"applied=1 phase={phase_for_boundary}"
                    )

        return {
            "content": content,
            "model": self.model_id(),
            "tokens": len(result.token_ids),
            "sanitized": ref_sanitized or conf_sanitized,
            "sanitize_reasons": sorted(set(ref_sanitize_reasons + conf_sanitize_reasons)),
            "expected_phase_seen": expected_phase_seen,
            "ref_gate_path": gate_path,
            "ref_sanitizer_applied": ref_sanitized,
            "ref_sanitize_reasons": ref_sanitize_reasons,
            "conf_sanitizer_applied": conf_sanitized,
            "conf_sanitize_reasons": conf_sanitize_reasons,
            "conf_gate_path": conf_gate_path,
            "expected_phase_seen_conf": expected_phase_seen_conf,
        }