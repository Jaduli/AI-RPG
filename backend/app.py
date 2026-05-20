from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import requests
import re
import os
import utils
import database
from prompts.asset_generation import (
    GENERATE_CHARACTER_SYS_PROMPT,
    GENERATE_LOCATION_SYS_PROMPT,
    GENERATE_ITEM_SYS_PROMPT,
    GENERATE_OTHER_SYS_PROMPT
)
from prompts.memory import (
    SUMMARIZATION_SYS_PROMPT, 
    MEMORY_SYS_PROMPT,
    CHARACTER_MEMORY_SYS_PROMPT,
    CHARACTER_MEMORY_RPG_SYS_PROMPT
)
from prompts.rpg import (
    RPG_SYS_PROMPT, 
    PLAYER_ACTION_SYS_PROMPT, 
    RECENT_ACTION_SYS_PROMPT, 
    OUTCOME_SYS_PROMPT
)
from prompts.storyteller import STORYTELLER_SYS_PROMPT

# Maximum file size for save files
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Initialize the database
database.init_db()

# Check if local AI is enabled via Docker compose environment variable 
# Default to false if not set
LOCAL_AI_ENABLED = os.getenv("LOCAL_AI_ENABLED", "false") == "true"

# Local Ollama model API endpoint and model
OLLAMA_URL = "http://ai:11434/api/chat"
OLLAMA_MODEL = "llama3.1:8b"

api_url = os.getenv("API_URL")
api_key = os.getenv("API_KEY")

api_main_model = os.getenv("API_MAIN_MODEL", None)
api_mem_model = os.getenv("API_MEM_MODEL", None)
env_gamemode = os.getenv("GAMEMODE", None)

app = Flask(__name__)
CORS(app)

# Directory to store story files
BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)


# Backend Routes #


"""
/config

Returns configuration settings.
"""
@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        "local_ai_enabled": LOCAL_AI_ENABLED,
        "main_model": api_main_model,
        "mem_model": api_mem_model,
        "gamemode": env_gamemode
    })

"""
/load

Load story file by filename. 
Returns 400 if filename or story_id is missing or invalid, 
404 if file not found, and 500 for other errors.
"""
@app.route('/api/load', methods=['GET'])
def load_file():
    story_id_str = request.args.get('story_id')
    story_id = int(story_id_str) if story_id_str.isdigit() else None

    # Validate story ID
    if not story_id or story_id <= 0:
        return jsonify({"error": "Story ID is required. ID must be a positive integer."}), 400

    path = os.path.join(BASE_DIR, str(story_id), 'save.json')

    # Ensure the real path is within the BASE_DIR to prevent directory traversal
    real_path = os.path.realpath(path)
    if not real_path.startswith(os.path.realpath(BASE_DIR)):
        return jsonify({"error": "Invalid path."}), 400

    # Ensure file exists before attempting to open
    if not os.path.exists(path):
        return jsonify({"error": "File not found."}), 404

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            story_name = data.get("story_name", '')
            instructions = data.get("instructions", '')
            content = data.get("content", '')
            summary = data.get("summary", '')
            essential_context = data.get("essential_context", '')
            memory_cursor = data.get("memory_cursor", 0)
            summary_cursor = data.get("summary_cursor", 0)
            context_cards = data.get("context_cards", [])
            player = data.get("player", [])
            inventory = data.get("inventory", [])
    except Exception as e:
        # Internal Server Error
        return jsonify({"error": str(e)}), 500

    return jsonify({"story_name": story_name, "instructions": instructions, "content": content, 
                    "summary": summary, "essential_context": essential_context, "memory_cursor": memory_cursor,
                    "summary_cursor":summary_cursor, "context_cards": context_cards, "player": player,
                    "inventory": inventory})

