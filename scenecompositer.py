from google.adk.agents import LlmAgent

def generate_backdrop_prompt(
    style: str, 
    product_desc: str, 
    lighting: str = "soft studio", 
    composition: str = "minimalist",
    aspect_ratio: str = "1:1"
) -> str:
    """
    Constructs a highly detailed backdrop prompt for text-to-image models.
    
    Args:
        style: The visual style (e.g., 'minimalist pastel', 'high-tech gloss').
        product_desc: Description of the product to be integrated.
        lighting: Specific lighting instructions (e.g., 'golden hour', 'neon glow').
        composition: Scene layout instructions (e.g., 'centered on a marble pedestal').
        aspect_ratio: The target aspect ratio for the image generation.
        
    Returns:
        A descriptive prompt string optimized for high-end product photography.
    """
    prompt = (
        f"A professional product photography backdrop in a {style} style. "
        f"The scene features a {composition} layout specifically designed for {product_desc}. "
        f"Lighting: {lighting}. Atmosphere: clean, premium commercial aesthetic, photorealistic. "
        f"Technical specifications: 8k resolution, ultra-detailed textures, ray-traced reflections. --ar {aspect_ratio}"
    )
    return prompt

def get_scene_compositer():
    return LlmAgent(
        name="SceneCompositor",
        model="gemini-2.5-flash",
        instruction=(
            "You are a Scene Compositor (Agent C). Your role is to translate trend recommendations and "
            "product descriptions into highly descriptive image generation prompts. Focus on "
            "professional photography principles to ensure the backdrop highlights the product effectively."
        ),
        tools=[generate_backdrop_prompt]
    )
