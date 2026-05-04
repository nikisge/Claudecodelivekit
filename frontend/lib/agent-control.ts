import Docker from 'dockerode';

// Socket-Mount aus docker-compose.local.yml:
//   volumes: - /var/run/docker.sock:/var/run/docker.sock
// Lokal (pnpm dev ohne Container) nutzt der Default die lokale Docker-Installation.
export const docker = new Docker();

export type AgentName = 'simple-latency' | 'appointment-booking' | 'outbound-telephony';

export const AGENT_CONTAINER: Record<AgentName, string> = {
  'simple-latency': 'voice-agent-1',
  'appointment-booking': 'voice-agent-2',
  'outbound-telephony': 'voice-agent-3',
};

export const AGENT_LABELS: Record<AgentName, string> = {
  'simple-latency': 'Simple Latency',
  'appointment-booking': 'Termin-Assistent',
  'outbound-telephony': 'Outbound-Anruf',
};

export type AgentState = 'running' | 'stopped' | 'starting' | 'missing' | 'failed';

export async function getAgentState(name: AgentName): Promise<AgentState> {
  const containerName = AGENT_CONTAINER[name];
  try {
    const container = docker.getContainer(containerName);
    const info = await container.inspect();
    if (info.State.Running) return 'running';
    if (info.State.Restarting) return 'failed';
    if (info.State.ExitCode && info.State.ExitCode !== 0) return 'failed';
    return 'stopped';
  } catch (err) {
    // Container existiert nicht → noch nicht gebaut
    return 'missing';
  }
}

export function assertValidAgent(name: string): asserts name is AgentName {
  if (!(name in AGENT_CONTAINER)) {
    throw new Error(`Unbekannter Agent: ${name}`);
  }
}
