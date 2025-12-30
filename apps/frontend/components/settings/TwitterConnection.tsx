'use client';

import { useState, useEffect } from 'react';
import { socialApi, Connection } from '@/lib/api/social';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, Twitter, CheckCircle } from 'lucide-react';

interface TwitterConnectionProps {
    userId: string;
}

export function TwitterConnection({ userId }: TwitterConnectionProps) {
    const [isConnecting, setIsConnecting] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [connection, setConnection] = useState<Connection | null>(null);

    useEffect(() => {
        loadConnections();
    }, [userId]);

    const loadConnections = async () => {
        try {
            const connections = await socialApi.listConnections(userId);
            const twitter = connections.find(c => c.platform === 'twitter');
            setConnection(twitter || null);
        } catch (error) {
            console.error(error);
        }
    };

    const handleConnect = async () => {
        setIsConnecting(true);
        try {
            const redirectUri = window.location.origin + '/settings';
            // Get Auth URL + Verifier from backend
            const response = await socialApi.getTwitterAuthUrl(userId, redirectUri);

            // Store verifier for callback
            if (response.code_verifier) {
                localStorage.setItem('twitter_code_verifier', response.code_verifier);
            }

            // Redirect
            window.location.href = response.url;
        } catch (error) {
            console.error(error);
            toast.error("Failed to initiate connection");
            setIsConnecting(false);
        }
    };

    // Handle OAuth Callback
    useEffect(() => {
        const query = new URLSearchParams(window.location.search);
        const code = query.get('code');
        const state = query.get('state');
        // Twitter might return 'error' or 'denied'

        if (code && state) {
            const handleCallback = async () => {
                // Must be "twitter" related state or verify source? 
                // Twitter state usually matches what we sent. 
                // We check if we have a verifier pending.
                const verifier = localStorage.getItem('twitter_code_verifier');
                if (!verifier) return; // Not a twitter callback or lost state

                setIsConnecting(true);
                try {
                    await socialApi.exchangeTwitterCode(
                        code,
                        state,
                        window.location.origin + '/settings',
                        verifier
                    );
                    toast.success("Twitter/X Connected!");
                    await loadConnections();

                    // Cleanup
                    localStorage.removeItem('twitter_code_verifier');
                    window.history.replaceState({}, '', '/settings');
                } catch (error) {
                    console.error(error);
                    toast.error("Failed to complete connection");
                } finally {
                    setIsConnecting(false);
                }
            };
            handleCallback();
        }
    }, [userId]);

    const handleDisconnect = async () => {
        setIsLoading(true);
        try {
            await socialApi.disconnect(userId, 'twitter');
            await loadConnections();
            setConnection(null);
            toast.success("Disconnected from Twitter");
        } catch (error) {
            toast.error("Failed to disconnect");
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return <div className="animate-pulse h-32 bg-slate-800/50 rounded-lg"></div>;
    }

    const isConnected = !!connection;
    const redirectUri = typeof window !== 'undefined' ? `${window.location.origin}/settings` : '';

    return (
        <Card className="w-full max-w-md bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-100">
                    <Twitter className="h-6 w-6 text-sky-500" />
                    X (Twitter) Integration
                </CardTitle>
                <CardDescription className="text-slate-400">
                    Connect your X account to post updates.
                </CardDescription>
            </CardHeader>
            <CardContent>
                {isConnected ? (
                    <div className="flex flex-col gap-4">
                        <div className="flex items-center justify-between p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                            <div className="flex items-center gap-2">
                                <CheckCircle className="h-5 w-5 text-green-500" />
                                <div>
                                    <p className="font-medium text-green-400">Connected</p>
                                    <p className="text-sm text-green-500/80">
                                        {connection?.profile_name || 'Active'}
                                    </p>
                                </div>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleDisconnect}
                                disabled={isLoading}
                                className="border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300 bg-transparent"
                            >
                                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Disconnect'}
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col gap-4">
                        <Button
                            onClick={handleConnect}
                            disabled={isConnecting}
                            className="w-full bg-black hover:bg-black/80 text-white font-medium border border-slate-700"
                        >
                            {isConnecting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Connecting...
                                </>
                            ) : (
                                "Connect with X"
                            )}
                        </Button>
                        <div className="text-center space-y-2">
                            {redirectUri && (
                                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-[10px] text-slate-400 break-all">
                                    <p className="font-medium mb-1 text-slate-300">Requires Redirect URI in X Portal:</p>
                                    <code className="bg-black/50 px-1 py-0.5 rounded select-all">{redirectUri}</code>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
