import asyncio
import os
from memory import create_runner

async def test():
    runner = create_runner()
    from google.genai._transformers import t_content
    events = runner.run(
        user_id="test_user",
        session_id="test_session",
        new_message=t_content("You are a photography critic. Generate an ad for A sleek, silver LA 28 Olympics swim costume on a minimalist white background")
    )
    print("Runner started...")
    for event in events:
        print(f"Event: author={event.author}")
        if event.message and event.message.parts:
            for part in event.message.parts:
                if part.text:
                    print(f"Text: {part.text}")

if __name__ == "__main__":
    asyncio.run(test())
