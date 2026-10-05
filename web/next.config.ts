import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Dev-only. Production on Vercel does not use this gate.
  allowedDevOrigins: ["127.0.0.1"],
  agentRules: false,
};

export default nextConfig;
