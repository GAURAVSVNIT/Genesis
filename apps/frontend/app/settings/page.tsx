'use client';

import { useEffect, useState } from 'react';
import { LinkedInConnection } from '@/components/settings/LinkedInConnection';
import { TwitterConnection } from '@/components/settings/TwitterConnection';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
    // We get userId from the state param if it exists in URL, otherwise we might be just visiting settings
    // But since this page is primarily for the callback now, let's derive it or hold it.
    // Actually, LinkedInConnection handles the callback using 'state' from URL param itself.
    // But it requires a 'userId' prop to list connections. 

    // For the callback scenario, the 'state' param IS the userId.
    const [userId, setUserId] = useState<string>('');

    useEffect(() => {
        // Try to get userId from URL state (callback scenario)
        const params = new URLSearchParams(window.location.search);
        const state = params.get('state');
        if (state) {
            setTimeout(() => setUserId(state), 0);
        } else {
            // Fallback: try to grab from local storage or guest session if available
            const storedParams = localStorage.getItem('genesis-guest-params');
            if (storedParams) {
                try {
                    const parsed = JSON.parse(storedParams);
                    if (parsed.userId) {
                        const uid = parsed.userId;
                        setTimeout(() => setUserId(uid), 0);
                    }
                } catch (e) { }
            }
        }
    }, []);

    if (!userId) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                <Card className="w-full max-w-md bg-slate-900 border-slate-800 text-slate-200">
                    <CardHeader>
                        <CardTitle>Settings</CardTitle>
                        <CardDescription>Loading user context...</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Link href="/" className="text-blue-400 hover:underline flex items-center gap-2">
                            <ArrowLeft className="w-4 h-4" /> Return to Home
                        </Link>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col p-4 md:p-8">
            <div className="max-w-4xl mx-auto w-full space-y-6">
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/">
                        <Button variant="ghost" className="text-slate-400 hover:text-white pl-0 gap-2">
                            <ArrowLeft className="w-4 h-4" /> Back to Chat
                        </Button>
                    </Link>
                    <h1 className="text-2xl font-bold text-white">Settings</h1>
                </div>

                <div className="grid gap-6">
                    <section>
                        <h2 className="text-xl font-semibold text-slate-200 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-400">
                            Integrations
                        </h2>
                        <div className="grid gap-6 md:grid-cols-2">
                            <LinkedInConnection userId={userId} />
                            <TwitterConnection userId={userId} />
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
