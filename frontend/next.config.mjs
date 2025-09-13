/** @type {import('next').NextConfig} */
const nextConfig = {
    webpack: (config) => {
        // Handle PDF.js worker
        config.resolve.alias = {
            ...config.resolve.alias,
            canvas: false,
        };

        // Disable webpack cache for PDF.js
        config.externals = config.externals || [];
        config.externals.push({
            canvas: 'canvas',
        });

        return config;
    },
    async rewrites() {
        // Proxy API calls to backend during development
        if (process.env.NODE_ENV === 'development') {
            return [
                {
                    source: '/api/:path*',
                    destination: 'http://127.0.0.1:8000/api/v1/:path*',
                },
            ];
        }
        // In production, API routes are handled by Vercel routing
        return [];
    },
    async headers() {
        return [
            {
                source: '/(.*)',
                headers: [
                    {
                        key: 'X-Frame-Options',
                        value: 'DENY',
                    },
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff',
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'strict-origin-when-cross-origin',
                    },
                ],
            },
        ];
    },
};

export default nextConfig;
