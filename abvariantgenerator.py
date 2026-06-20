from google.adk.agents import LlmAgent

def create_variants(base_prompt: str) -> list:
    """
    Modifies lighting, aspect ratios, and CTA overlays for A/B testing.
    """
    variants = [
        f"{base_prompt}, golden hour lighting, 16:9",
        f"{base_prompt}, neon cyberpunk lighting, 1:1",
        f"{base_prompt}, soft studio lighting, 'Shop Now' overlay, 4:5"
    ]
    return variants

def get_ab_variant_generator():
    return LlmAgent(
        name="ABVariantGenerator",
        model="gemini-2.5-flash",
        instruction="You are an A/B Variant Generator. Modify lighting and ratios to create marketing variants.",
        tools=[create_variants]
    )
