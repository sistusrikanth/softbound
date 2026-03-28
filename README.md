# Softbound

Lightweight **sketch art** image generator (250×250 px) that runs **locally on your Mac**. Uses a small diffusion model and a pencil-sketch post-process; no external APIs.

## Example prompt

```bash
python generate.py "Rooster on a rustic meadow"
```

Output is saved as `output/Rooster on a rustic meadow.png` (250×250, pencil-sketch style).

## Setup

```bash
cd softbound
python -m venv .venv
source .venv/bin/activate   # on Mac/Linux
pip install -r requirements.txt
```

First run will download the model (~200MB) from Hugging Face.

## Usage

```bash
# Default prompt: "Rooster on a rustic meadow"
python generate.py

# Better quality (Stable Diffusion 1.5, ~4GB download, slower)
python generate.py "Rooster on a rustic meadow" -m sd15

# Custom prompt
python generate.py "A cat sleeping on a windowsill"

# Save to a specific file
python generate.py "Mountain at sunset" -o my_image.png

# Higher quality (more steps, ~30–45s)
python generate.py "Ship in a bottle" -s 50

# Faster draft (fewer steps)
python generate.py "Ship in a bottle" -s 20

# Reproducible result
python generate.py "Abstract shapes" --seed 42
```

## Options

| Option | Description |
|--------|-------------|
| `prompt` | Text description of the image |
| `-m`, `--model` | `tiny` (fast, ~200MB) or `sd15` (better quality, ~4GB). Default: tiny |
| `-o`, `--output` | Output file path |
| `-s`, `--steps` | Inference steps (default: 40, higher = better quality) |
| `-g`, `--guidance` | Guidance scale (default: 7.5) |
| `--seed` | Random seed for reproducibility |

## Requirements

- Python 3.10+
- Mac (uses Apple Silicon GPU via MPS when available, else CPU)
- ~2GB disk for model cache

## How it works

- **Models:** `tiny` = [Segmind Tiny-SD](https://huggingface.co/segmind/tiny-sd) (fast, small). `sd15` = [Stable Diffusion 1.5](https://huggingface.co/runwayml/stable-diffusion-v1-5) (better quality, larger).
- Prompts are augmented with sketch-style keywords; output is then passed through a **pencil-sketch** filter (grayscale, hand-drawn look).
- Generates at **512×512** for better detail, then downscales to 250×250 and applies the sketch effect.
- Uses a negative prompt to reduce blur and photorealism; 40 steps and guidance scale 7.5 by default.
- Runs fully offline after the first model download.
