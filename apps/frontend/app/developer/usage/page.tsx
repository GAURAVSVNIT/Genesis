"use client";


import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MoveUpRight, Zap, RefreshCw, AlertTriangle, TrendingUp } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function UsagePage() {
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState({
        requests: 14293,
        requestsChange: "+20.1%",
        balance: 450.00,
        latency: 124,
        latencyChange: "-12ms",
        errorRate: "0.02%"
    });

    const refreshStats = () => {
        setLoading(true);
        setTimeout(() => {
            setStats({
                requests: Math.floor(Math.random() * 20000) + 10000,
                requestsChange: `+${(Math.random() * 30).toFixed(1)}%`,
                balance: parseFloat((Math.random() * 1000).toFixed(2)),
                latency: Math.floor(Math.random() * 200) + 50,
                latencyChange: `-${Math.floor(Math.random() * 20)}ms`,
                errorRate: `${(Math.random() * 0.1).toFixed(2)}%`
            });
            setLoading(false);
            toast.info("Usage statistics updated");
        }, 1000);
    };

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Usage & Billing</h1>
                    <p className="text-muted-foreground mt-2">
                        Monitor API usage, rate limits, and billing details.
                    </p>
                </div>
                <Button onClick={refreshStats} variant="outline" className="gap-2" disabled={loading}>
                    <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                    {loading ? "Refreshing..." : "Refresh"}
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card className="bg-card/40 hover:bg-card/60 transition-colors border-border/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
                        <TrendingUp className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.requests.toLocaleString()}</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.requestsChange} from last month
                        </p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40 hover:bg-card/60 transition-colors border-border/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Credit Balance</CardTitle>
                        <Zap className="h-4 w-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">${stats.balance.toFixed(2)}</div>
                        <p className="text-xs text-muted-foreground">
                            Available for immediate use
                        </p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40 hover:bg-card/60 transition-colors border-border/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
                        <MoveUpRight className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.latency}ms</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.latencyChange} improvement
                        </p>
                    </CardContent>
                </Card>
                <Card className="bg-card/40 hover:bg-card/60 transition-colors border-border/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.errorRate}</div>
                        <p className="text-xs text-muted-foreground">
                            Within SLA limits
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-7">
                <Card className="md:col-span-4 bg-card/30 border-border/50">
                    <CardHeader>
                        <CardTitle>Usage Over Time</CardTitle>
                        <CardDescription>
                            API requests for the past 30 days.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pl-2">
                        <div className="h-[200px] flex items-end justify-between gap-2 px-4">
                            {[45, 60, 30, 80, 50, 90, 100, 70, 40, 60, 55, 85, 95, 20, 40, 60, 80, 75, 55, 65, 90, 85, 60, 40, 50, 70, 80, 95, 100, 110].map((h, i) => (
                                <div
                                    key={i}
                                    className="w-full bg-primary/20 hover:bg-primary/50 transition-all rounded-t-sm relative group"
                                    style={{ height: `${h}%` }}
                                >
                                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-popover text-popover-foreground text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                                        {h * 10} reqs
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="flex justify-between mt-4 text-xs text-muted-foreground px-4 font-mono uppercase tracking-wider">
                            <span>Feb 01</span>
                            <span>Feb 10</span>
                            <span>Feb 19</span>
                        </div>
                    </CardContent>
                </Card>
                <Card className="md:col-span-3 bg-card/30 border-border/50">
                    <CardHeader>
                        <CardTitle>Usage by Model</CardTitle>
                        <CardDescription>
                            Distribution of requests across different AI models.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[
                                { model: "Verbix-V4 (Text)", percent: 65, color: "bg-blue-500" },
                                { model: "Verbix-Diffusion (Image)", percent: 25, color: "bg-purple-500" },
                                { model: "Verbix-Voice (Audio)", percent: 10, color: "bg-green-500" }
                            ].map((item, i) => (
                                <div key={i} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium">{item.model}</span>
                                        <span className="text-muted-foreground">{item.percent}%</span>
                                    </div>
                                    <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                                        <div className={`h-full ${item.color}`} style={{ width: `${item.percent}%` }} />
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="mt-8 pt-6 border-t border-border/50">
                            <h4 className="font-semibold mb-4 text-sm">Plan Limits</h4>
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                                    <span>75% of monthly quota used</span>
                                    <span>75,000 / 100,000</span>
                                </div>
                                <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                                    <div className="h-full bg-orange-500 w-[75%]" />
                                </div>
                            </div>
                            <div className="mt-4">
                                <Button variant="outline" size="sm" className="w-full">
                                    Upgrade Plan
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
