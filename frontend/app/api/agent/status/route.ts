import { NextResponse } from 'next/server';
import { AGENT_CONTAINER, AgentName, AgentState, getAgentState } from '@/lib/agent-control';

export const revalidate = 0;

export async function GET() {
  const names = Object.keys(AGENT_CONTAINER) as AgentName[];
  const entries = await Promise.all(
    names.map(async (n) => [n, await getAgentState(n)] as [AgentName, AgentState])
  );
  return NextResponse.json({
    agents: Object.fromEntries(entries) as Record<AgentName, AgentState>,
  });
}
