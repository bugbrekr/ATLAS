import bottle
import json
import os
import models

from pprint import pprint

class JSONBottle(bottle.Bottle):
    def default_error_handler(self, res):
        bottle.response.content_type = 'application/json'
        return json.dumps({
            "success": False,
            "error": res.body
        })

app = JSONBottle()

def _check_auth_token(token):
    try:
        auth_file = os.path.join('config/auth/', 'auth_tokens')
        if not os.path.exists(auth_file):
            return False
        with open(auth_file) as f:
            valid_tokens = {line.strip() for line in f if line.strip()}
        return token in valid_tokens
    except:
        return False

def require_auth(func):
    def wrapper(*args, **kwargs):
        auth_token = bottle.request.headers.get('Authorization')
        if not auth_token or not _check_auth_token(auth_token):
            bottle.response.status = 401
            return {"error": "Unauthorized"}
        return func(*args, **kwargs)
    return wrapper

@app.route("/process_hass_user", method="POST")
@require_auth
def process_hass_user():
    print(bottle.request.json)
    prompt = models.hass.PromptPayload(bottle.request.json)
    print(prompt)
    response_payload = {
        "tts_text": "Hello, World!",
        "new_history": [
            {"role": "user", "content": prompt.text},
            {"role": "assistant", "content": ""}
        ],
        "continue_conversation": False
    }
    return {
        "success": True,
        "data": response_payload
    }

if __name__ == "__main__":
    bottle.run(app, host='0.0.0.0', port=8054)
