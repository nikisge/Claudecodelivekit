import { NextResponse } from 'next/server';
import { AGENT_CONTAINER, assertValidAgent, docker } from '@/lib/agent-control';

export const revalidate = 0;

export async function POST(req: Request) {
  try {
    const { name } = (await req.json()) as { name?: string };
    if (!name) {
      return NextResponse.json({ error: 'name fehlt.' }, { status: 400 });
    }
    assertValidAgent(name);

    const container = docker.getContainer(AGENT_CONTAINER[name]);
    await container.stop({ t: 5 });
    return NextResponse.json({ status: 'stopped' });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unbekannter Fehler';
    if (message.includes('not running') || message.includes('304')) {
      return NextResponse.json({ status: 'already-stopped' });
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
