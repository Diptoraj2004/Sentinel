import json
import re
from typing import Literal
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key="YOUR_API_KEY")

SYSTEM_PROMPT = """
You are a security classifier AI.
Your task is to classify user input into EXACTLY one of the following categories:
Safe, Jailbreak, Toxic, Malware_Generation

Return STRICT JSON ONLY:
{"label": "<one_of_the_four_labels>"}
"""

VALID_LABELS = {"Safe", "Jailbreak", "Toxic", "Malware_Generation"}

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
    safety_settings=safety_settings
)

def classify_prompt(user_text: str) -> Literal["Safe", "Jailbreak", "Toxic", "Malware_Generation"]:
    if not user_text.strip():
        return "Safe"

    try:
        response = model.generate_content(
            user_text,
            generation_config={
                "temperature": 0,
                "top_p": 0,
                "max_output_tokens": 50
            }
        )

        if not response.parts:
            return "Toxic"

        text = response.text.strip()
        text = re.sub(r"```json|```", "", text).strip()

        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            return "Safe"

        data = json.loads(match.group())
        label = data.get("label")

        if label not in VALID_LABELS:
            return "Safe"

        return label

    except Exception:
        return "Safe"

if __name__ == "__main__":
    print("--- Security Classifier Active (type 'exit' to quit) ---")
    while True:
        user_input = input("\nEnter prompt: ").strip()
        if user_input.lower() == "exit":
            break
        print("Classification:", classify_prompt(user_input))
