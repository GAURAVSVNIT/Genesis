"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Copy, Plus, Trash2, ShieldCheck, RefreshCw } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

interface ApiKey {
    id: string;
    name: string;
    key: string;
    created: string;
    lastUsed: string;
}

export default function ApiKeysPage() {
    const [keys, setKeys] = useState<ApiKey[]>([
        { id: "1", name: "Production App", key: "sk-proj-892h3f9823hf98h2398fh2398", created: "Jan 15, 2026", lastUsed: "Just now" },
        { id: "2", name: "Development", key: "sk-dev-2398h2398fh2398hf2398h239", created: "Feb 10, 2026", lastUsed: "2 days ago" },
        { id: "3", name: "Test Environment", key: "sk-test-9823hf98h2398fh2398h239", created: "Feb 18, 2026", lastUsed: "Never" },
    ]);

    const generateKey = () => {
        const newKeyString = "sk-" + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        const newKey: ApiKey = {
            id: Math.random().toString(36).substring(7),
            name: "New Secret Key",
            key: newKeyString,
            created: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
            lastUsed: "Never"
        };
        setKeys([newKey, ...keys]);
        toast.success("New API key generated successfully");
    };

    const deleteKey = (id: string) => {
        setKeys(keys.filter(k => k.id !== id));
        toast.info("API key deleted");
    };

    const copyKey = (key: string) => {
        navigator.clipboard.writeText(key);
        toast.success("Copied to clipboard");
    };

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">API Keys</h1>
                    <p className="text-muted-foreground mt-2">
                        Manage your API keys for accessing the Verbix AI Platform. keep your keys secure.
                    </p>
                </div>
                <Button onClick={generateKey} className="gap-2 shadow-lg shadow-primary/20">
                    <Plus className="w-4 h-4" />
                    Create New Secret Key
                </Button>
            </div>

            <div className="grid gap-6">
                <Card className="bg-card/50 border-border/50 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle className="text-xl flex items-center gap-2">
                            <ShieldCheck className="w-5 h-5 text-primary" />
                            Active Keys
                        </CardTitle>
                        <CardDescription>
                            These keys can be used to authenticate requests to the Verbix AI API.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {/* Header */}
                            <div className="hidden md:grid grid-cols-12 gap-4 text-sm font-medium text-muted-foreground uppercase tracking-wider px-4">
                                <div className="col-span-4">Name</div>
                                <div className="col-span-4">Key</div>
                                <div className="col-span-2">Created</div>
                                <div className="col-span-2 text-right">Last Used</div>
                            </div>

                            {/* Rows */}
                            {keys.length === 0 ? (
                                <div className="text-center py-10 text-muted-foreground">
                                    No API keys found. Create one to get started.
                                </div>
                            ) : (
                                keys.map((key) => (
                                    <div key={key.id} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center p-4 rounded-xl bg-card hover:bg-accent/50 transition-colors border border-border/50 group">
                                        <div className="col-span-12 md:col-span-4 font-medium flex items-center gap-2">
                                            <span className={`w-2 h-2 rounded-full animate-pulse ${key.lastUsed === 'Never' ? 'bg-yellow-500' : 'bg-green-500'}`} />
                                            {key.name}
                                        </div>
                                        <div className="col-span-12 md:col-span-4 font-mono text-sm text-muted-foreground flex items-center gap-2 bg-background/50 px-2 py-1 rounded border border-border/30 w-fit">
                                            {key.key.substring(0, 10)}...{key.key.substring(key.key.length - 4)}
                                            <Button onClick={() => copyKey(key.key)} variant="ghost" size="icon" className="h-6 w-6 ml-2 hover:text-primary">
                                                <Copy className="w-3 h-3" />
                                            </Button>
                                        </div>
                                        <div className="col-span-6 md:col-span-2 text-sm text-muted-foreground">
                                            {key.created}
                                        </div>
                                        <div className="col-span-6 md:col-span-2 text-sm text-muted-foreground md:text-right">
                                            {key.lastUsed}
                                        </div>

                                        {/* Actions overlay on hover or mobile */}
                                        <div className="md:opacity-0 group-hover:opacity-100 transition-opacity absolute right-4 flex gap-2">
                                            <Button onClick={() => deleteKey(key.id)} variant="ghost" size="sm" className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10">
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                <Card className="bg-orange-500/5 border-orange-500/20">
                    <CardHeader>
                        <CardTitle className="text-orange-500 text-lg flex items-center gap-2">
                            <RefreshCw className="w-5 h-5" />
                            Key Rotation Policy
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-muted-foreground text-sm">
                            For security reasons, we recommend rotating your API keys every 90 days.
                            Old keys will continue to work for 24 hours after a new key is generated to allow for migration.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
