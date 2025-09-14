import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const viewport = {
    width: 'device-width',
    initialScale: 1
}

export const metadata: Metadata = {
    title: 'ATS Résumé Analyzer',
    description: 'Analyze your résumé for ATS compatibility and job matching',
    keywords: 'ATS, resume, analyzer, job matching, applicant tracking system',
    authors: [{ name: 'ATS Analyzer Team' }],
    robots: 'index, follow',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <div className="min-h-screen bg-background">
                    <header className="border-b border-border bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/50">
                        <div className="container mx-auto px-4 py-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                    <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                                        <span className="text-primary-foreground font-bold text-sm">ATS</span>
                                    </div>
                                    <h1 className="text-xl font-semibold text-foreground">
                                        Résumé Analyzer
                                    </h1>
                                </div>
                                <nav className="hidden md:flex items-center space-x-6">
                                    <a
                                        href="#analyzer"
                                        className="text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        Analyzer
                                    </a>
                                    <a
                                        href="#about"
                                        className="text-muted-foreground hover:text-foreground transition-colors"
                                    >
                                        About
                                    </a>
                                </nav>
                            </div>
                        </div>
                    </header>

                    <main className="container mx-auto px-4 py-8">
                        {children}
                    </main>

                    <footer className="border-t border-border bg-card/50 mt-16">
                        <div className="container mx-auto px-4 py-8">
                            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                                <div className="text-sm text-muted-foreground">
                                    © 2024 ATS Analyzer. Built with Next.js and FastAPI.
                                </div>
                                <div className="text-sm text-muted-foreground">
                                    Privacy-focused • No data stored • Open source
                                </div>
                            </div>
                        </div>
                    </footer>
                </div>
            </body>
        </html>
    )
}
