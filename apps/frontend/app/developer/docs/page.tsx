"use client";

import { Button } from "@/components/ui/button";
import { Copy, Terminal, Server, Code, PlayCircle, Layers, AlertCircle, Zap } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function DocsPage() {
    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast.success("Code copied to clipboard");
    };

    return (
        <div className="space-y-12 pb-20">
            {/* Header */}
            <div className="space-y-4">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent w-fit">
                    API Documentation
                </h1>
                <p className="text-xl text-muted-foreground font-light max-w-2xl">
                    Complete reference for the Verbix AI Platform API.          Integrate the power of Verbix AI into your applications with our simple REST API.interface.
                </p>
                <div className="flex gap-2 pt-2">
                    <Badge variant="outline" className="text-xs bg-primary/10 text-primary border-primary/20">v1.2.0</Badge>
                    <Badge variant="outline" className="text-xs">Uptime 99.99%</Badge>
                </div>
            </div>

            <div className="grid gap-8 lg:grid-cols-4">
                {/* Main Content */}
                <div className="lg:col-span-3 space-y-16">

                    {/* Quick Start */}
                    <section id="quick-start" className="scroll-mt-24 space-y-6">
                        <div className="p-6 rounded-2xl border border-primary/20 bg-primary/5 backdrop-blur-sm relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <Terminal className="w-32 h-32" />
                            </div>
                            <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
                                <PlayCircle className="w-6 h-6 text-primary" />
                                Quick Start
                            </h3>
                            <p className="text-muted-foreground mb-6 leading-relaxed">
                                To interact with the Verbix AI API, you'll need an API Key.
                                Include this key in the <code className="bg-primary/10 px-2 py-1 rounded text-primary font-mono text-sm">Authorization</code> header of your requests.
                            </p>

                            <div className="bg-black/50 rounded-xl border border-border/50 overflow-hidden relative group">
                                <div className="flex items-center justify-between px-4 py-2 bg-muted/20 border-b border-border/20">
                                    <div className="flex gap-1">
                                        <div className="w-3 h-3 rounded-full bg-red-500/50" />
                                        <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                                        <div className="w-3 h-3 rounded-full bg-green-500/50" />
                                    </div>
                                    <span className="text-xs text-muted-foreground font-mono">bash</span>
                                </div>
                                <pre className="p-4 text-sm font-mono overflow-x-auto text-green-400">
                                    curl https://api.verbix.ai/v1/analyze \<br />
                                    &nbsp;&nbsp;-H "Content-Type: application/json" \<br />
                                    &nbsp;&nbsp;-H "Authorization: Bearer sk-proj-..." \<br />
                                    &nbsp;&nbsp;-d &#39;&#123;"text": "Analyze the sentiment of this text."&#125;&#39;
                                </pre>
                                <Button
                                    size="icon"
                                    variant="ghost"
                                    className="absolute top-12 right-4 opacity-0 group-hover:opacity-100 transition-opacity bg-background/50 hover:bg-background"
                                    onClick={() => copyToClipboard('curl https://api.verbix.ai/v1/analyze \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer sk-proj-..." \\\n  -d \'{"text": "Analyze the sentiment of this text."}\'')}
                                >
                                    <Copy className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    </section>

                    {/* Authentication */}
                    <section id="authentication" className="scroll-mt-24 space-y-6">
                        <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                            <Server className="w-6 h-6 text-purple-400" />
                            <h2 className="text-3xl font-bold">Authentication</h2>
                        </div>
                        <p className="text-muted-foreground text-lg leading-relaxed">
                            The Verbix AI API uses API keys to authenticate requests. You can view and manage your API keys in the <a href="/developer/api-keys" className="text-primary hover:underline font-medium">API Keys</a> section.
                            Your API keys carry many privileges, so be sure to keep them secure! Do not share your secret API keys in publicly accessible areas such as GitHub, client-side code, and so forth.
                        </p>

                        <Card className="bg-card/50 border-border/50">
                            <CardHeader>
                                <CardTitle className="text-base text-muted-foreground uppercase tracking-wider">Base URL</CardTitle>
                                <CardDescription className="text-xl font-mono text-foreground bg-background/50 p-3 rounded-md border border-border/50 flex justify-between items-center group">
                                    https://api.verbix.ai/v1
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                                        onClick={() => copyToClipboard('https://api.verbix.ai/v1')}
                                    >
                                        <Copy className="w-4 h-4" />
                                    </Button>
                                </CardDescription>
                            </CardHeader>
                        </Card>
                    </section>

                    {/* Models */}
                    <section id="models" className="scroll-mt-24 space-y-6">
                        <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                            <Layers className="w-6 h-6 text-blue-400" />
                            <h2 className="text-3xl font-bold">Models</h2>
                        </div>
                        <p className="text-muted-foreground text-lg">
                            Verbix AI offers a range of models with different capabilities and price points.
                        </p>

                        <div className="rounded-xl border border-border overflow-hidden">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-muted/50 text-muted-foreground uppercase font-medium border-b border-border">
                                    <tr>
                                        <th className="px-6 py-4">Model ID</th>
                                        <th className="px-6 py-4">Description</th>
                                        <th className="px-6 py-4">Context Window</th>
                                        <th className="px-6 py-4">Training Data</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/50 bg-card/30">
                                    {[
                                        { id: "verbix-v4-turbo", desc: "Our most capable model for high-complexity tasks.", context: "128k", data: "Up to Oct 2025" },
                                        { id: "verbix-v4-standard", desc: "Balanced performance and cost.", context: "32k", data: "Up to Sep 2024" },
                                        { id: "verbix-image-ultra", desc: "State-of-the-art image generation model.", context: "N/A", data: "Visual Dataset v3" },
                                        { id: "verbix-video-pro", desc: "High-fidelity video synthesis.", context: "N/A", data: "Video Dataset v2" },
                                    ].map((model, i) => (
                                        <tr key={i} className="hover:bg-muted/30 transition-colors">
                                            <td className="px-6 py-4 font-mono font-bold text-primary">{model.id}</td>
                                            <td className="px-6 py-4 text-muted-foreground">{model.desc}</td>
                                            <td className="px-6 py-4 font-mono text-xs">{model.context}</td>
                                            <td className="px-6 py-4 text-xs text-muted-foreground">{model.data}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Endpoints */}
                    <section id="endpoints" className="scroll-mt-24 space-y-12">
                        <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                            <Code className="w-6 h-6 text-green-400" />
                            <h2 className="text-3xl font-bold">Endpoints</h2>
                        </div>

                        {/* Chat Completions */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <span className="px-3 py-1 rounded-md bg-green-500/10 text-green-500 font-bold text-sm border border-green-500/20">POST</span>
                                <h3 className="text-xl font-mono font-semibold">/chat/completions</h3>
                            </div>
                            <p className="text-muted-foreground">Creates a model response for the given chat conversation.</p>

                            <Card className="bg-card/30 border-border/50">
                                <CardContent className="p-0">
                                    <div className="rounded-xl overflow-hidden border border-border/50">
                                        <table className="w-full text-sm text-left">
                                            <thead className="bg-muted/30 text-xs uppercase text-muted-foreground">
                                                <tr>
                                                    <th className="px-4 py-3">Parameter</th>
                                                    <th className="px-4 py-3">Type</th>
                                                    <th className="px-4 py-3">Required</th>
                                                    <th className="px-4 py-3">Description</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border/20">
                                                <tr className="bg-background/20">
                                                    <td className="px-4 py-3 font-mono text-primary">model</td>
                                                    <td className="px-4 py-3 font-mono text-xs">string</td>
                                                    <td className="px-4 py-3 text-red-400 text-xs font-bold">Yes</td>
                                                    <td className="px-4 py-3 text-muted-foreground">ID of the model to use.</td>
                                                </tr>
                                                <tr className="bg-background/20">
                                                    <td className="px-4 py-3 font-mono text-primary">messages</td>
                                                    <td className="px-4 py-3 font-mono text-xs">array</td>
                                                    <td className="px-4 py-3 text-red-400 text-xs font-bold">Yes</td>
                                                    <td className="px-4 py-3 text-muted-foreground">A list of messages comprising the conversation so far.</td>
                                                </tr>
                                                <tr className="bg-background/20">
                                                    <td className="px-4 py-3 font-mono text-primary">temperature</td>
                                                    <td className="px-4 py-3 font-mono text-xs">number</td>
                                                    <td className="px-4 py-3 text-muted-foreground text-xs">No</td>
                                                    <td className="px-4 py-3 text-muted-foreground">Sampling temperature (0 to 2). Defaults to 1.</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </CardContent>
                            </Card>

                            <div className="relative group/code mt-4">
                                <div className="bg-slate-950 rounded-lg p-5 font-mono text-sm border border-border/50 text-blue-300 shadow-xl overflow-x-auto">
                                    <div className="flex justify-between items-center mb-2 pb-2 border-b border-white/10">
                                        <span className="text-xs text-muted-foreground">Example Request</span>
                                        <span className="text-xs text-green-400">JSON</span>
                                    </div>
                                    <pre>{`{
  "model": "verbix-v4-turbo",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing in simple terms."}
  ]
}`}</pre>
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="absolute top-4 right-4 opacity-0 group-hover/code:opacity-100 transition-opacity bg-background/20 hover:bg-background/40 text-white"
                                        onClick={() => copyToClipboard(`{ "model": "verbix-v4-turbo", "messages": [ {"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Explain quantum computing in simple terms."} ] }`)}
                                    >
                                        <Copy className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>

                        <div className="w-full h-px bg-border/50" />

                        {/* Image Generation */}
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                <span className="px-3 py-1 rounded-md bg-green-500/10 text-green-500 font-bold text-sm border border-green-500/20">POST</span>
                                <h3 className="text-xl font-mono font-semibold">/images/generations</h3>
                            </div>
                            <p className="text-muted-foreground">Creates an image given a prompt.</p>

                            <Card className="bg-card/30 border-border/50">
                                <CardContent className="p-0">
                                    <div className="rounded-xl overflow-hidden border border-border/50">
                                        <table className="w-full text-sm text-left">
                                            <thead className="bg-muted/30 text-xs uppercase text-muted-foreground">
                                                <tr>
                                                    <th className="px-4 py-3">Parameter</th>
                                                    <th className="px-4 py-3">Type</th>
                                                    <th className="px-4 py-3">Required</th>
                                                    <th className="px-4 py-3">Description</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-border/20">
                                                <tr className="bg-background/20">
                                                    <td className="px-4 py-3 font-mono text-primary">prompt</td>
                                                    <td className="px-4 py-3 font-mono text-xs">string</td>
                                                    <td className="px-4 py-3 text-red-400 text-xs font-bold">Yes</td>
                                                    <td className="px-4 py-3 text-muted-foreground">A text description of the desired image.</td>
                                                </tr>
                                                <tr className="bg-background/20">
                                                    <td className="px-4 py-3 font-mono text-primary">n</td>
                                                    <td className="px-4 py-3 font-mono text-xs">integer</td>
                                                    <td className="px-4 py-3 text-muted-foreground text-xs">No</td>
                                                    <td className="px-4 py-3 text-muted-foreground">Number of images to generate (1-10). Defaults to 1.</td>
                                                </tr>
                                                <tr className="bg-background/20">
                                                    <td className="px-4 py-3 font-mono text-primary">size</td>
                                                    <td className="px-4 py-3 font-mono text-xs">string</td>
                                                    <td className="px-4 py-3 text-muted-foreground text-xs">No</td>
                                                    <td className="px-4 py-3 text-muted-foreground">The size of the generated images. Must be one of 256x256, 512x512, or 1024x1024.</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </CardContent>
                            </Card>

                            <div className="relative group/code mt-4">
                                <div className="bg-slate-950 rounded-lg p-5 font-mono text-sm border border-border/50 text-blue-300 shadow-xl overflow-x-auto">
                                    <div className="flex justify-between items-center mb-2 pb-2 border-b border-white/10">
                                        <span className="text-xs text-muted-foreground">Example Request</span>
                                        <span className="text-xs text-green-400">JSON</span>
                                    </div>
                                    <pre>{`{
  "prompt": "A cute baby sea otter",
  "n": 2,
  "size": "1024x1024"
}`}</pre>
                                    <Button
                                        size="icon"
                                        variant="ghost"
                                        className="absolute top-4 right-4 opacity-0 group-hover/code:opacity-100 transition-opacity bg-background/20 hover:bg-background/40 text-white"
                                        onClick={() => copyToClipboard(`{ "prompt": "A cute baby sea otter", "n": 2, "size": "1024x1024" }`)}
                                    >
                                        <Copy className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Errors */}
                    <section id="errors" className="scroll-mt-24 space-y-6">
                        <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                            <AlertCircle className="w-6 h-6 text-red-400" />
                            <h2 className="text-3xl font-bold">Errors</h2>
                        </div>
                        <p className="text-muted-foreground text-lg">
                            Verbix AI API uses standard HTTP response codes to indicate the success or failure of an API request.
                        </p>

                        <div className="rounded-xl border border-border overflow-hidden">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-muted/50 text-muted-foreground uppercase font-medium border-b border-border">
                                    <tr>
                                        <th className="px-6 py-4">Code</th>
                                        <th className="px-6 py-4">Error Type</th>
                                        <th className="px-6 py-4">Description</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/50 bg-card/30">
                                    {[
                                        { code: 400, type: "Bad Request", desc: "The request was unacceptable, often due to missing a required parameter." },
                                        { code: 401, type: "Unauthorized", desc: "No valid API key provided." },
                                        { code: 429, type: "Too Many Requests", desc: "Too many requests hit the API too quickly. We recommend an exponential backoff of your requests." },
                                        { code: 500, type: "Server Error", desc: "Something went wrong on our end." },
                                    ].map((err, i) => (
                                        <tr key={i} className="hover:bg-muted/30 transition-colors">
                                            <td className="px-6 py-4 font-mono font-bold text-red-400">{err.code}</td>
                                            <td className="px-6 py-4 font-semibold">{err.type}</td>
                                            <td className="px-6 py-4 text-muted-foreground">{err.desc}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Rate Limits */}
                    <section id="rate-limits" className="scroll-mt-24 space-y-6">
                        <div className="flex items-center gap-2 border-b border-border/50 pb-2">
                            <Zap className="w-6 h-6 text-yellow-400" />
                            <h2 className="text-3xl font-bold">Rate Limits</h2>
                        </div>
                        <p className="text-muted-foreground text-lg">
                            Rate limits are enforced at the organization level.
                        </p>

                        <div className="grid md:grid-cols-3 gap-6">
                            {[
                                { tier: "Free", rpm: "3 RPM", tpm: "40K TPM", color: "border-border/50" },
                                { tier: "Pro", rpm: "60 RPM", tpm: "160K TPM", color: "border-primary/50 bg-primary/5" },
                                { tier: "Enterprise", rpm: "500+ RPM", tpm: "Unlimited", color: "border-purple-500/50 bg-purple-500/5" },
                            ].map((tier, i) => (
                                <Card key={i} className={`backdrop-blur-sm border ${tier.tier === 'Pro' ? 'shadow-lg shadow-primary/10' : ''} ${tier.color}`}>
                                    <CardHeader>
                                        <CardTitle className="text-xl">{tier.tier} Tier</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div>
                                            <div className="text-2xl font-bold">{tier.rpm}</div>
                                            <div className="text-xs text-muted-foreground uppercase tracking-wider">Requests per Minute</div>
                                        </div>
                                        <div>
                                            <div className="text-2xl font-bold">{tier.tpm}</div>
                                            <div className="text-xs text-muted-foreground uppercase tracking-wider">Tokens per Minute</div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </section>

                </div>

                {/* Sidebar Navigation */}
                <div className="hidden lg:block">
                    <div className="sticky top-8 space-y-8">
                        <div className="p-5 rounded-xl bg-card/30 border border-border/50 shadow-sm backdrop-blur-md">
                            <h4 className="font-bold mb-4 text-xs uppercase tracking-wider text-muted-foreground">On this page</h4>
                            <nav className="space-y-1 text-sm">
                                {[
                                    { name: "Quick Start", href: "#quick-start" },
                                    { name: "Authentication", href: "#authentication" },
                                    { name: "Models", href: "#models" },
                                    { name: "Endpoints", href: "#endpoints" },
                                    { name: "Errors", href: "#errors" },
                                    { name: "Rate Limits", href: "#rate-limits" },
                                ].map((item, i) => (
                                    <a
                                        key={i}
                                        href={item.href}
                                        className="block px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors text-muted-foreground hover:translate-x-1 duration-200"
                                    >
                                        {item.name}
                                    </a>
                                ))}
                            </nav>
                        </div>

                        <div className="p-5 rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20 shadow-lg">
                            <h4 className="font-bold text-blue-400 mb-2 flex items-center gap-2">
                                <AlertCircle className="w-4 h-4" /> Need Support?
                            </h4>
                            <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                                Our engineering team is available 24/7 to help you with your integration.
                            </p>
                            <div className="space-y-2">
                                <Button variant="outline" size="sm" className="w-full border-blue-500/30 hover:bg-blue-500/20 text-blue-400">
                                    Join Discord
                                </Button>
                                <Button variant="ghost" size="sm" className="w-full hover:bg-white/5">
                                    Contact Sales
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
