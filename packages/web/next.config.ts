import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com',
        pathname: '/drawing-practice-agent-images/**',
      },
    ],
  },
};

export default nextConfig;
