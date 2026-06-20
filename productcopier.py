from google.adk.agents import LlmAgent

def analyze_product_image(image_path: str) -> str:
    """
    Simulates analyzing a raw product image for masking.
    """
    # Placeholder for image analysis logic
    return "structural mask generated, background removal strategy: alpha matting"

def get_product_copier():
    return LlmAgent(
        name="ProductCopier",
        model="gemini-2.5-flash",
        instruction="You are a Product Copier (Agent B). Analyze product images and create structural masks.",
        tools=[analyze_product_image]
    )
