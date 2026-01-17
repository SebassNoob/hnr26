import json
import os
from litellm import completion

DEFAULT_MODEL = "huggingface/together/meta-llama/Llama-3.2-3B-Instruct"


def _load_env():
    env_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    )
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env()


def negotiate_time(user_excuse: str, model=DEFAULT_MODEL):
    system_prompt = """
    You are a strict Asian mother. Your child wants more computer time.
    Reply with an Asian accent.

    Rules:
    1. Valid excuses (homework, studying) = 15-30 mins.
    2. Invalid excuses (games, generic begging) = 0-5 mins.
    3. If they are annoying or greedy, set "slipper": true.
    
    Output strictly valid JSON:
    {
        "minutes": <int>,
        "reply": "<short_nagging_response>",
        "slipper": <bool>
    }
    Do not output anything else.
    """

    try:
        print("submitting excuse: ", user_excuse)
        response = completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_excuse},
            ],
            temperature=0.7,
            response_format={ "type": "json_object" },
        )
        print("received response: ", response)

        # Parse JSON response
        data = json.loads(response.choices[0].message.content)
        return data

    except Exception as e:
        print(f"Error calling Mom: {e}")
        # Fail-safe response if API is down
        return {
            "minutes": 0,
            "reply": "I'm too tired to argue. Go sleep.",
            "slipper": False,
        }


# testing
def main():
    print("--- STARTING MOM TEST ---")

    # 1. Check for API Keys (Quick helper for testing)
    if "HUGGINGFACE_API_KEY" not in os.environ and "OPENAI_API_KEY" not in os.environ:
        print("⚠️  WARNING: No API Key found.")
        key = input("Enter HuggingFace API Key for this test: ")
        if key.strip():
            os.environ["HUGGINGFACE_API_KEY"] = key.strip()
        else:
            print("No key provided. This will likely fail.")

    # 2. Define Test Scenarios
    scenarios = [
        "I need to finish my math homework, it's due tomorrow!",
        "I just want to play Minecraft for 10 more minutes.",
        "Please mom! Everyone else is still online!",
    ]

    # 3. Run Tests
    for excuse in scenarios:
        print(f"\n[Child]: {excuse}")
        print("(Mom is thinking...)")

        result = negotiate_time(excuse)

        print(f"[Mom]:   {result.get('reply')}")
        print(f"       -> Added: {result.get('minutes')} mins")
        print(f"       -> Slipper: {'YES' if result.get('slipper') else 'No'}")

    print("\n--- TEST FINISHED ---")

if __name__ == "__main__":
    main()