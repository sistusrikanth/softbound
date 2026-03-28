#!/usr/bin/env python3
"""
Softbound — lightweight image generator (250×250px).
Runs locally on Mac using a small diffusion model. Output is sketch art style.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image, ImageFilter


OUTPUT_SIZE = 250
MODEL_SIZE = 512  # generate higher-res for detail, then downscale to OUTPUT_SIZE

# tiny = fast & small (~200MB). sd15 = better quality (~4GB).
MODELS = {
    "tiny": "segmind/tiny-sd",
    "sd15": "runwayml/stable-diffusion-v1-5",
}
DEFAULT_MODEL = "tiny"
DEFAULT_STEPS = 40
DEFAULT_GUIDANCE = 7.5
# Appended to every prompt so the model outputs sketch art.
SKETCH_PROMPT_SUFFIX = (
    ", pencil sketch, hand drawn, detailed line art, sketch art style, "
    "charcoal drawing, artistic sketch, fine lines"
)
NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
    "disfigured, poorly drawn, mutation, extra limbs, photograph, realistic, 3d render"
)
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def get_device():
    """Use MPS (Apple Silicon GPU) if available, else CPU."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def to_sketch_art(img: Image.Image) -> Image.Image:
    """Pencil-sketch effect: grayscale + color-dodge blend for hand-drawn look."""
    gray = img.convert("L")
    inv = Image.eval(gray, lambda x: 255 - x)
    blurred = inv.filter(ImageFilter.GaussianBlur(radius=2))
    w, h = gray.size
    base = gray.load()
    blend = blurred.load()
    out = Image.new("L", (w, h))
    pix = out.load()
    for y in range(h):
        for x in range(w):
            b = blend[x, y]
            if b >= 255:
                b = 254
            pix[x, y] = min(255, (base[x, y] * 256) // (256 - b))
    return out.convert("RGB")


def load_pipeline(device: torch.device, model_key: str = DEFAULT_MODEL):
    """Load the diffusion pipeline (lazy, cached)."""
    model_id = MODELS.get(model_key, MODELS[DEFAULT_MODEL])
    dtype = torch.float16 if device.type == "mps" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
        safety_checker=None,
    )
    pipe = pipe.to(device)
    if device.type == "cpu":
        pipe.enable_attention_slicing()
    return pipe


def generate(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    steps: int = DEFAULT_STEPS,
    guidance: float = DEFAULT_GUIDANCE,
    seed: int | None = None,
    out_path: Path | None = None,
) -> Path:
    """Generate a 250×250 sketch-art image from a text prompt. Returns path to saved file."""
    device = get_device()
    pipe = load_pipeline(device, model_key=model)

    generator = None
    if seed is not None:
        generator = torch.Generator(device=device).manual_seed(seed)

    full_prompt = prompt.rstrip() + SKETCH_PROMPT_SUFFIX
    image = pipe(
        prompt=full_prompt,
        negative_prompt=NEGATIVE_PROMPT,
        height=MODEL_SIZE,
        width=MODEL_SIZE,
        num_inference_steps=steps,
        guidance_scale=guidance,
        generator=generator,
    ).images[0]

    image_out = image
    if image_out.size != (OUTPUT_SIZE, OUTPUT_SIZE):
        image_out = image_out.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
        image_out = image_out.filter(ImageFilter.UnsharpMask(radius=0.5, percent=80, threshold=2))
    image_out = to_sketch_art(image_out)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if out_path is None:
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in prompt)[:50]
        out_path = OUTPUT_DIR / f"{safe_name.strip() or 'image'}.png"
    else:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

    image_out.save(out_path)
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate a 250×250 sketch art image from a text prompt (runs locally)."
    )
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        default="Rooster on a rustic meadow",
        help="Text description of the image (default: Rooster on a rustic meadow)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output file path (default: output/<prompt>.png)",
    )
    parser.add_argument(
        "-s", "--steps",
        type=int,
        default=DEFAULT_STEPS,
        help=f"Inference steps (default: {DEFAULT_STEPS}, higher = better quality)",
    )
    parser.add_argument(
        "-g", "--guidance",
        type=float,
        default=DEFAULT_GUIDANCE,
        help=f"Guidance scale, prompt adherence (default: {DEFAULT_GUIDANCE})",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        choices=list(MODELS.keys()),
        default=DEFAULT_MODEL,
        help=f"Model: tiny (fast, ~200MB) or sd15 (better quality, ~4GB). Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()

    print(f"Device: {get_device()}", file=sys.stderr)
    print(f"Model: {args.model} ({MODELS[args.model]})", file=sys.stderr)
    print(f"Prompt: {args.prompt!r}", file=sys.stderr)
    print("Generating...", file=sys.stderr)

    out_path = generate(
        args.prompt,
        model=args.model,
        steps=args.steps,
        guidance=args.guidance,
        seed=args.seed,
        out_path=args.output,
    )
    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
