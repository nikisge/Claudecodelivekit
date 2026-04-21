import { NextResponse } from 'next/server';
import { AgentDispatchClient, SipClient } from 'livekit-server-sdk';

// Hinweis: Für das Tutorial-Repo bewusst ohne Auth — in echter Produktion
// gehört hier Rate-Limiting + Session-Check davor.
export const revalidate = 0;

type DispatchRequest = {
  name: string;
  phone: string;
  context?: string;
};

function isValidE164(phone: string): boolean {
  return /^\+\d{8,15}$/.test(phone);
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as DispatchRequest;
    const name = body.name?.trim();
    const phone = body.phone?.trim();
    const context = body.context?.trim() ?? '';

    if (!name || !phone) {
      return NextResponse.json({ error: 'Name und Telefonnummer erforderlich.' }, { status: 400 });
    }
    if (!isValidE164(phone)) {
      return NextResponse.json(
        { error: 'Telefonnummer muss im Format +49... (E.164) sein.' },
        { status: 400 }
      );
    }

    const livekitUrl = process.env.LIVEKIT_URL;
    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const trunkId = process.env.LIVEKIT_OUTBOUND_TRUNK_ID;

    if (!livekitUrl || !apiKey || !apiSecret || !trunkId) {
      return NextResponse.json(
        {
          error:
            'Server nicht konfiguriert: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET und LIVEKIT_OUTBOUND_TRUNK_ID müssen gesetzt sein.',
        },
        { status: 500 }
      );
    }

    const roomName = `outbound-${crypto.randomUUID()}`;
    const metadata = JSON.stringify({ name, phone, context });

    const dispatchClient = new AgentDispatchClient(livekitUrl, apiKey, apiSecret);
    const sipClient = new SipClient(livekitUrl, apiKey, apiSecret);

    // 1. Agent in den Room dispatchen (Metadata = Kontext fürs Gespräch)
    await dispatchClient.createDispatch(roomName, 'outbound-telephony', { metadata });

    // 2. SIP-Participant in den Room setzen → triggert den Outbound-Call über Twilio
    await sipClient.createSipParticipant(trunkId, phone, roomName, {
      participantIdentity: `caller-${phone}`,
      participantName: name,
      waitUntilAnswered: false,
    });

    return NextResponse.json({ roomName, status: 'dispatched' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unbekannter Fehler';
    console.error('[dispatch-call]', message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
