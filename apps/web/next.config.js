/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // `next build` runs ESLint by default; CI/Docker often fail on warnings. Run `npm run lint` locally.
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
