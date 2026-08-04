# Converts AI Dungeon story cards to a custom context card format. (https://play.aidungeon.com/)
# 1. Export story cards from scenario.
# 2. Name file 'story_cards.json' and add to same folder as this file.
# 3. Navigate to folder in terminal and run: `py convert_story_cards.py`
# Context cards are saved to file 'context_cards.json' and can be added to your save file
# in backend/files/{save_id}

import json

def transform_story_cards(cards):
    """
    Transform AI Dungeon story cards into the custom context_cards format.
    """
    context_cards = []
    id = 1

    for card in cards:
        card_type = card.get("type", "").strip().lower()

        if card_type == "character":
            new_type = "character"
        elif card_type == "location":
            new_type = "location"
        else:
            new_type = "other"

        new_card = {
            "id": id,
            "name": card.get("title", ""),
            "type": new_type,
            "content": card.get("value", ""),
            "keywords": [
                k.strip()
                for k in card.get("keys", "").split(",")
                if k.strip()
            ],
        }

        if new_type == "character":
            new_card.update({
                "create_memories": False,
                "memories": [],
                "relationship_memories": {}
            })

        elif new_type == "location":
            new_card.update({
                "parent_location": "",
                "child_locations": [],
                "create_memories": False,
                "memories": []
            })

        context_cards.append(new_card)
        id += 1

    return {"context_cards": context_cards}


def convert_file(input_file, output_file):
    """Load an AI Dungeon JSON file, convert it, and save the result."""
    with open(input_file, "r", encoding="utf-8") as f:
        cards = json.load(f)

    converted = transform_story_cards(cards)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    convert_file("story_cards.json", "context_cards.json")