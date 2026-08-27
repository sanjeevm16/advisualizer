import os
import json
from google.genai import Client
from scenecompositer import generate_backdrop_prompt
from abvariantgenerator import create_variants
from global_wrapper import audited_generate_content
from google import genai
from google.genai import types
import time

safety_settings = [
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_NONE", # Prevent empty None returns
    ),
]
def evaluate_prompt(prompt: str, context: str, client: Client) -> dict:
    """Uses Gemini to evaluate a text-to-image prompt."""
    evaluator_prompt = f"""
    You are an expert prompt engineer and photography critic. Evaluate the following text-to-image prompt.
    Context of the prompt: {context}
    
    Prompt to evaluate:
    "{prompt}"
    
    Evaluate the prompt based on:
    1. Clarity: Is the subject and style clear?
    2. Detail: Are lighting, composition, and technical specs well-defined?
    3. Effectiveness: How likely is this prompt to generate a high-quality, professional image?
    
    Provide your evaluation in JSON format with the following keys:
    - "score": A score from 1 to 10 (integer).
    - "clarity_feedback": Brief feedback on clarity.
    - "detail_feedback": Brief feedback on detail.
    - "overall_critique": A short summary of strengths and weaknesses.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=evaluator_prompt,
            config={'response_mime_type': 'application/json'}
        )
       # response = audited_generate_content(client, model="gemini-2.5-flash", contents=evaluator_prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

def run_evaluations():
    #client = Client()
    client = genai.Client(
        vertexai=True,
        project="ai-studio-applet-webapp-19ab7",
        location="us-central1",
        http_options=types.HttpOptions(
        headers={
            "X-Vertex-AI-LLM-Shared-Request-Type": "shared"
        }
        )
)
    
    print("--- Evaluating Scene Compositor Prompts ---")
    
    test_cases = [
        {"style": "minimalist pastel", "product_desc": "a sleek white smartwatch", "lighting": "soft studio", "composition": "centered on a marble pedestal", "aspect_ratio": "1:1"},
        {"style": "cyberpunk neon", "product_desc": "a mechanical keyboard", "lighting": "neon glow", "composition": "angled perspective", "aspect_ratio": "16:9"}
    ]
    
    for i, case in enumerate(test_cases):
        prompt = generate_backdrop_prompt(**case)
        print(f"\nTest Case {i+1}:")
        print(f"Generated Prompt: {prompt}")
        evaluation = evaluate_prompt(prompt, "Scene Compositor Backdrop Prompt", client)
        print(json.dumps(evaluation, indent=2,skipkeys='True'))
        #time.sleep(2)
        print(f"\n--- Evaluating A/B Variants for Test Case {i+1} ---")
        variants = create_variants(prompt)
        for j, variant in enumerate(variants):
            print(f"  Variant {j+1}: {variant}")
            var_eval = evaluate_prompt(variant, "A/B Marketing Variant", client)
            print("  Evaluation:" + json.dumps(var_eval))
            #print("  " + json.dumps(var_eval, indent=2,skipkeys='True').replace('\n', '\n  '))
            #time.sleep(2)

if __name__ == "__main__":
    run_evaluations()
