'use client';

import { useState, useEffect, useRef } from 'react';
import { socialApi, Connection } from '@/lib/api/social';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { toast } from 'sonner'; // Using sonner for consistent toasts
import { Loader2, Linkedin, CheckCircle } from 'lucide-react';

interface LinkedInConnectionProps {
    userId: string;
}

export function LinkedInConnection({ userId }: LinkedInConnectionProps) {
    const [isConnecting, setIsConnecting] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [connection, setConnection] = useState<Connection | null>(null);

    useEffect(() => {
        loadConnections();
    }, [userId]);

    const loadConnections = async () => {
        try {
            const connections = await socialApi.listConnections(userId);
            const linkedIn = connections.find(c => c.platform === 'linkedin');
            setConnection(linkedIn || null);
        } catch (error) {
            console.error(error);
        }
    };

    // Handle initial Connect Click
    const handleConnect = async () => {
        setIsConnecting(true);
        try {
            // Get Auth URL from backend
            // Use configured Redirect URI or fallback to current page
            const redirectUri = process.env.NEXT_PUBLIC_LINKEDIN_REDIRECT_URI || (window.location.origin + '/settings');

            const response = await socialApi.getLinkedInAuthUrl(
                userId,
                redirectUri
            );

            // Redirect to LinkedIn
            window.location.href = response.url;
        } catch (error) {
            console.error(error);
            toast.error("Failed to initiate connection");
            setIsConnecting(false);
        }
    };

    const processedCode = useRef<string | null>(null);

    // Handle OAuth Callback (Runs on mount if code is present)
    useEffect(() => {
        const query = new URLSearchParams(window.location.search);
        const code = query.get('code');
        const state = query.get('state');

        // Only process if we have code/state AND we haven't already processed THIS code
        if (code && state && processedCode.current !== code) {
            processedCode.current = code; // Mark as processed immediately

            const handleCallback = async () => {
                setIsConnecting(true);
                // toast.loading("Finalizing connection..."); 
                try {
                    await socialApi.exchangeLinkedInCode(
                        code,
                        state,
                        process.env.NEXT_PUBLIC_LINKEDIN_REDIRECT_URI || (window.location.origin + '/settings')
                    );
                    toast.success("LinkedIn Connected!");
                    await loadConnections();
                    // Clean URL
                    window.history.replaceState({}, '', '/settings');
                } catch (error) {
                    console.error(error);
                    toast.error("Failed to complete connection");
                    // If failed, allow retrying (optional, but code handles one-time use)
                } finally {
                    setIsConnecting(false);
                }
            };
            handleCallback();
        }
    }, [userId]); // Add userId to dependency to ensure context is ready

    const handleDisconnect = async () => {
        setIsLoading(true);
        try {
            await socialApi.disconnect(userId, 'linkedin');
            await loadConnections();
            setConnection(null);
            toast.success("Disconnected from LinkedIn");
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

    const redirectUri = process.env.NEXT_PUBLIC_LINKEDIN_REDIRECT_URI || (typeof window !== 'undefined' ? `${window.location.origin}/settings` : '');

    return (
        <Card className="w-full max-w-md bg-slate-900 border-slate-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-slate-100">
                    <Linkedin className="h-6 w-6 text-[#0077b5]" />
                    LinkedIn Integration
                </CardTitle>
                <CardDescription className="text-slate-400">
                    Connect your LinkedIn account to share generated blogs directly.
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
                                        {connection?.profile_name ? `as ${connection.profile_name}` : 'Active'}
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
                            className="w-full bg-[#0077b5] hover:bg-[#0077b5]/90 text-white font-medium"
                        >
                            {isConnecting ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Connecting...
                                </>
                            ) : (
                                "Connect with LinkedIn"
                            )}
                        </Button>
                        <div className="text-center space-y-2">
                            <p className="text-xs text-slate-500">
                                You will be redirected to LinkedIn to approve access.
                            </p>
                            {redirectUri && (
                                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-[10px] text-slate-400 break-all">
                                    <p className="font-medium mb-1 text-slate-300">Requires Redirect URI in LinkedIn Portal:</p>
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