"""
/save

Save story to file. Valid story_id is required. 
Returns 400 if filename or story_id is missing or invalid,
413 (Payload Too Large) if file size exceeds set limit.
"""
@app.route('/api/save', methods=['POST'])
def save_file():
    data = request.json
    story_id = data.get("story_id")

    # Validate story ID
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400
    
    if not isinstance(story_id, int) or isinstance(story_id, bool) or story_id <= 0:
        return jsonify({"error": "Invalid story ID. ID must be a positive integer."}), 400
    
    story_name = data.get("story_name", '')
    if (story_name.strip() == ''):
        return jsonify({"error": "Story name is required."}), 400

    path = os.path.join(BASE_DIR, str(story_id))
    os.makedirs(path, exist_ok=True)
    save_path = os.path.join(path, 'save.json')

    # Ensure the real path is within the BASE_DIR to prevent directory traversal
    real_path = os.path.realpath(save_path)
    if not real_path.startswith(os.path.realpath(BASE_DIR)):
        return jsonify({"error": "Invalid path."}), 400
    
    # Create a backup of existing file. Only keep one backup per file.
    if os.path.exists(save_path):
        backup_path = os.path.join(path, 'backup.json')

        # If backup already exists, remove it
        if os.path.exists(backup_path):
            os.remove(backup_path)

        # Rename current file to backup
        os.rename(save_path, backup_path)

    # Get rest of saved data
    instructions = data.get("instructions", '')
    content = data.get("content", '')
    summary = data.get("summary", '')
    essential_context = data.get("essential_context", '')
    memory_cursor = data.get("memory_cursor", 0)
    summary_cursor = data.get("summary_cursor", 0)
    context_cards = data.get("context_cards", [])
    inventory = data.get("inventory", [])
    player = data.get("player_information", [])

    # Build payload
    save_data = {
        "story_name": story_name,
        "instructions": instructions,
        "content": content,
        "summary": summary,
        "essential_context": essential_context,
        "memory_cursor": memory_cursor,
        "summary_cursor": summary_cursor,
        "context_cards": context_cards,
        "player": player,
        "inventory": inventory
    }

    # Serialize to JSON
    json_string = json.dumps(save_data, ensure_ascii=False, indent=2)

    # Ensure file size doesn't exceed limit to prevent malicious file uploads and server overload
    file_size = len(json_string.encode('utf-8'))
    if file_size > MAX_FILE_SIZE:
        return jsonify({
            "error": f"File size exceeds limit of {MAX_FILE_SIZE // (1024 * 1024)} MB."
        }), 413

    # Save new file
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(json_string)

    return jsonify({"message": f"File saved with ID {str(story_id)}."})


"""
/get_save_files

Returns list of saved story files with their associated name and story IDs.
Returns 500 if error reading files.
"""
@app.route('/api/get_save_files', methods=['GET'])
def get_save_files():
    files = []
    try:
        for entry in os.scandir(BASE_DIR):
            if not entry.is_dir():
                continue
            story_id = int(entry.name) if entry.name.isdigit() else None

            if not story_id or story_id <= 0:
                continue

            save_file_path = os.path.join(entry.path, 'save.json')
            if not os.path.exists(save_file_path):
                continue
            try:
                with open(save_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                story_name = data.get("story_name", '')

                files.append({
                    "story_id": story_id,
                    "story_name": story_name
                })
            except (OSError, json.JSONDecodeError):
                # Skip corrupted or unreadable save files
                continue
    except OSError as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"files": files})

