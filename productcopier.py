import os
from google.genai import Client, types
from google.adk.agents import LlmAgent

def analyze_product_image(image_path: str) -> str:
    """
    Analyzes a raw product image using Gemini Vision to determine
    structural details and a masking/background removal strategy.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = Client(api_key=api_key)

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        prompt = (
            "Analyze this product image for a marketing campaign. "
            "1. Identify the product and its key structural features. "
            "2. Suggest the best technical background removal strategy (e.g., alpha matting for hair/fur, "
            "sharp vector paths for hard surfaces, or depth-based masking) to create a high-quality mask."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ]
        )
        return response.text
    except Exception as e:
        return f"Error analyzing product image: {str(e)}"

def get_product_copier():
    return LlmAgent(
        name="ProductCopier",
        model="gemini-2.5-flash",
        instruction="You are a Product Copier (Agent B). Analyze product images and create structural masks.",
        tools=[analyze_product_image]
    )
