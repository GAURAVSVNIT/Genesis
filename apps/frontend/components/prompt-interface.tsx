'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { useGeneration } from '@/lib/hooks/use-generation'
import { GenerationResult } from './generation-result'
import { AuthGate } from './auth-gate'
import Link from 'next/link'

interface PromptInterfaceProps {
    isAuthenticated: boolean
}

type Mode = 'text' | 'image' | 'video'

export function PromptInterface({ isAuthenticated }: PromptInterfaceProps) {
    const [mode, setMode] = useState<Mode>('text')
    const [prompt, setPrompt] = useState('')
    const [tone, setTone] = useState('informative')
    const [length, setLength] = useState('medium')
    const [showAuthGate, setShowAuthGate] = useState(false)

    const { generate, isLoading, generatedContent, metrics, error, remainingGenerations, hasReachedLimit } =
        useGeneration(isAuthenticated)

    const handleModeChange = (newMode: Mode) => {
        if (!isAuthenticated && (newMode === 'image' || newMode === 'video')) {
            setShowAuthGate(true)
            return
        }
        setMode(newMode)
    }

    const handleGenerate = async () => {
        if (!prompt.trim()) return

        if (mode === 'text') {
            await generate({ prompt, tone, length })
        } else {
            // Image/Video generation will be implemented later
            alert(`${mode} generation coming soon!`)
        }
    }

    return (
        <div className="w-full min-h-screen py-8 px-4">
            {showAuthGate && <AuthGate feature={mode as 'image' | 'video'} />}

            {/* Hero Section */}
            <div className="text-center space-y-4 mb-12">
                <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border border-primary/10">
                        <span className="text-3xl">✨</span>
                    </div>
                </div>
                <h1 className="text-5xl md:text-6xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground to-foreground/70">
                    Create Content with AI
                </h1>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Harness the power of multi-agent AI to generate blogs, images, and videos instantly
                </p>
            </div>

            <div className="max-w-4xl mx-auto space-y-6">
                <Card className="p-8 space-y-8 border-border/50 shadow-lg backdrop-blur-sm bg-card/50">
                    {/* Mode Selector */}
                    <div className="space-y-4">
                        <Label className="text-base font-semibold">Content Type</Label>
                        <div className="grid grid-cols-3 gap-3">
                            <Button
                                variant={mode === 'text' ? 'default' : 'outline'}
                                onClick={() => handleModeChange('text')}
                                className="h-12 text-base"
                            >
                                📝 Text
                            </Button>
                            <Button
                                variant={mode === 'image' ? 'default' : 'outline'}
                                onClick={() => handleModeChange('image')}
                                className="h-12 text-base"
                            >
                                🖼️ Image {!isAuthenticated && '🔒'}
                            </Button>
                            <Button
                                variant={mode === 'video' ? 'default' : 'outline'}
                                onClick={() => handleModeChange('video')}
                                className="h-12 text-base"
                            >
                                🎬 Video {!isAuthenticated && '🔒'}
                            </Button>
                        </div>
                    </div>

                    {/* Prompt Input */}
                    <div className="space-y-3">
                        <Label htmlFor="prompt" className="text-base font-semibold">
                            Your Creative Brief
                        </Label>
                        <Textarea
                            id="prompt"
                            placeholder="Describe what you want to create. Be as detailed as you'd like..."
                            value={prompt}
                            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                            rows={6}
                            className="resize-none rounded-xl text-base border-border/50 focus:border-primary focus:ring-primary/20"
                        />
                        <p className="text-xs text-muted-foreground">💡 Tip: More details = better results</p>
                    </div>

                    {/* Text Mode Options */}
                    {mode === 'text' && (
                        <div className="space-y-4">
                            <Label className="text-base font-semibold">Content Settings</Label>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-3">
                                    <Label htmlFor="tone" className="text-sm">Writing Tone</Label>
                                    <Select value={tone} onValueChange={setTone}>
                                        <SelectTrigger id="tone" className="border-border/50">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="informative">📚 Informative</SelectItem>
                                            <SelectItem value="casual">😊 Casual</SelectItem>
                                            <SelectItem value="professional">💼 Professional</SelectItem>
                                            <SelectItem value="friendly">🤝 Friendly</SelectItem>
                                            <SelectItem value="formal">🎩 Formal</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-3">
                                    <Label htmlFor="length" className="text-sm">Content Length</Label>
                                    <Select value={length} onValueChange={setLength}>
                                        <SelectTrigger id="length" className="border-border/50">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="short">📝 Short (300-500 words)</SelectItem>
                                            <SelectItem value="medium">📄 Medium (800-1200 words)</SelectItem>
                                            <SelectItem value="long">📚 Long (1500+ words)</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Generate Button */}
                    <Button
                        onClick={handleGenerate}
                        disabled={isLoading || !prompt.trim() || hasReachedLimit}
                        className="w-full h-12 text-base font-semibold"
                        size="lg"
                    >
                        {isLoading ? (
                            <>
                                <span className="animate-spin mr-2">⏳</span>
                                Generating your content...
                            </>
                        ) : (
                            <>
                                ✨ Generate Content
                            </>
                        )}
                    </Button>

                    {/* Usage Counter for Anonymous Users */}
                    {!isAuthenticated && (
                        <div className="text-center space-y-3 py-3 px-4 bg-primary/5 rounded-lg border border-primary/10">
                            {hasReachedLimit ? (
                                <div className="space-y-2">
                                    <p className="text-sm text-destructive font-semibold">
                                        🎯 You've used your free generations
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        <Link href="/auth/sign-up" className="text-primary font-semibold hover:underline">
                                            Create an account
                                        </Link>
                                        {' '}for unlimited access
                                    </p>
                                </div>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    💡 {remainingGenerations}/5 free generations • 
                                    <Link href="/auth/sign-up" className="text-primary font-semibold hover:underline ml-1">
                                        Sign in for unlimited
                                    </Link>
                                </p>
                            )}
                        </div>
                    )}

                    {/* Error Display */}
                    {error && (
                        <div className="p-4 bg-destructive/10 text-destructive rounded-lg text-sm border border-destructive/20 flex items-start gap-3">
                            <span className="text-lg flex-shrink-0">⚠️</span>
                            <span>{error}</span>
                        </div>
                    )}
                </Card>

                {/* Generated Content */}
                {(generatedContent || isLoading) && (
                    <div className="space-y-4 animate-in fade-in-50 slide-in-from-bottom-4 duration-300">
                        <GenerationResult content={generatedContent} isLoading={isLoading} metrics={metrics} />
                    </div>
                )}
            </div>
        </div>
    )
}
