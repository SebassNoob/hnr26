import os
import sys
import time
import base64
import json
from litellm import completion
from PIL import ImageGrab
from dotenv import load_dotenv

# --- Constants ---
DEFAULT_MODEL = "groq/meta-llama/llama-4-scout-17b-16e-instruct" 
CHECK_INTERVAL_SECONDS =  5*60  # 5 minutes

def _load_env():
    # Correctly locate the .env file at the project root
    if hasattr(sys, '_MEIPASS'):
        # In PyInstaller bundle
        base_dir = sys._MEIPASS
    else:
        # In development
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    env_path = os.path.join(base_dir, ".env")
    
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        print("WYD: Loaded environment variables from .env file.")
    else:
        print("WYD: .env file not found.")

def take_screenshot():
    """Takes a screenshot and returns the path to a temporary file."""
    try:
        screenshot = ImageGrab.grab()
        # --- FIX: Use a unique filename to avoid caching issues ---
        temp_dir = os.getenv("TEMP", "/tmp")
        temp_filename = f"urmom_screenshot_{int(time.time())}.jpg"
        temp_path = os.path.join(temp_dir, temp_filename)
        screenshot.save(temp_path, "JPEG")
        return temp_path
    except Exception as e:
        print(f"WYD Error taking screenshot: {e}")
        return None

def encode_image(image_path):
    """Encodes an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_activity(image_path, model=DEFAULT_MODEL):
    """
    Sends the screenshot to the AI for analysis and returns the structured response.
    """
    system_prompt = """
    You are a strict but caring Asian mother. You are looking over your child's shoulder at their computer screen.
    Based on the image, you will provide a short, nagging comment in an Asian accent and a productivity score.

    Productivity Score Scale:
    -1.0: Very unproductive (games, social media, distractions).
     0.0: Neutral (idle, desktop, file explorer).
     1.0: Very productive (coding, studying, research, work).

    Output strictly valid JSON:
    {
        "reply": "<short_nagging_comment_in_accent>",
        "score": <float_between_-1_and_1>
    }
    Do not output anything else. Be concise.
    """
    base64_image = encode_image(image_path)
    if not base64_image:
        return None

    try:
        print("WYD: Analyzing screenshot...")
        response = completion(
            model=model,
            messages=[
                {
                    "role": "system", "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is my child doing? Are they being productive?"},
                        {
                            "type": "image_url",
                            "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
        )
        print("WYD: Received analysis:")
        data = json.loads(response.choices[0].message.content)
        print(data)
        return data

    except Exception as e:
        print(f"WYD Error calling AI: {e}")
        return None
    finally:
        # Clean up the temporary screenshot file
        if os.path.exists(image_path):
            os.remove(image_path)

def main(mom_queue=None):
    _load_env()
    if not os.environ.get("GROQ_API_KEY"):
        print("⚠️ WYD: GROQ_API_KEY not found in environment. This feature will be disabled.")
        return
        
    print("👀 WYD Manager started. Checking screen every 5 minutes.")
    
    while True:
        screenshot_path = take_screenshot()
        if not screenshot_path:
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        analysis = analyze_activity(screenshot_path)
        
        if analysis and mom_queue:
            reply = analysis.get("reply")
            score = analysis.get("score")
            
            if reply is not None and score is not None:
                mom_queue.put({
                    "type": "show_bubble_message",
                    "text": reply,
                    "score": score
                })

        time.sleep(CHECK_INTERVAL_SECONDS)