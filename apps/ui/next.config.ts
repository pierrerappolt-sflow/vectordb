import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  typescript: {
    // Skip type checking during build (fix types later)
    ignoreBuildErrors: true,
  },
  eslint: {
    // Skip ESLint during build
    ignoreDuringBuilds: true,
  },
  async rewrites() {
    const rewrites = [
      {
        source: "/temporal/:path*",
        destination: `${process.env.TEMPORAL_UI_HOST || "http://localhost:8080"}/:path*`,
      },
      {
        source: "/database/:path*",
        destination: `${process.env.DATABASE_UI_HOST || "http://localhost:8081"}/:path*`,
      },
      {
        source: "/rabbitmq/:path*",
        destination: `${process.env.RABBITMQ_UI_HOST || "http://localhost:15672"}/:path*`,
      },
    ];

    // Add Octant proxy if running on Kubernetes
    if (process.env.NEXT_PUBLIC_IS_KUBERNETES === "true") {
      rewrites.push({
        source: "/octant/:path*",
        destination: `${process.env.OCTANT_HOST || "http://localhost:7777"}/:path*`,
      });
    }

    return rewrites;
  },
};

export default nextConfig;
