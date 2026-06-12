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

    # Replace curly quotes with straight quotes
    trimmed = trimmed.replace('“', '"').replace('”', '"').replace("’", "'").replace("‘", "'")

    # Close quote if trim cuts off dialogue
    if trimmed.count('"') % 2:
        trimmed += '"'

    return trimmed

def get_action_outcome(text):
    """
    Return a random outcome for action.
    Returns one of:
      - "success." (20 %)
      - "partial success." (20 %)
      - "critical success." (10 %)
      - "failure." (40 %)
      - "critical failure." (10 %)

    "Advantage" and "disadvantage" words are detected as modifiers in the text  
    and give +-20 % to success chance.
    """
    if not isinstance(text, str):
        return None

    trimmed_text = text.strip()
    if not trimmed_text:
        return None

    # Base chances
    crit_failure = 0.10
    failure = 0.40
    partial = 0.20
    success = 0.20
    crit_success = 0.10

    # Modifiers
    if re.search(r'\bdisadvantage\b', trimmed_text, re.IGNORECASE):
        failure += 0.20      # -> 60 % chance
        partial -= 0.05      # -> 15 % chance
        success -= 0.10      # -> 10 % chance
        crit_success -= 0.05 # -> 5 % chance

    elif re.search(r'\badvantage\b', trimmed_text, re.IGNORECASE):
        failure -= 0.20
        partial += 0.10
        success += 0.10

    roll = random.random()

    threshold = 0

    threshold += crit_failure
    if roll < threshold:
        return 'critical failure.'

    threshold += failure
    if roll < threshold:
        return 'failure.'

    threshold += partial
    if roll < threshold:
        return 'partial success.'

    threshold += success
    if roll < threshold:
        return 'success.'

    return 'critical success.'

def call_ai_api(api_url, headers, payload):
    try:
        # Call external AI API with 90-second timeout
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)

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
            if len(detail) > 40:
                detail = detail[:40] + '...'
            return None, (f"Invalid response from AI API. Response body: {detail}", 502)

    except requests.exceptions.Timeout:
        return None, ("Request timed out. Please try again.", 504)

    except requests.exceptions.ConnectionError:
        return None, ("Failed to connect to AI service.", 503)

    except Exception as e:
        return None, (f"Unexpected error: {str(e)}", 500)