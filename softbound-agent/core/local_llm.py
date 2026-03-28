"""
Local lightweight LLM for Mac (CPU or Apple Silicon MPS).
Set SOFTBOUND_LLM_BACKEND=local to use.
Default: SmolLM2-360M (360M params, low memory). Optional SOFTBOUND_LOCAL_MODEL to override.
"""
from __future__ import annotations

import os

# 360M params — much lighter than 1.1B; reduces memory and avoids getting stuck
DEFAULT_LOCAL_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
MAX_INPUT_TOKENS = 512   # truncate long prompts to avoid OOM/hangs
MAX_NEW_TOKENS_LOCAL = 512   # cap generation length for local


def _make_sanitize_logits_processor():
    import torch
    from transformers.generation import LogitsProcessor, LogitsProcessorList

    class _SanitizeLogitsProcessor(LogitsProcessor):
        """Replaces nan/inf in logits and clamps to safe range so multinomial gets valid probabilities."""

        def __init__(self, clamp_min: float = -50.0, clamp_max: float = 50.0):
            self.clamp_min = clamp_min
            self.clamp_max = clamp_max

        def __call__(self, input_ids, scores):
            scores = torch.where(torch.isnan(scores), torch.full_like(scores, self.clamp_min), scores)
            scores = torch.where(torch.isposinf(scores), torch.full_like(scores, self.clamp_max), scores)
            scores = torch.where(torch.isneginf(scores), torch.full_like(scores, self.clamp_min), scores)
            scores = torch.clamp(scores, self.clamp_min, self.clamp_max)
            return scores

    return LogitsProcessorList([_SanitizeLogitsProcessor()])
_model = None
_tokenizer = None
_device = None


def _get_device():
    import torch
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _get_model_id() -> str:
    return os.environ.get("SOFTBOUND_LOCAL_MODEL", DEFAULT_LOCAL_MODEL)


def _load_model():
    global _model, _tokenizer, _device
    if _model is not None:
        return
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model_id = _get_model_id()
    _device = _get_device()
    dtype = torch.float32
    if _device.type == "mps":
        dtype = torch.float16
    # 8-bit needs NVIDIA GPU (bitsandbytes); leave off by default for Mac
    use_8bit = os.environ.get("SOFTBOUND_LOCAL_8BIT", "0").strip().lower() in ("1", "true", "yes")
    load_kw: dict = {"trust_remote_code": True}
    if use_8bit:
        try:
            from transformers import BitsAndBytesConfig
            load_kw["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
            load_kw["device_map"] = "auto"
        except ImportError:
            use_8bit = False
    if not use_8bit:
        load_kw["torch_dtype"] = dtype
        load_kw["device_map"] = None
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        _tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        try:
            _model = AutoModelForCausalLM.from_pretrained(model_id, **load_kw)
        except TypeError:
            load_kw.pop("quantization_config", None)
            if "torch_dtype" in load_kw:
                load_kw["dtype"] = load_kw.pop("torch_dtype")
            _model = AutoModelForCausalLM.from_pretrained(model_id, **load_kw)
    if load_kw.get("device_map") is None:
        _model = _model.to(_device)


def _model_device():
    """Device to put inputs on (model may use device_map='auto')."""
    if getattr(_model, "device", None) is not None:
        return _model.device
    return next(_model.parameters()).device


def complete(
    user_content: str,
    *,
    system_content: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    _load_model()
    import torch
    if system_content:
        prompt = f"<|system|>\n{system_content}\n<|user|>\n{user_content}\n<|assistant|>\n"
    else:
        prompt = f"<|user|>\n{user_content}\n<|assistant|>\n"
    # print(f"============= Prompt: {prompt} =============")
    try:
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        if hasattr(_tokenizer, "apply_chat_template") and _tokenizer.chat_template is not None:
            prompt = _tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
            )
    except Exception:
        pass
    inputs = _tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_TOKENS,
    )
    device = _model_device()
    inputs = {k: v.to(device) for k, v in inputs.items()}
    input_len = inputs["input_ids"].shape[1]
    max_new = min(max_tokens, MAX_NEW_TOKENS_LOCAL)
    with torch.no_grad():
        out = _model.generate(
            **inputs,
            max_new_tokens=max_new,
            temperature=max(temperature, 1e-5) if temperature > 0 else 1e-5,
            do_sample=temperature > 0,
            pad_token_id=_tokenizer.eos_token_id or _tokenizer.pad_token_id,
            top_p=0.9,
            logits_processor=_make_sanitize_logits_processor(),
        )
    generated = out[0][input_len:]
    text = _tokenizer.decode(generated, skip_special_tokens=True)
    return text.strip()


def is_available() -> bool:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        return True
    except ImportError:
        return False
