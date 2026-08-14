"""Dial an outbound number or SIP address using LiveKit SIP participant.

Usage:
  python src/dial_outbound.py --to <username_or_phone> --name "Rahul" --scenario vaccination_reminder --baby-age 2
"""

import argparse
import asyncio
import json
import os
import sys
import uuid

from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(".env.local")


def format_sip_recipient(raw: str) -> str:
    cleaned = raw.strip()

    # Check if it looks like a standard E.164 phone number
    if cleaned.startswith("+") or (cleaned.isdigit() and len(cleaned) >= 7):
        if cleaned.startswith("+"):
            return cleaned
        return f"+{cleaned}"

    # If it is a full SIP URI, extract the username part
    if cleaned.startswith("sip:"):
        cleaned = cleaned[len("sip:") :]
    if "@" in cleaned:
        cleaned = cleaned.split("@")[0]

    # Return only the SIP user/username as expected by LiveKit
    return cleaned


async def main():
    parser = argparse.ArgumentParser(description="Dial outbound voice AI helper call")
    parser.add_argument(
        "--to",
        required=True,
        help="Recipient phone number (e.g. +91XXXXXXXXXX) or SIP username/address (e.g. myuser)",
    )
    parser.add_argument(
        "--name", default="Rahul", help="Recipient name (default: Rahul)"
    )
    parser.add_argument(
        "--scenario",
        choices=["vaccination_reminder", "triage_followup"],
        default="vaccination_reminder",
        help="Outbound scenario",
    )
    parser.add_argument(
        "--baby-age",
        type=int,
        default=2,
        help="Baby's age in months (only for vaccination_reminder, default: 2)",
    )
    args = parser.parse_args()

    recipient = format_sip_recipient(args.to)
    print(f"Formatted SIP recipient: {recipient}")

    required = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "LIVEKIT_SIP_OUTBOUND_TRUNK_ID",
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(
            f"Error: Missing required environment variables in .env.local: {', '.join(missing)}"
        )
        print("Please check your .env.local file configuration.")
        sys.exit(1)

    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    sip_trunk_id = os.environ["LIVEKIT_SIP_OUTBOUND_TRUNK_ID"]

    # Generate a unique room name
    room_name = f"aarogya-outbound-{uuid.uuid4().hex[:8]}"

    # Structure metadata for the agent to read
    metadata = {
        "is_outbound": True,
        "caller_name": args.name,
        "phone": recipient,
        "scenario": args.scenario,
        "baby_age_months": args.baby_age,
    }
    metadata_str = json.dumps(metadata)

    print("Connecting to LiveKit server...")
    lkapi = api.LiveKitAPI(url=url, api_key=api_key, api_secret=api_secret)

    try:
        print(f"Creating LiveKit room: {room_name}")
        await lkapi.room.create_room(
            api.CreateRoomRequest(name=room_name, metadata=metadata_str)
        )

        print("Dispatching 'my-agent' to room...")
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="my-agent", room=room_name, metadata=metadata_str
            )
        )

        print(f"Dialing {recipient} (name={args.name}, scenario={args.scenario})...")
        await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=sip_trunk_id,
                sip_call_to=recipient,
                room_name=room_name,
                participant_identity=f"sip_{args.name.lower()}",
                participant_name=args.name,
            )
        )
        print("\n" + "=" * 60)
        print(f"SUCCESS! Outbound call successfully initiated to {recipient}.")
        print(f"LiveKit Room Name: {room_name}")
        print("=" * 60)

    except Exception as e:
        print(f"\nFailed to place outbound call: {e}")
        sys.exit(1)
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(main())
