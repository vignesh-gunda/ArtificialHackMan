import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("FRIENDLI_TOKEN")
    team_id = os.getenv("FRIENDLI_TEAM_ID")
    print(f"Token: {token[:5]}...")
    print(f"Team ID: {team_id}")

    base_url = "https://api.friendli.ai/serverless/v1"
    headers = {}
    if team_id:
        headers["X-Friendli-Team"] = team_id

    client = AsyncOpenAI(
        api_key=token,
        base_url=base_url,
        default_headers=headers
    )

    try:
        print("Listing models...")
        models = await client.models.list()
        print("Models available:")
        for m in models.data:
            print(f" - {m.id}")
    except Exception as e:
        print(f"Error listing models: {e}")

    try:
        print("\nTesting chat completion with meta-llama-3.1-8b-instruct...")
        response = await client.chat.completions.create(
            model="meta-llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10  
        )
        print("Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"Error chatting: {e}")

if __name__ == "__main__":
    asyncio.run(main())
