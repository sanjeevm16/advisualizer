from typing import Callable, Optional
from google import genai
from google.genai import types
from google.adk.models import LlmResponse
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

def track_token_usage(callback_context: CallbackContext, llm_response: LlmResponse) ->Optional[LlmResponse]:
    """
    Hook that fires automatically after every LLM call inside the agent loop.
    """
    agent_name = callback_context.agent_name
    print(f"[Callback] After model call for agent: {agent_name}")
    try:
        # 1. Primary: Check 'usage_metadata' attribute (Standard for Gemini ADK)
        usage = getattr(llm_response, 'usage_metadata', None)

        # 2. Secondary: Check 'usage' attribute (Common in LiteLLM backends)
        if not usage:
            usage = getattr(llm_response, 'usage', None)

        # 3. Fallback: Search inside metadata if it exists
        metadata = getattr(llm_response, 'metadata', {}) or {}
        model_response = metadata.get("model_response") if isinstance(metadata, dict) else None
        
        if not usage and model_response:
            if hasattr(model_response, 'usage_metadata'):
                usage = model_response.usage_metadata
            elif isinstance(model_response, dict):
                usage = model_response.get("usage_metadata") or model_response.get("usage")
        
        if not usage:
            usage = metadata.get("usage_metadata") or metadata.get("usage")

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if usage:
            if hasattr(usage, 'prompt_token_count'): # SDK Object style (Gemini)
                prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                completion_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', 0)
            elif isinstance(usage, dict): # Dictionary style fallback
                prompt_tokens = usage.get("prompt_token_count") or usage.get("prompt_tokens") or 0
                completion_tokens = usage.get("candidates_token_count") or usage.get("completion_tokens") or 0
                total_tokens = usage.get("total_token_count") or usage.get("total_tokens") or 0
        
        # Alternative Way: Manual Estimation if telemetry is missing
        if total_tokens == 0:
            # Count tokens in the generated response parts
            if llm_response.content and llm_response.content.parts:
                for part in llm_response.content.parts:
                    if part.text:
                        # Gemini heuristic: ~4 characters per token
                        completion_tokens += len(part.text) // 4
            
            # Note: Prompt tokens cannot be easily calculated here without the original prompt.
            # You can call client.models.count_tokens() if you have the prompt string.
            total_tokens = prompt_tokens + completion_tokens
            if total_tokens > 0:
                print(f"[Callback] Usage estimated via heuristic (Metadata was missing)")


        if total_tokens > 0:
            # Pricing for Gemini 2.5 Flash tier (Approximated)
            # Input: $0.075 per 1 million tokens | Output: $0.30 per 1 million tokens
            cost_input = (prompt_tokens / 1_000_000) * 0.075
            cost_output = (completion_tokens / 1_000_000) * 0.30
            total_cost = cost_input + cost_output

            print(f"\n--- [LlmAgent Token Hook] ---")
            print(f"Agent: {agent_name}")
            print(f"Prompt Input: {prompt_tokens} tokens (${cost_input:.6f})")
            print(f"Completion Output: {completion_tokens} tokens (${cost_output:.6f})")
            print(f"Total Call Tokens: {total_tokens} tokens")
            print(f"Estimated Cost: ${total_cost:.6f}")
            print(f"-----------------------------\n")
        else:
            print(f"[Callback] No usage telemetry found for agent: {agent_name}")

    except Exception as e:
        print(f"Error reading usage telemetry: {e}")
        
    return llm_response

# Define your generic after-model callback function
def global_after_model_callback(response: types.GenerateContentResponse) -> types.GenerateContentResponse:
    # Add your generic logic here (e.g., logging, auditing, telemetry, censoring)
    print(f"[Callback] Processed response, token count: {response.usage_metadata}")    # 1. Telemetry: Log detailed token usage and model latency
   
#if response.usage_metadata is not None:
    usage = response.usage_metadata
    if usage:
        print(f"[Telemetry] Prompt: {usage.prompt_token_count}, Candidates: {usage.candidates_token_count}, Total: {usage.total_token_count}")
    
    # 2. Censoring: Check for restricted keywords or safety filters
    censored_keywords = ["competitor_name_alpha", "internal_secret_project"]

    
#if response.text is not None:
    if response.usage_metadata is not None and response.text:
        for word in censored_keywords:
            if word.lower() in response.text.lower():
                print(f"[Censoring] Warning: Restricted content detected in response.")
                # Example of simple redaction logic
                # response.text = response.text.replace(word, "[REDACTED]")

    # 3. Auditing: Log the interaction for compliance/debugging
    audit_log = {
        "model": response.model_version,
        "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else "N/A",
        "safety_ratings": [str(rating.category) + ": " + str(rating.probability) for rating in response.candidates[0].safety_ratings] if response.candidates else []
    }
    print(f"[Audit] {audit_log}")

    return response

# Create a generic wrapper/injector for generate_content
def audited_generate_content(
    client: genai.Client,
    model: str,
    contents: any,
    config: Optional[types.GenerateContentConfig] = None,
    after_cb: Callable[[types.GenerateContentResponse], types.GenerateContentResponse] = global_after_model_callback
) -> types.GenerateContentResponse:
    
    # Execute standard Gemini model call
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    
    # Inject generic post-processing callback
    return after_cb(response)