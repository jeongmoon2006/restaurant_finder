import os

from google import genai


# Learn more about calling the LLM: https://the-pocket.github.io/PocketFlow/utility_function/llm.html
def call_llm(prompt: str) -> str:
    """Call Gemini via google-genai and return the response text.

    Uses environment variables:
      - GEMINI_API_KEY (required)
      - GEMINI_MODEL (optional, default: "gemini-2.5-flash")
    """

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(model=model_name, contents=prompt)
    # google-genai returns `response.text` for convenience
    return response.text


if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
