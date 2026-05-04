"""
Einmaliges Setup: legt einen LiveKit Outbound SIP Trunk an, der auf den
Twilio Elastic SIP Trunk zeigt. Der zurückgegebene TRUNK_ID wird als
LIVEKIT_OUTBOUND_TRUNK_ID in .env eingetragen und von der Dispatch-Route
genutzt, um ausgehende Anrufe zu starten.

Nutzung:
    python scripts/setup-sip.py

Voraussetzungen in .env:
    LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
    TWILIO_SIP_TRUNK_URI (z.B. sip:abc123.pstn.twilio.com)
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
    TWILIO_PHONE_NUMBER (z.B. +4912345678)
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit import api


def _http_url_from_ws(ws_url: str) -> str:
    return ws_url.replace("wss://", "https://").replace("ws://", "http://")


def _write_env_value(key: str, value: str) -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return

    lines = env_path.read_text().splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n")


async def main() -> None:
    load_dotenv()

    required = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "TWILIO_SIP_TRUNK_URI",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"Fehlende ENV-Variablen: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    trunk_address = os.environ["TWILIO_SIP_TRUNK_URI"].removeprefix("sip:")

    lkapi = api.LiveKitAPI(
        url=_http_url_from_ws(os.environ["LIVEKIT_URL"]),
        api_key=os.environ["LIVEKIT_API_KEY"],
        api_secret=os.environ["LIVEKIT_API_SECRET"],
    )

    try:
        trunk = api.SIPOutboundTrunkInfo(
            name="Twilio Outbound (Tutorial)",
            address=trunk_address,
            numbers=[os.environ["TWILIO_PHONE_NUMBER"]],
            auth_username=os.environ["TWILIO_ACCOUNT_SID"],
            auth_password=os.environ["TWILIO_AUTH_TOKEN"],
        )
        response = await lkapi.sip.create_sip_outbound_trunk(
            api.CreateSIPOutboundTrunkRequest(trunk=trunk)
        )

        print("✓ Outbound SIP Trunk erstellt.")
        print()
        _write_env_value("LIVEKIT_OUTBOUND_TRUNK_ID", response.sip_trunk_id)
        print("In .env eingetragen:")
        print(f"LIVEKIT_OUTBOUND_TRUNK_ID={response.sip_trunk_id}")
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    asyncio.run(main())
