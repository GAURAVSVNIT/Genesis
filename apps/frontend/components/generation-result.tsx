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

    const formatScore = (score: number | undefined) => {
        if (score === undefined) return 'N/A'
        return (score * 100).toFixed(1) + '%'
    }

    if (isLoading) {
        return (
            <Card>
                <CardContent className="pt-6">
                    <div className="flex items-center justify-center py-12">
                        <div className="flex flex-col items-center gap-4">
                            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                            <p className="text-sm text-muted-foreground">Generating content...</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    if (!content) return null

    return (
        <div className="space-y-4">
            {/* Metrics Summary */}
            {metrics && (
                <Card className="bg-muted/50">
                    <CardContent className="pt-6">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {/* Quality Scores */}
                            {metrics.seo_score !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">SEO Score</p>
                                    <p className="text-lg font-semibold">{formatScore(metrics.seo_score)}</p>
                                </div>
                            )}
                            {metrics.uniqueness_score !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Uniqueness</p>
                                    <p className="text-lg font-semibold">{formatScore(metrics.uniqueness_score)}</p>
                                </div>
                            )}
                            {metrics.engagement_score !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Engagement</p>
                                    <p className="text-lg font-semibold">{formatScore(metrics.engagement_score)}</p>
                                </div>
                            )}
                            {metrics.cost_usd !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Cost</p>
                                    <p className="text-lg font-semibold">${metrics.cost_usd.toFixed(5)}</p>
                                </div>
                            )}
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                            {/* Cache & Performance */}
                            {metrics.cached !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Cache</p>
                                    <p className="text-sm font-medium">{metrics.cached ? '✓ Hit' : '✗ Miss'}</p>
                                </div>
                            )}
                            {metrics.generation_time_ms !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Time</p>
                                    <p className="text-sm font-medium">{metrics.generation_time_ms}ms</p>
                                </div>
                            )}
                            {metrics.cache_hit_rate !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Hit Rate</p>
                                    <p className="text-sm font-medium">{(metrics.cache_hit_rate * 100).toFixed(1)}%</p>
                                </div>
                            )}
                            {metrics.total_cost_usd !== undefined && (
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Total Cost</p>
                                    <p className="text-sm font-medium">${metrics.total_cost_usd.toFixed(5)}</p>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Rate Limiting Info */}
            {metrics && metrics.rate_limit_remaining !== undefined && (
                <div className="text-xs text-muted-foreground text-center">
                    Requests remaining: {metrics.rate_limit_remaining} | Resets in {metrics.rate_limit_reset_after}s
                </div>
            )}

            {/* Content Card */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Generated Content</CardTitle>
                            <CardDescription>Your AI-generated blog post</CardDescription>
                        </div>
                        <Button onClick={handleCopy} variant="outline" size="sm">
                            {copied ? 'Copied!' : 'Copy'}
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                        <div className="whitespace-pre-wrap">{content}</div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
