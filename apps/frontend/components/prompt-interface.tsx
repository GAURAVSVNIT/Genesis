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
import { VoiceInput } from '@/components/ui/voice-input'
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

    const handleTranscription = (text: string) => {
        setPrompt(prev => prev ? `${prev} ${text}` : text)
    }

    const handleGenerate = async () => {
        if (!prompt.trim()) return

        if (mode === 'text') {
            await generate({ prompt, tone, length, intent: 'blog' })
        } else {
            // Image/Video generation will be implemented later
            alert(`${mode} generation coming soon!`)
        }
    }

    return (
        <div className="w-full min-h-screen py-8 px-4">
            {showAuthGate && <AuthGate feature={mode as 'image' | 'video'} />}

            {/* Hero Section */}
            <div className="text-center space-y-4 mb-12 animate-in fade-in-50 slide-in-from-bottom-5 duration-700">
                <div className="flex justify-center mb-6">
                    <div className="relative">
                        <div className="w-20 h-20 bg-background/50 border border-primary/20 flex items-center justify-center rounded-3xl shadow-2xl shadow-primary/20 backdrop-blur-xl">
                            <span className="text-4xl animate-pulse">✨</span>
                        </div>
                        <div className="absolute -inset-4 bg-primary/20 rounded-[40px] blur-3xl -z-10"></div>
                    </div>
                </div>
                <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-100 to-blue-200">
                    Create Content with AI
                </h1>
                <p className="text-xl text-muted-foreground/80 max-w-2xl mx-auto font-light leading-relaxed">
                    Harness the power of multi-agent AI to generate blogs, images, and videos instantly
                </p>
            </div>

            <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in-50 slide-in-from-bottom-6 duration-1000 delay-100">
                <Card className="p-8 space-y-8 border-border/50 shadow-2xl shadow-primary/5 bg-background/40 backdrop-blur-xl rounded-3xl">
                    {/* Mode Selector */}
                    <div className="space-y-4">
                        <Label className="text-base font-medium text-muted-foreground ml-1">Content Type</Label>
                        <div className="grid grid-cols-3 gap-4">
                            <Button
                                variant={mode === 'text' ? 'default' : 'outline'}
                                onClick={() => handleModeChange('text')}
                                className={`h-14 text-base rounded-2xl transition-all duration-300 ${mode === 'text' ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/25' : 'bg-secondary/50 border-transparent hover:bg-secondary/80'}`}
                            >
                                📝 Text
                            </Button>
                            <Button
                                variant={mode === 'image' ? 'default' : 'outline'}
                                onClick={() => handleModeChange('image')}
                                className={`h-14 text-base rounded-2xl transition-all duration-300 ${mode === 'image' ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/25' : 'bg-secondary/50 border-transparent hover:bg-secondary/80'}`}
                            >
                                🖼️ Image {!isAuthenticated && <span className="ml-2 text-xs opacity-70">🔒</span>}
                            </Button>
                            <Button
                                variant={mode === 'video' ? 'default' : 'outline'}
                                onClick={() => handleModeChange('video')}
                                className={`h-14 text-base rounded-2xl transition-all duration-300 ${mode === 'video' ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/25' : 'bg-secondary/50 border-transparent hover:bg-secondary/80'}`}
                            >
                                🎬 Video {!isAuthenticated && <span className="ml-2 text-xs opacity-70">🔒</span>}
                            </Button>
                        </div>
                    </div>

                    {/* Prompt Input */}
                    <div className="space-y-3">
                        <Label htmlFor="prompt" className="text-base font-medium text-muted-foreground ml-1">
                            Your Creative Brief
                        </Label>
                        <div className="relative group">
                            <Textarea
                                id="prompt"
                                placeholder="Describe what you want to create. Be as detailed as you'd like..."
                                value={prompt}
                                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                                rows={6}
                                className="resize-none rounded-2xl text-base border-border/50 bg-secondary/20 focus:bg-secondary/40 focus:border-primary/50 focus:ring-0 shadow-inner transition-all p-4"
                            />
                            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 opacity-0 group-focus-within:opacity-100 pointer-events-none transition-opacity duration-500"></div>
                            <VoiceInput
                                onTranscription={handleTranscription}
                                className="absolute right-3 bottom-3 z-20 hover:bg-secondary/80"
                                isCompact={true}
                            />
                        </div>
                        <p className="text-xs text-muted-foreground pl-1">💡 Tip: More details = better results</p>
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
                        className="w-full h-14 text-lg font-bold tracking-wide rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-300 border-none"
                        size="lg"
                    >
                        {isLoading ? (
                            <>
                                <span className="animate-spin mr-3">⏳</span>
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
