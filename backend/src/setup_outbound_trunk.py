"""Create a LiveKit SIP outbound trunk pointing at Linphone or Twilio.

Run this ONCE after setting up your SIP provider.
It prints the trunk ID — copy it into .env.local as LIVEKIT_SIP_OUTBOUND_TRUNK_ID.
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(".env.local")


async def main():
    parser = argparse.ArgumentParser(description="Create LiveKit SIP outbound trunk")
    parser.add_argument(
        "--provider",
        choices=["linphone", "twilio"],
        default="linphone",
        help="Outbound SIP provider (default: linphone)",
    )
    args = parser.parse_args()

    # Check common required environment variables
    common_required = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    missing_common = [var for var in common_required if not os.getenv(var)]
    if missing_common:
        print(
            f"Error: Missing required LiveKit environment variables in .env.local: {', '.join(missing_common)}"
        )
        sys.exit(1)

    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]

    # Provider-specific setup
    if args.provider == "linphone":
        if not os.getenv("LINPHONE_USERNAME"):
            print("Error: Missing LINPHONE_USERNAME in .env.local")
            print(
                "Please add 'LINPHONE_USERNAME=your_username' to your .env.local file first."
            )
            sys.exit(1)

        username = os.environ["LINPHONE_USERNAME"]
        print(f"Configuring outbound trunk for Linphone (username: {username})...")

        trunk_info = api.SIPOutboundTrunkInfo(
            name="Linphone Outbound Trunk",
            address="sip.linphone.org",
            transport=api.SIPTransport.SIP_TRANSPORT_TLS,
            numbers=[username],
        )

    else:  # twilio
        twilio_required = [
            "TWILIO_SIP_TERM_URI",
            "TWILIO_SIP_USERNAME",
            "TWILIO_SIP_PASSWORD",
            "TWILIO_PHONE_NUMBER",
        ]
        missing_twilio = [var for var in twilio_required if not os.getenv(var)]
        if missing_twilio:
            print(
                f"Error: Missing required Twilio environment variables in .env.local: {', '.join(missing_twilio)}"
            )
            sys.exit(1)

        print("Configuring outbound trunk for Twilio Elastic SIP...")
        trunk_info = api.SIPOutboundTrunkInfo(
            name="Twilio Outbound Trunk",
            address=os.environ["TWILIO_SIP_TERM_URI"],
            auth_username=os.environ["TWILIO_SIP_USERNAME"],
            auth_password=os.environ["TWILIO_SIP_PASSWORD"],
            numbers=[os.environ["TWILIO_PHONE_NUMBER"]],
        )

    request = api.CreateSIPOutboundTrunkRequest(trunk=trunk_info)

    print(f"Connecting to LiveKit server at: {url}")
    lkapi = api.LiveKitAPI(url=url, api_key=api_key, api_secret=api_secret)

    try:
        print("Registering SIP outbound trunk in LiveKit...")
        trunk = await lkapi.sip.create_sip_outbound_trunk(request)
        print("\n" + "=" * 60)
        print(
            f"SUCCESS! {args.provider.capitalize()} SIP Outbound Trunk created successfully."
        )
        print(f"LIVEKIT_SIP_OUTBOUND_TRUNK_ID={trunk.sip_trunk_id}")
        print("=" * 60)
        print("\nPlease add the above line to your .env.local file.")
    except Exception as e:
        print(f"\nFailed to create trunk: {e}")
        sys.exit(1)
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(main())
