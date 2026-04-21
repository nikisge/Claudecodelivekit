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
    await container.start();
    return NextResponse.json({ status: 'started' });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unbekannter Fehler';
    // "already started" ist kein Fehler
    if (message.includes('already started') || message.includes('304')) {
      return NextResponse.json({ status: 'already-running' });
    }
    // Container existiert nicht → Image muss erst gebaut werden
    if (message.includes('No such container')) {
      return NextResponse.json(
        {
          error:
            'Agent-Container existiert noch nicht. Einmalig im Terminal ausführen: ' +
            'docker compose --profile all-agents build',
        },
        { status: 409 }
      );
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
