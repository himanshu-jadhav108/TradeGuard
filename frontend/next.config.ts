import type { NextConfig } from "next";

const backendTarget = (
  process.env.BACKEND_URL ||
  process.env.INTERNAL_API_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendTarget}/api/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      {
        source: "/app/trade",
        destination: "/app",
        permanent: false,
      },
      {
        source: "/trade",
        destination: "/app",
        permanent: false,
      },
      {
        source: "/reset",
        destination: "/app",
        permanent: false,
      },
      {
        source: "/restart",
        destination: "/app",
        permanent: false,
      },
      {
        source: "/restart-demo",
        destination: "/app",
        permanent: false,
      },
      {
        source: "/reset-demo",
        destination: "/app",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
