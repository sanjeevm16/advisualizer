import asyncio
import os
from memory import create_runner

async def test():
    runner = create_runner()
    from google.genai._transformers import t_content
    events = runner.run(
        user_id="test_user",
        session_id="test_session",
        new_message=t_content("Generate an ad for an electronic gadget")
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
