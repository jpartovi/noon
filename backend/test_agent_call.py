#!/usr/bin/env python3
"""Script to test the agent endpoint with a real audio file."""

import asyncio
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_agent_endpoint():
    """Test the /agent/action endpoint."""

    # Step 1: Authenticate
    print("1. Authenticating...")
    phone = input("Enter phone number (with country code, e.g., +1234567890): ")

    async with httpx.AsyncClient() as client:
        # Request OTP
        response = await client.post(
            f"{BASE_URL}/auth/otp",
            json={"phone": phone}
        )
        print(f"   OTP request: {response.status_code}")

        # Verify OTP
        code = input("Enter OTP code: ")
        response = await client.post(
            f"{BASE_URL}/auth/verify",
            json={"phone": phone, "code": code}
        )

        if response.status_code != 200:
            print(f"   Auth failed: {response.text}")
            return

        auth_data = response.json()
        access_token = auth_data["session"]["access_token"]
        print("   ✓ Authenticated!")

        # Step 2: Check Google account
        print("\n2. Checking Google account...")
        response = await client.get(
            f"{BASE_URL}/google-accounts/",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code == 200 and response.json():
            print(f"   ✓ Found {len(response.json())} Google account(s)")
        else:
            print("   ⚠ No Google accounts linked!")
            print("   Link a Google account first: POST /google-accounts/oauth/start")
            return

        # Step 3: Call agent with audio file
        print("\n3. Calling agent endpoint...")

        # Option A: Use an existing audio file
        audio_path = input("Enter path to audio file (or press Enter to use test data): ").strip()

        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                files = {"file": (Path(audio_path).name, f, "audio/wav")}
                response = await client.post(
                    f"{BASE_URL}/agent/action",
                    files=files,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=30.0
                )
        else:
            # Option B: Use fake audio data (will fail transcription in real env)
            print("   Using test audio data (note: may fail transcription)")
            files = {"file": ("test.wav", b"fake audio data", "audio/wav")}
            response = await client.post(
                f"{BASE_URL}/agent/action",
                files=files,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0
            )

        # Step 4: Show results
        print(f"\n4. Results:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        if response.status_code == 200:
            print("\n   ✓ Success! Check LangSmith for traces:")
            print("   https://smith.langchain.com")

if __name__ == "__main__":
    asyncio.run(test_agent_endpoint())
