import { notFound } from 'next/navigation';
import { headers } from 'next/headers';
import { App } from '@/components/app/app';
import { getAppConfig } from '@/lib/utils';

const VALID_AGENTS: Record<string, { title: string; description: string }> = {
  'simple-latency': {
    title: 'Simple Latency Demo',
    description: 'Schneller Voice-Bot — zeigt die Basis-Pipeline',
  },
  'appointment-booking': {
    title: 'Termin-Assistent',
    description: 'Sprachbuchung in Google Kalender',
  },
};

export default async function AgentPage({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  if (!(name in VALID_AGENTS)) {
    notFound();
  }

  const hdrs = await headers();
  const baseConfig = await getAppConfig(hdrs);

  const appConfig = {
    ...baseConfig,
    agentName: name,
    pageTitle: VALID_AGENTS[name].title,
    pageDescription: VALID_AGENTS[name].description,
  };

  return <App appConfig={appConfig} />;
}
