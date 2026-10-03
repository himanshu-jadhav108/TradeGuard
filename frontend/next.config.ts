import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
  async redirects() {
    return [
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
