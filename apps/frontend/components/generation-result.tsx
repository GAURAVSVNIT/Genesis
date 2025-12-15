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

interface GenerationResultProps {
    content: string | null
    isLoading: boolean
}

export function GenerationResult({ content, isLoading }: GenerationResultProps) {
    const [copied, setCopied] = useState(false)

    const handleCopy = async () => {
        if (!content) return
        await navigator.clipboard.writeText(content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
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
    )
}
