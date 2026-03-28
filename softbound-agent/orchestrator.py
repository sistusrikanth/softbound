from __future__ import annotations

# -----------------------------
# Imports: agents and core types
# -----------------------------

import argparse
import os
from pathlib import Path

from core.llm_client import is_available
from core.session_store import load_session, save_session
from agents import IntentAgent, AudienceAgent, WorldAgent, StoryAgent

DEFAULT_SESSION_PATH = Path(__file__).resolve().parent / ".softbound_session.json"


# -----------------------------
# Orchestrator
# -----------------------------

class CreativeOrchestrator:
    def run(
        self,
        *,
        load_path: str | None = None,
        store_path: str | None = None,
    ) -> None:
        print("\n--- INITIALIZING CREATIVE SESSION ---")
        backend = os.environ.get("SOFTBOUND_LLM_BACKEND", "").strip().lower() or "openrouter"
        if is_available():
            print(f"LLM backend: {backend or 'openrouter'} (ready)")
        else:
            print("WARNING: LLM not available. Set OPENROUTER_API_KEY for API, or SOFTBOUND_LLM_BACKEND=local for local model. Agents will use fallback only.")

        if load_path:
            path = Path(load_path)
            intent, audience, world = load_session(path)
            print(f"---------------- Loaded session from {path} (skipping LLM for layers 1–3) ---")
            print(f"Intent: {intent}")
            print(f"Audience: {audience}")
            print(f"World: {world}")
        else:
            # Intent: same semantics as original (warm, pastoral, calm low-tech, safety/belonging)
            intent_input = {
                "artist_style": "warm, slow village life based in Canadian wilderness",  # slow village life based in India
                # "product_philosophy": "calm, low-tech, co-play",
                # "emotional_promise": "safety, belonging, gentle curiosity",
            }
            intent = IntentAgent().create(intent_input)
            print("---------------- Layer 1: Intent Agent ---")
            print(f"{intent}")

            audience_input = {
                "age_range": "5",
                # "emotional_needs": "security, comfort",
                # "attention_span": "short",
                # "culture": "Indian culture",
                # "coplay": "bedtime with parent",
            }
            audience = AudienceAgent().create(audience_input)
            print("---------------- Layer 2: Audience Agent ---")
            print(f"Audience: {audience}")

            world_agent = WorldAgent()
            world = world_agent.create(intent, audience)
            print("---------------- Layer 3: World Agent ---")
            print(f"World: {world}")

        if store_path is not None:
            out = Path(store_path)
            save_session(out, intent, audience, world)
            print(f"---------------- Saved intent, audience, world to {out} ---")

        story = StoryAgent().create(world, intent, audience)

        print("---------------- Layer 4: Story Agent ---")
        print(f"Theme (short label): {story.theme}")
        print(f"Story full_output ({len(story.full_output)} chars):")
        print(story.full_output)


# -----------------------------
# Run
# -----------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Softbound creative orchestrator (intent → audience → world → story).")
    parser.add_argument(
        "--load",
        type=str,
        default=None,
        metavar="PATH",
        help="Load intent, audience, and world from JSON; skip LLM for layers 1–3.",
    )
    parser.add_argument(
        "--store",
        nargs="?",
        default=None,
        const=str(DEFAULT_SESSION_PATH),
        metavar="PATH",
        help=(
            "After intent/audience/world are ready, save them to JSON (before story LLM). "
            f"If omitted with --store, default is {DEFAULT_SESSION_PATH.name} next to orchestrator.py."
        ),
    )
    args = parser.parse_args()
    CreativeOrchestrator().run(load_path=args.load, store_path=args.store)


if __name__ == "__main__":
    main()