"""
/continue

Continue story using external AI API. 
Returns 400 for missing/invalid JSON, empty content, or missing model; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty content.
"""
@app.route('/api/continue', methods=['POST'])
def continue_story():
    # Validate request JSON
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    recent_story = data.get('recent_story')
    if not recent_story or recent_story.strip() == '':
        return jsonify({"error": "Empty story content."}), 400
    
    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    story_id = data.get('story_id')

    # Validate story ID
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400
    
    if not isinstance(story_id, int) or isinstance(story_id, bool) or story_id <= 0:
        return jsonify({"error": "Invalid story ID. ID must be a positive integer."}), 400
    
    gamemode = data.get('gamemode')
    user_instructions = data.get('instructions')
    essential_context = data.get('essential_context', 'None.')
    summary = data.get('summary', 'None.')
    context_cards = data.get('context_cards', 'None.')
    player_information = data.get('player_information', '')
    player_equipment = data.get('player_equipment', '')
    player_skills = data.get('player_skills', '')
    player_action = data.get('player_action', '')
    recent_action = data.get('recent_action', '')
    recent_outcome = data.get('recent_outcome', '')
    use_d20 = data.get('use_d20', False)

    top_p = data.get('top_p', 0.9)
    temperature = data.get('temperature', 0.8)
    max_tokens = data.get('max_tokens', 200)

    # Validate environment configuration
    if not api_url or not api_key:
        return jsonify({"error": "API_URL or API_KEY not set."}), 500
    
    full_instructions = ''

    if (gamemode == 'rpg'):
        full_instructions = RPG_SYS_PROMPT
    elif (gamemode == 'storyteller'):
        full_instructions = STORYTELLER_SYS_PROMPT
    else:
        return jsonify({"error": f"Game mode '{gamemode}' not recognized."}), 400
    
    # Get relevant memories for recent content
    relevant_memories = database.get_relevant_memories(recent_story[-2000:], story_id, 3)

    # Get most recent memories for story
    recent_memories = database.get_recent_memories(story_id, 2)

    # Combine and remove duplicate memories
    unique_memories = list(set(relevant_memories + recent_memories))

    memory_block = "\n".join(unique_memories) or "None."

    outcome = ''

    if (player_action and use_d20):
        outcome = utils.get_action_outcome(player_action)
    
    # Context ordered based on which content is most likely to stay static (unedited).
    # This will increase rate of cache hits in API call -> cheaper responses (if supported by API provider).
    full_prompt = (
        "[Essential Story Information]\n" + essential_context +
        ("\n\n[Player Information]\n" + player_information if player_information else "") +
        ("\n\n[Player Equipment]\n" + player_equipment if player_equipment else "") +
        ("\n\n[Player Skills]\n" + player_skills if player_skills else "") +
        ("\n\n[Story Summary]\n" + summary if summary else "") +
        "\n\n[Past Memories]\n" + memory_block +
        ("\n\n[Relevant Context]\n" + context_cards if context_cards else "") +
        ("\n\n[Recent Player Action]\n" + recent_action if recent_action else "") +
        ("\n\n[Recent Action Outcome]\n" + recent_outcome if recent_outcome else "") +
        "\n\n[Recent Story]\n" + recent_story +
        ("\n\n[Player Action]\n" + player_action if player_action else "") +
        ("\n\n[Action Outcome]\n" + outcome if outcome else "")
    )

    if (player_action):
        full_instructions += PLAYER_ACTION_SYS_PROMPT
    elif (recent_action):
        full_instructions += RECENT_ACTION_SYS_PROMPT

    if (outcome or recent_outcome):
        full_instructions += OUTCOME_SYS_PROMPT

    if (user_instructions.strip() != ''):
        full_instructions = (f"{full_instructions}\n{user_instructions}")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": full_instructions},
            {"role": "user", "content": full_prompt}
        ],
        "max_tokens": max_tokens,
        "top_p": top_p,
        "temperature": temperature,
        "presence_penalty": 0.3, # Increases the likelihood of introducing new content vs repeating existing content
        "frequency_penalty": 0.3 # Decreases the likelihood of repeating words or phrases
    }

    # Disable "thinking" phase for DeepSeek models to reduce output token use 
    # -> cheaper & faster responses.
    # May become redundant if model names are changed by API provider.
    if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
        payload["thinking"] = {"type": "disabled"}

    # Call external AI API with error handling
    result, error = utils.call_ai_api(api_url, headers, payload)

    if error:
        message, status = error
        return jsonify({"error": message}), status

    continued_content = result["choices"][0]["message"]["content"]

    if not continued_content or continued_content.strip() == '':
        return jsonify({"error": "AI API returned empty content."}), 500

    trimmed = utils.trim_incomplete_sentences(continued_content)

    full_context = '{---SYSTEM---}\n' + full_instructions + '\n\n{---USER---}\n\n' + full_prompt

    return jsonify({"continued_content": trimmed, "tokens_total": result['usage']['total_tokens'],
                    "full_context": full_context, "outcome": outcome})

