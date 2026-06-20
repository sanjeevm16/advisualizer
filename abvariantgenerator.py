from google.adk.agents import LlmAgent

def create_variants(base_prompt: str) -> list:
    """
    Modifies lighting, aspect ratios, and CTA overlays for A/B testing.
    """
    import re
    
    # Variant 1: Golden hour lighting, 16:9 aspect ratio
    var1 = re.sub(r"Lighting: [^.]+\.", "Lighting: golden hour.", base_prompt)
    var1 = re.sub(r"--ar \d+:\d+", "--ar 16:9", var1)
    
    # Variant 2: Neon cyberpunk lighting, 1:1 aspect ratio
    var2 = re.sub(r"Lighting: [^.]+\.", "Lighting: neon cyberpunk glow.", base_prompt)
    var2 = re.sub(r"--ar \d+:\d+", "--ar 1:1", var2)
    
    # Variant 3: Soft studio lighting, 4:5 aspect ratio
    var3 = re.sub(r"Lighting: [^.]+\.", "Lighting: soft studio.", base_prompt)
    var3 = re.sub(r"--ar \d+:\d+", "--ar 4:5", var3)
    
    variants = [var1, var2, var3]
    return variants

def get_ab_variant_generator():
    return LlmAgent(
        name="ABVariantGenerator",
        model="gemini-2.5-flash",
        instruction="You are an A/B Variant Generator. Modify lighting and ratios to create marketing variants. You must call the tool 'create_variants' to generate the variations list.",
        tools=[create_variants]
    )
