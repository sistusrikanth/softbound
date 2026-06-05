#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:3000}"

echo "Using BASE_URL=${BASE_URL}"
echo

echo "==> Health"
curl -s "${BASE_URL}/health"
echo -e "\n"

echo "==> Expand description"
curl -s -X POST "${BASE_URL}/api/expand-description" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A rustic canadian winter landscape",
    "world_style": "Atmospheric / Nordic–Scottish Storybook Aesthetic. The muted palette and nocturnal woodland scenes give it a, Moody, Nature-centric, Quiet, contemplative feel"
  }'
echo -e "\n"

echo "==> Suggest characters"
curl -s -X POST "http://localhost:3000/api/suggest-characters" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A rustic canadian winter landscape",
    "world_style": "Atmospheric / Nordic–Scottish Storybook Aesthetic. The muted palette and nocturnal woodland scenes give it a, Moody, Nature-centric, Quiet, contemplative feel",
    "expanded_description": "Deep in the northern reaches, where the maps fray at the edges, the village lay hushed under a heavy quilt of indigo twilight. Here, winter was not merely a season, but a living presence that breathed in long, frosted plumes of mist. The rustic cabins, built from sturdy, silver-barked spruce, huddled close together like shivering kin, their stone chimneys exhaling thin ribbons of peat-scented smoke into the crisp, biting air. \n\nBeyond the threshold of the last lantern-lit porch, the boreal forest stood as a wall of jagged, ink-black silhouettes against a sky bruised with shades of violet and slate. Every branch was heavy with the weight of pristine, powder-soft snow, creating a landscape of muffled echoes and crystalline silence. There was no sound save for the occasional sharp *crack* of a freezing timber or the distant, lonely hoot of a great horned owl. In this remote corner of the world, the stars burned with a cold, piercing intensity, watching over the village as it drifted into a dreamless, frozen slumber.",
    "existing_characters": [
      {"name": "Pip", "description": "A small bright orange and white fox who is very curious and brave"}
    ],
    "count": 2
  }'
echo -e "\n"

echo "==> Generate style prompt"
curl -s -X POST "${BASE_URL}/api/generate-style-prompt" \
  -H "Content-Type: application/json" \
  -d '{
    "style_description": "dark fantasy, melancholic",
    "text": "A city built on the bones of a dead god"
  }'
echo -e "\n"

echo "==> Generate world (standalone)"
curl -s -X POST "${BASE_URL}/api/world" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A city built on the bones of a dead god",
    "characters": ["Mira, a scavenger"],
    "world_style": "dark fantasy, melancholic"
  }'
echo -e "\n"

echo "==> Generate world (agentic with trace)"
curl -s -X POST "${BASE_URL}/api/world" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Floating islands connected by silk bridges",
    "characters": [],
    "world_style": "whimsical steampunk",
    "mode": "agentic",
    "max_iterations": 2,
    "include_trace": true
  }'
echo -e "\n"

echo "All requests completed."

echo
echo "==> Studio: generate bible"
curl -s -X POST "${BASE_URL}/api/studio/bible/generate" \
  -H "Content-Type: application/json" \
  -d '{"seed": "a sleepy lighthouse on a foggy coast", "preset_id": "lighthouse"}'
echo -e "\n"

echo "==> Studio: seed cast"
curl -s -X POST "${BASE_URL}/api/studio/cast/seed" \
  -H "Content-Type: application/json" \
  -d '{"seed": "rooster meadow", "preset_id": "meadow", "count": 3}'
echo -e "\n"

echo "==> Studio: propose stories"
curl -s -X POST "${BASE_URL}/api/studio/stories/propose" \
  -H "Content-Type: application/json" \
  -d '{"bible": {"title": "Rooster meadow", "logline": "a quiet meadow", "paras": [{"heading": "the place", "text": "a warm meadow"}]}, "count": 2}'
echo -e "\n"

echo "Studio requests completed."
