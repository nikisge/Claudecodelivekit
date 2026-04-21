import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // dockerode zieht ssh2/cpu-features mit nativen Binaries nach. Next.js soll die
  // nicht bundlen — nur auf dem Server zur Laufzeit aus node_modules laden.
  serverExternalPackages: ['dockerode', 'ssh2', 'cpu-features', 'docker-modem'],

  // Prettier-Formatting im CI/Docker-Build tolerant behandeln — für das Tutorial
  // ist Code-Formatting kein Blocker.
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
