import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Key, BookOpen, BarChart2, Home, Settings, Terminal } from "lucide-react";

export default function DeveloperLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex min-h-screen bg-background text-foreground">
            {/* Sidebar */}
            <aside className="hidden w-64 border-r border-border/50 bg-card/30 backdrop-blur-xl flex-col md:flex">
                <div className="p-6 border-b border-border/50">
                    <Link href="/home" className="flex items-center gap-2 font-bold text-xl">
                        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                            <Terminal className="w-5 h-5 text-primary" />
                        </div>
                        <span className="bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">Verbix AI API</span>
                    </Link>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <div className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Platform
                    </div>
                    <Link href="/developer/api-keys">
                        <Button variant="ghost" className="w-full justify-start gap-3 h-10">
                            <Key className="w-4 h-4" />
                            API Keys
                        </Button>
                    </Link>
                    <Link href="/developer/usage">
                        <Button variant="ghost" className="w-full justify-start gap-3 h-10">
                            <BarChart2 className="w-4 h-4" />
                            Usage
                        </Button>
                    </Link>
                    <div className="px-4 py-2 mt-6 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Resources
                    </div>
                    <Link href="/developer/docs">
                        <Button variant="ghost" className="w-full justify-start gap-3 h-10">
                            <BookOpen className="w-4 h-4" />
                            Documentation
                        </Button>
                    </Link>
                </nav>

                <div className="p-4 border-t border-border/50">
                    <Link href="/home">
                        <Button variant="outline" className="w-full justify-start gap-3">
                            <Home className="w-4 h-4" />
                            Back to App
                        </Button>
                    </Link>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="container max-w-5xl mx-auto p-6 md:p-10 space-y-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
