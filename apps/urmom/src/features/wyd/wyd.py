import os
import sys
import time
import base64
import json
from groq import Groq
from PIL import ImageGrab
from utils.env import load_env
from utils import log

# --- Constants ---
DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
CHECK_INTERVAL_SECONDS = 5 * 60  # 5 minutes
ANIMATION_DELAY_SECONDS = 2


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
        log(f"WYD Error taking screenshot: {e}")
        return None


def encode_image(image_path):
    """Encodes an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_activity(image_path, model=DEFAULT_MODEL):
    """
    Sends the screenshot to the AI for analysis and returns the structured response.
    """
    system_prompt = """
    You are a strict but caring Asian mother. You are looking over your child's shoulder at their computer screen.
    Based on the image, you will provide a short, nagging comment in an Asian accent and a productivity score.
    If the activity is productive, be more encouraging in your comment, otherwise be stricter.

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
        log("WYD: Analyzing screenshot...")
        client = Groq()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What is my child doing? Are they being productive?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )
        log("WYD: Received analysis:")
        data = json.loads(response.choices[0].message.content)
        log(str(data))
        return data

    except Exception as e:
        log(f"WYD Error calling AI: {e}")
        return None
    finally:
        # Clean up the temporary screenshot file
        if os.path.exists(image_path):
            os.remove(image_path)

def main(mom_queue=None, check_interval_minutes=10):
    load_env()
    if not os.environ.get("GROQ_API_KEY"):
        log(
            "⚠️ WYD: GROQ_API_KEY not found in environment. This feature will be disabled."
        )
        return
        
    print("👀 WYD Manager started. Checking screen every {check_interval_minutes:.1f} minutes.")
    
    while True:
        # 1. Tell Mom to get ready for the picture
        if mom_queue:
            log("WYD: Telling Mom to take a picture.")
            mom_queue.put({"type": "prepare_for_screenshot"})
            time.sleep(ANIMATION_DELAY_SECONDS)  # Give animation time to play

        # 2. Take the screenshot and analyze it
        screenshot_path = take_screenshot()
        analysis = None
        if screenshot_path:
            analysis = analyze_activity(screenshot_path)

        # 3. Send the analysis results back to Mom
        if analysis and mom_queue:
            reply = analysis.get("reply")
            score = analysis.get("score")

            if reply is not None and score is not None:
                mom_queue.put(
                    {"type": "show_bubble_message", "text": reply, "score": score}
                )
                if score < -0.3:
                    mom_queue.put({"type": "change_anger", "delta": 1})
                elif score > 0.3:
                    mom_queue.put({"type": "change_anger", "delta": -1})

        # 4. Wait for the next cycle
        time.sleep(check_interval_minutes * 60 - ANIMATION_DELAY_SECONDS)