"""
/summarize

Summarize story using external or local AI API.
Returns 400 for missing/invalid JSON, empty content, or missing model;
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty summary.
"""
@app.route('/api/summarize', methods=['POST'])
def summarize():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    if not content or content.strip() == '':
        return jsonify({"error": "Empty content."}), 400
    
    local = data.get('local')

    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    new_summary = ''
    tokens_total = -1

    if (local and local == True and LOCAL_AI_ENABLED):
        # Local summarization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 0.2, # Low temperature for good consistency
                "num_predict": 1000, # Token limit to prevent unnecessarily long responses
                "num_ctx": 8192 # Use 8k input token limit
            },
            "stream": False
        })

        if response.status_code == 200:
            try:
                response_data = response.json()
            except ValueError:
                return jsonify({"error": "Invalid JSON response from local AI service.", "detail": response.text}), 502

            new_summary = response_data.get("message", {}).get("content", '').strip()
            tokens_total = response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)

        else:
            return jsonify({"error": response.text}), response.status_code
    # Default to cloud  
    else:
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SUMMARIZATION_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }

        if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
            payload["thinking"] = {"type": "disabled"}

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_summary = result["choices"][0]["message"]["content"]

        tokens_total = result['usage']['total_tokens']

    trimmed = utils.trim_incomplete_sentences(new_summary)

    return jsonify({"summary": trimmed, "tokens_total": tokens_total})

"""
/memorize

Creates a memory using local or cloud AI. Memory is stored in the database.
Returns 400 for missing/invalid JSON, empty content, or missing model or story_id; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty content.
"""
@app.route('/api/memorize', methods=['POST'])
def memorize():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    content = data.get('content')
    if not content or content.strip() == '':
        return jsonify({"error": "Empty content."}), 400
    
    local = data.get('local')

    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400
    
    story_id = data.get('story_id')

    # Validate story ID
    if not story_id:
        return jsonify({"error": "Story ID is required."}), 400
    if not isinstance(story_id, int) or isinstance(story_id, bool) or story_id <= 0:
        return jsonify({"error": "Invalid story ID. ID must be a positive integer."}), 400
    
    new_memory = ''
    tokens_total = -1

    if (local and local == True and LOCAL_AI_ENABLED):
        # Local memorization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": MEMORY_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 0.0, # Low temperature for best consistency
                "num_predict": 200,
                "num_ctx": 8192
            },
            "stream": False
        })

        if response.status_code == 200:
            try:
                response_data = response.json()
            except ValueError:
                return jsonify({"error": "Invalid JSON response from local AI service.", "detail": response.text}), 502

            new_memory = response_data.get("message", {}).get("content", '').strip()

            # Some models often include metatext (e.g. "Here are the created memories:") in their output
            # even when explicitly instructed not to. The commented out function below removes the first
            # line of the output and can be used if encountering issues with metatext generation.
            # It was useful with llama:3 but switching to llama:3.1 seemed to lessen the issue.
            # 
            # new_memory = "\n".join(new_memory.splitlines()[1:]).lstrip("\n")

            tokens_total = response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)

        else:
            return jsonify({"error": response.text}), response.status_code
    # Default to cloud
    else:
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": MEMORY_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "temperature": 0.0,
            "max_tokens": 200
        }

        if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
            payload["thinking"] = {"type": "disabled"}

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_memory = result["choices"][0]["message"]["content"]

        tokens_total = result['usage']['total_tokens']

    trimmed = utils.trim_incomplete_sentences(new_memory)

    database.create_memory(story_id, trimmed)

    return jsonify({"memory": trimmed, "tokens_total": tokens_total})

