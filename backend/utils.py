import random
import re
import requests

"""
Utility functions for AI Storyteller backend, including:
- trim_incomplete_sentences: Trims text to the last complete sentence. Useful due to
  AI models sometimes returning incomplete sentences at the end of generated content.
- get_action_outcome: If an input ends in try/wish/attempt, returns one of
  success, partial success, critical success, failure, or critical failure.
- call_ai_api: Makes a POST request to an AI API with error handling for various scenarios
  (HTTP errors, timeouts, connection issues, and unexpected exceptions). 
  Returns either the API response data or an error message with an appropriate status code.
"""
def trim_incomplete_sentences(text):
    last_period_index = text.rfind(".")

    if last_period_index == -1:
        return text

    trimmed = text[:last_period_index + 1]

    # Close quote if trim cuts off dialogue
    if trimmed.count('"') % 2:
        trimmed += '"'

    return trimmed

def get_action_outcome(text):
    """
    Return a random outcome for action.
    Returns one of:
      - "Success." (20 %)
      - "Partial success." (20 %)
      - "Critical success." (10 %)
      - "Failure." (40 %)
      - "Critical failure." (10 %)

    "Advantage" and "disadvantage" words are detected as modifiers in the text  
    and give +-15 % to success chance.
    """
    if not isinstance(text, str):
        return None

    trimmed_text = text.strip()
    if not trimmed_text:
        return None

    if not re.search(r'\b(?:try|wish|attempt)\b', trimmed_text, re.IGNORECASE):
        return None

    success_threshold = 0.5
    if re.search(r'\bdisadvantage\b', trimmed_text, re.IGNORECASE):
        success_threshold += 0.15
    elif re.search(r'\badvantage\b', trimmed_text, re.IGNORECASE):
        success_threshold -= 0.15

    partial_threshold = success_threshold + 0.2
    crit_success_threshold = 0.9
    crit_failure_threshold = 0.1

    roll = random.random()
    succeeded = roll > success_threshold

    if succeeded:
        if roll > crit_success_threshold:
            return 'Critical success.'
        if roll < partial_threshold:
            return 'Partial success.'
        return 'Success.'

    if roll < crit_failure_threshold:
        return 'Critical failure.'

    return 'Failure.'

def call_ai_api(api_url, headers, payload):
    try:
        # Call external AI API with 30-second timeout
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)

        raw_body = response.text

        # Try to parse JSON
        try:
            data = response.json()
        except ValueError:
            data = None

        # Handle HTTP errors explicitly
        if response.status_code == 400:
            message = "Bad request."

            if data and "error" in data:
                message = data["error"].get("message", message)

            return None, (message, 400)

        if response.status_code == 429:
            return None, ("Rate limit exceeded. Wait or increase rate limit.", 429)

        if response.status_code == 401:
            return None, ("Unauthorized. Check your API key and permissions.", 401)

        if response.status_code >= 500:
            return None, ("AI service is currently unavailable.", 503)

        if response.status_code != 200:
            return None, (f"Unexpected error: {response.text}", response.status_code)

        # Return data if valid, otherwise return error
        if data:
            return data, None
        else:
            detail = raw_body.strip()
            if len(detail) > 500:
                detail = detail[:500] + '...'
            return None, (f"Invalid response from AI API. Response body: {detail}", 502)

    except requests.exceptions.Timeout:
        return None, ("Request timed out. Please try again.", 504)

    except requests.exceptions.ConnectionError:
        return None, ("Failed to connect to AI service.", 503)

    except Exception as e:
        return None, (f"Unexpected error: {str(e)}", 500)