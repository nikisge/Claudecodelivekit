import { NextResponse } from 'next/server';
import { AGENT_CONTAINER, assertValidAgent, docker } from '@/lib/agent-control';

export const revalidate = 0;

const SETUP_TARGET = {
  'simple-latency': '1',
  'appointment-booking': '2',
  'outbound-telephony': '3',
} as const;

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function POST(req: Request) {
  let setupCommand = './start.sh setup <1|2|3>';
  try {
    const { name } = (await req.json()) as { name?: string };
    if (!name) {
      return NextResponse.json({ error: 'name fehlt.' }, { status: 400 });
    }
    assertValidAgent(name);
    setupCommand = `./start.sh setup ${SETUP_TARGET[name]}`;

    const container = docker.getContainer(AGENT_CONTAINER[name]);
    const before = await container.inspect();
    if (before.State.Restarting || (before.State.ExitCode && before.State.ExitCode !== 0)) {
      return NextResponse.json(
        {
          error:
            'Agent-Container ist im Fehlerzustand. Logs prüfen und Image neu bauen/starten, z. B. ./start.sh vps ' +
            SETUP_TARGET[name],
        },
        { status: 409 }
      );
    }

    await container.start();
    await sleep(1200);
    const after = await container.inspect();
    if (after.State.Restarting || (!after.State.Running && after.State.ExitCode !== 0)) {
      return NextResponse.json(
        {
          error:
            'Agent ist direkt nach dem Start abgestürzt. Logs prüfen: ./start.sh agent-logs ' +
            SETUP_TARGET[name],
        },
        { status: 500 }
      );
    }
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
            setupCommand,
        },
        { status: 409 }
      );
    }
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
