from google.adk.agents import LlmAgent

def generate_backdrop_prompt(style: str, product_desc: str) -> str:
    """
    Writes contextual backdrop prompts for Flux or Midjourney.
    """
    return f"A {style} backdrop for a {product_desc}, cinematic lighting, 8k resolution."

def get_scene_compositer():
    return LlmAgent(
        name="SceneCompositor",
        model="gemini-2.5-flash",
        instruction="You are a Scene Compositor (Agent C). Write backdrop prompts matching trend recommendations.",
        tools=[generate_backdrop_prompt]
    )
