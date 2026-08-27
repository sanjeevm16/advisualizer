import asyncio
import os
from memory import create_runner
from google.genai._transformers import t_content

async def test():
    runner = create_runner()
    events = runner.run(
        user_id="test_user",
        session_id="test_jewelry_session",
        new_message=t_content("You are a photography critic. Generate an ad campaign for Indian jewelry.A close-up shot of jewelry on a hi-tech gloss white background. Godlen hour lighting, dramatic lighting, and a clear view is preffered .")
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
