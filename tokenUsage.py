import sys

# 1. OpenAI / Custom Model Estimation (Using Tiktoken)
def count_openai_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        # Fallback heuristic: ~4 characters or ~0.75 words per token
        return round((len(text) / 4 + len(text.split()) / 0.75) / 2)

# 2. Google Gemini Estimation
def count_gemini_tokens(text: str, model: str = "gemini-2.5-flash") -> int:
    try:
        from google import genai
        # Automatically pulls GEMINI_API_KEY from your environment variables
        client = genai.Client()
        response = client.models.count_tokens(model=model, contents=text)
        return response.total_tokens
    except Exception as e:
        return f"Error (Ensure GEMINI_API_KEY is set): {e}"

# 3. Anthropic Claude Estimation
def count_anthropic_tokens(text: str, model: str = "claude-3-7-sonnet-latest") -> int:
    try:
        from anthropic import Anthropic
        # Automatically pulls ANTHROPIC_API_KEY from environment variables
        client = Anthropic()
        response = client.beta.messages.count_tokens(model=model, system="You are a helpful assistant.", messages=[{"role": "user", "content": text}])
        return response.input_tokens
    except Exception as e:
        return f"Error (Ensure ANTHROPIC_API_KEY is set): {e}"

# --- Test Execution ---
if __name__ == "__main__":
    sample_prompt = "Write a test script to calculate token usage."
    
    print("--- LLM Token Metrics Test ---")
    print(f"Sample Payload: \"{sample_prompt}\"\n")
    
    # Run OpenAI local tokenizer (or fallback heuristic)
    print(f"OpenAI (Tiktoken/Heuristic): {count_openai_tokens(sample_prompt)} tokens")
    
    # Run API-based token counters (Uncomment if you have SDKs and keys configured)
    print(f"Google Gemini API: {count_gemini_tokens(sample_prompt)} tokens")
    print(f"Anthropic Claude API: {count_anthropic_tokens(sample_prompt)} tokens")