"""
/generate_asset

Generates a story asset (e.g. character, location, or item) using local or cloud AI.
Returns 400 for missing/invalid JSON or missing asset type; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty content.
"""
@app.route('/api/generate_asset', methods=['POST'])
def generate_asset():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400

    asset_type = data.get('type')
    if not asset_type or asset_type.strip() == '':
        return jsonify({"error": "Missing asset type."}), 400
    
    local = data.get('local', False)
    name = data.get('name', '')
    story_information = data.get('story_information', '')
    recent_story = data.get('recent_story', '')

    content = ''
    if story_information:
        content += '[Story Information]\n' + story_information + '\n\n'

    if name:
        content += f'[Generation Context]\nNew {asset_type} name: ' + name

        # Only use recent story as context if name is given
        if recent_story:
            content += '\n\nRecent story: ' + recent_story
    
    generated_content = ''
    sys_prompt = ''
    tokens_total = -1

    match asset_type:
        case 'character':
            sys_prompt = GENERATE_CHARACTER_SYS_PROMPT
        case 'location':
            sys_prompt = GENERATE_LOCATION_SYS_PROMPT
        case 'item':
            sys_prompt = GENERATE_ITEM_SYS_PROMPT
        case _:
            sys_prompt = GENERATE_OTHER_SYS_PROMPT

    if (local == True and LOCAL_AI_ENABLED):
        # Local memorization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 1.1, # Average temperature for good consistency & creativity
                "num_predict": 200,
                "num_ctx": 8192
            },
            "stream": False
        })

        if response.status_code == 200:
            try:
                response_data = response.json()
            except ValueError:
                return jsonify({"error": "Invalid JSON response from local AI service.", "detail": response.text}), 502

            generated_content = response_data.get("message", {}).get("content", '').strip()

            tokens_total = response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)

        else:
            return jsonify({"error": response.text}), response.status_code
    # Default to cloud
    else:
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": content}
            ],
            "temperature": 1.1,
            "max_tokens": 200
        }

        if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
            payload["thinking"] = {"type": "disabled"}

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        generated_content = result["choices"][0]["message"]["content"]

        tokens_total = result['usage']['total_tokens']

    trimmed = utils.trim_incomplete_sentences(generated_content)

    app.logger.info("Content used in asset generation:\n" + content)
    app.logger.info("Tokens used in asset generation: %s", tokens_total)

    return jsonify({"generated_content": trimmed, "tokens_total": tokens_total})

"""
/generate_character_memory

Generates a character memory using local or cloud AI.
Returns 400 for missing/invalid JSON or missing asset type; 
API call errors with appropriate status codes (from utils.call_ai_api);
500 for server or API key errors, or if AI API returns empty content.
"""
@app.route('/api/generate_character_memory', methods=['POST'])
def generate_character_memory():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Missing or invalid JSON body."}), 400

    model = data.get('model')
    if not model:
        return jsonify({"error": "Model is required."}), 400

    local = data.get('local', False)
    gamemode = data.get('gamemode', '')
    story_information = data.get('story_information', '')
    player = data.get('player', '')
    character_name = data.get('character_name', '')
    character_description = data.get('character_description', '')
    recent_story = data.get('recent_story', '')

    content = ''
    
    # Build context for memory
    content += '[Story Information]\n' + story_information + '\n\n'
    content += '[Player]\nPlayer Name: ' + player + '\n\n'

    content += '[Character]\nCharacter Name: ' + character_name + '\n'
    content += 'Character Description: ' + character_description + '\n\n'
    
    content += '\n[Recent Story]\n'
    content += recent_story
    
    new_memory = ''
    tokens_total = -1

    sys_prompt = CHARACTER_MEMORY_SYS_PROMPT

    if gamemode == 'rpg':
        sys_prompt = CHARACTER_MEMORY_RPG_SYS_PROMPT

    if (local == True and LOCAL_AI_ENABLED):
        # Local memorization using Ollama API
        response = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": content}
            ],
            "options": {
                "temperature": 0.8, # Below average temperature for good consistency with some creativity
                "num_predict": 50, # Small-ish limit as one memory should only be one sentence long
                "num_ctx": 8192
            },
            "stream": False
        })

        if response.status_code == 200:
            try:
                response_data = response.json()
            except ValueError:
                return jsonify({"error": "Invalid JSON response from local AI service.", "detail": response.text}), 502

            new_memory = response_data.get("message", {}).get("content", '').strip()

            tokens_total = response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0)

        else:
            return jsonify({"error": response.text}), response.status_code
    # Default to cloud
    else:
        if not api_url or not api_key:
            return jsonify({"error": "API_URL or API_KEY not set."}), 500

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": CHARACTER_MEMORY_SYS_PROMPT},
                {"role": "user", "content": content}
            ],
            "temperature": 0.8,
            "max_tokens": 50
        }

        if model in ("deepseek-v4-flash", "deepseek-v4-pro"):
            payload["thinking"] = {"type": "disabled"}

        # Call external AI API with error handling
        result, error = utils.call_ai_api(api_url, headers, payload)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        new_memory = result["choices"][0]["message"]["content"]

        tokens_total = result['usage']['total_tokens']

    app.logger.info("Content used in asset generation:\n" + content)
    app.logger.info("Tokens used in character memory generation: %s", tokens_total)

    return jsonify({"new_memory": new_memory, "tokens_total": tokens_total})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
