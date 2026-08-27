import asyncio
import os
from memory import create_runner
from google.genai._transformers import t_content

async def test():
    runner = create_runner()

    product_file = "products.txt"
    products = []
    
    # Load products from file if it exists
    if os.path.exists(product_file):
        with open(product_file, "r") as f:
            products = [line.strip() for line in f if line.strip()]
    
    # Fallback to a default if file is missing or empty
    if not products:
        products = ["Refreshing summer Coke drink"]

    for product in products:
        print(f"\n--- Starting campaign for: {product} ---")
        events = runner.run(
            user_id="test_user",
            session_id=f"test_session_{product.replace(' ', '_')}",
            new_message=t_content(f"You are a photography critic. Generate an ad campaign for {product}. A close-up shot of the {product} l .")
        )
        print("Runner started...")
        for event in events:
            print(f"\n--- Event from: {event.author} ---")
            if event.message and event.message.parts:
                for part in event.message.parts:
                    if part.text:
                        print(f"Text: {part.text}")
                    if part.function_call:
                        print(f"Function Call: {part.function_call.name}({part.function_call.args})")
                    if part.function_response:
                        print(f"Function Response: {part.function_response.name} -> {part.function_response.response}")

if __name__ == "__main__":
    asyncio.run(test())
