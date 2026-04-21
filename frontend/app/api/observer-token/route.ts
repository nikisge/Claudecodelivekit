import { NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';

// Stellt einen Read-Only-Token aus, mit dem das Frontend einem laufenden
// Outbound-Call-Room als passiver Zuhörer beitreten kann, um Transkripte +
// Lead-Daten (via Data-Channel) live anzuzeigen.
export const revalidate = 0;

export async function POST(req: Request) {
  try {
    const { roomName } = (await req.json()) as { roomName?: string };
    if (!roomName) {
      return NextResponse.json({ error: 'roomName erforderlich.' }, { status: 400 });
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const publicUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;

    if (!apiKey || !apiSecret || !publicUrl) {
      return NextResponse.json(
        { error: 'Server-Konfiguration unvollständig.' },
        { status: 500 }
      );
    }

    const at = new AccessToken(apiKey, apiSecret, {
      identity: `observer-${crypto.randomUUID().slice(0, 8)}`,
      ttl: '10m',
    });
    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: false,
      canSubscribe: true,
    });

    const token = await at.toJwt();
    return NextResponse.json({ token, url: publicUrl });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unbekannter Fehler';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
