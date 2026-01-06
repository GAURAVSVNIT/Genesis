'use client'

import { Button } from '@/components/ui/button'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card'
import { useState } from 'react'
import { Copy, Check, Download, Share2 } from 'lucide-react'

interface GenerationMetrics {
    seo_score?: number
    uniqueness_score?: number
    engagement_score?: number
    cost_usd?: number
    total_cost_usd?: number
    cached?: boolean
    cache_hit_rate?: number
    generation_time_ms?: number
    rate_limit_remaining?: number
    rate_limit_reset_after?: number
}

interface GenerationResultProps {
    content: string | null
    isLoading: boolean
    metrics?: GenerationMetrics
}

export function GenerationResult({ content, isLoading, metrics }: GenerationResultProps) {
    const [copied, setCopied] = useState(false)

    const handleCopy = async () => {
        if (!content) return
        await navigator.clipboard.writeText(content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const handleDownload = () => {
        if (!content) return
        const element = document.createElement('a')
        const file = new Blob([content], { type: 'text/plain' })
        element.href = URL.createObjectURL(file)
        element.download = 'generated-content.txt'
        document.body.appendChild(element)
        element.click()
        document.body.removeChild(element)
    }

    const formatScore = (score: number | undefined) => {
        if (score === undefined) return 'N/A'
        return (score * 100).toFixed(0)
    }

    const getScoreColor = (score: number | undefined) => {
        if (score === undefined) return 'text-muted-foreground'
        if (score >= 0.8) return 'text-green-600 dark:text-green-400'
        if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
        return 'text-orange-600 dark:text-orange-400'
    }

    if (isLoading) {
        return (
            <Card className="border border-border/50 bg-card/60 backdrop-blur-sm rounded-2xl shadow-lg">
                <CardContent className="pt-12">
                    <div className="flex items-center justify-center py-12">
                        <div className="flex flex-col items-center gap-4">
                            <div className="relative w-12 h-12 bg-background/50 border border-primary/20 flex items-center justify-center animate-spin rounded-xl shadow-lg shadow-primary/20 backdrop-blur-md">
                                <div className="w-4 h-4 bg-primary rounded-sm" />
                            </div>
                            <div className="text-center">
                                <p className="text-sm font-medium text-foreground tracking-wide">GENERATING CONTENT...</p>
                                <p className="text-xs text-muted-foreground mt-1 font-mono uppercase tracking-widest opacity-70">Please wait</p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
        )
    }

    if (!content) return null

    return (
        <div className="space-y-6 animate-in fade-in-50 slide-in-from-bottom-4 duration-500">
            {/* Metrics Summary */}
            {metrics && (
                <Card className="border border-border/50 bg-card/40 backdrop-blur-md rounded-2xl shadow-xl">
                    <CardContent className="pt-6">
                        <h3 className="text-xs font-semibold mb-4 text-muted-foreground uppercase tracking-widest pl-1">Quality Metrics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {/* Quality Scores */}
                            {metrics.seo_score !== undefined && (
                                <div className="p-3 bg-background/50 border border-border/50 rounded-xl shadow-sm backdrop-blur-sm">
                                    <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wide">SEO Score</p>
                                    <p className={`text-2xl font-bold ${getScoreColor(metrics.seo_score)}`}>
                                        {formatScore(metrics.seo_score)}%
                                    </p>
                                </div>
                            )}
                            {metrics.uniqueness_score !== undefined && (
                                <div className="p-3 bg-background/50 border border-border/50 rounded-xl shadow-sm backdrop-blur-sm">
                                    <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wide">Uniqueness</p>
                                    <p className={`text-2xl font-bold ${getScoreColor(metrics.uniqueness_score)}`}>
                                        {formatScore(metrics.uniqueness_score)}%
                                    </p>
                                </div>
                            )}
                            {metrics.engagement_score !== undefined && (
                                <div className="p-3 bg-background/50 border border-border/50 rounded-xl shadow-sm backdrop-blur-sm">
                                    <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wide">Engagement</p>
                                    <p className={`text-2xl font-bold ${getScoreColor(metrics.engagement_score)}`}>
                                        {formatScore(metrics.engagement_score)}%
                                    </p>
                                </div>
                            )}
                            {metrics.cost_usd !== undefined && (
                                <div className="p-3 bg-background/50 border border-border/50 rounded-xl shadow-sm backdrop-blur-sm">
                                    <p className="text-xs text-muted-foreground mb-1 font-medium uppercase tracking-wide">Generation Cost</p>
                                    <p className="text-2xl font-bold text-primary">
                                        ${metrics.cost_usd.toFixed(4)}
                                    </p>
                                </div>
                            )}
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-border/30">
                            {/* Cache & Performance */}
                            {metrics.cached !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Cache Status</p>
                                    <p className="text-sm font-semibold flex items-center gap-1">
                                        {metrics.cached ? '✅ Hit' : '⚡ Fresh'}
                                    </p>
                                </div>
                            )}
                            {metrics.generation_time_ms !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Generation Time</p>
                                    <p className="text-sm font-semibold">{metrics.generation_time_ms}ms</p>
                                </div>
                            )}
                            {metrics.cache_hit_rate !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Cache Hit Rate</p>
                                    <p className="text-sm font-semibold">{(metrics.cache_hit_rate * 100).toFixed(1)}%</p>
                                </div>
                            )}
                            {metrics.total_cost_usd !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Session Cost</p>
                                    <p className="text-sm font-semibold">${metrics.total_cost_usd.toFixed(4)}</p>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Rate Limiting Info */}
            {metrics && metrics.rate_limit_remaining !== undefined && (
                <div className="text-xs text-muted-foreground text-center p-2 bg-muted/30 rounded-lg border border-border/50 font-mono backdrop-blur-sm">
                    📊 {metrics.rate_limit_remaining} requests remaining • Resets in {metrics.rate_limit_reset_after}s
                </div>
            )}

            {/* Content Card */}
            <Card className="border border-border/50 overflow-hidden rounded-2xl shadow-xl bg-card/60 backdrop-blur-md">
                <CardHeader className="border-b border-border/50 bg-secondary/30 backdrop-blur-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle className="text-xl font-medium tracking-tight">Generated Content</CardTitle>
                            <CardDescription className="opacity-80">Ready to use and customize</CardDescription>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                onClick={handleDownload}
                                variant="outline"
                                size="sm"
                                className="gap-2 rounded-lg hover:bg-white/10"
                                title="Download as text file"
                            >
                                <Download className="w-4 h-4" />
                                <span className="hidden sm:inline">Download</span>
                            </Button>
                            <Button
                                onClick={handleCopy}
                                variant={copied ? "default" : "outline"}
                                size="sm"
                                className={`gap-2 rounded-lg ${copied ? 'bg-green-600 hover:bg-green-700' : 'hover:bg-white/10'}`}
                            >
                                {copied ? (
                                    <>
                                        <Check className="w-4 h-4" />
                                        <span className="hidden sm:inline">Copied!</span>
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-4 h-4" />
                                        <span className="hidden sm:inline">Copy</span>
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="pt-6">
                    <div className="prose prose-sm max-w-none dark:prose-invert prose-pre:bg-muted prose-pre:border prose-pre:rounded-lg">
                        <div className="text-foreground leading-relaxed whitespace-pre-wrap font-normal">
                            {content}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
