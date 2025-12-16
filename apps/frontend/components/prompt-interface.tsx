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

    const { generate, isLoading, generatedContent, error, remainingGenerations, hasReachedLimit } =
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
        <div className="w-full max-w-4xl mx-auto space-y-6">
            {showAuthGate && <AuthGate feature={mode as 'image' | 'video'} />}

            <div className="text-center space-y-2">
                <h1 className="text-4xl font-bold tracking-tight">Generate Content with AI</h1>
                <p className="text-lg text-muted-foreground">
                    Create blog posts, images, and videos using advanced AI
                </p>
            </div>

            <Card className="p-6 space-y-6">
                {/* Mode Selector */}
                <div className="flex gap-2">
                    <Button
                        variant={mode === 'text' ? 'default' : 'outline'}
                        onClick={() => handleModeChange('text')}
                        className="flex-1"
                    >
                        Text
                    </Button>
                    <Button
                        variant={mode === 'image' ? 'default' : 'outline'}
                        onClick={() => handleModeChange('image')}
                        className="flex-1"
                    >
                        Image {!isAuthenticated && '🔒'}
                    </Button>
                    <Button
                        variant={mode === 'video' ? 'default' : 'outline'}
                        onClick={() => handleModeChange('video')}
                        className="flex-1"
                    >
                        Video {!isAuthenticated && '🔒'}
                    </Button>
                </div>

                {/* Prompt Input */}
                <div className="space-y-2">
                    <Label htmlFor="prompt">Your Prompt</Label>
                    <Textarea
                        id="prompt"
                        placeholder="Describe what you want to generate..."
                        value={prompt}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                        rows={6}
                        className="resize-none"
                    />
                </div>

                {/* Text Mode Options */}
                {mode === 'text' && (
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="tone">Tone</Label>
                            <Select value={tone} onValueChange={setTone}>
                                <SelectTrigger id="tone">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="informative">Informative</SelectItem>
                                    <SelectItem value="casual">Casual</SelectItem>
                                    <SelectItem value="professional">Professional</SelectItem>
                                    <SelectItem value="friendly">Friendly</SelectItem>
                                    <SelectItem value="formal">Formal</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="length">Length</Label>
                            <Select value={length} onValueChange={setLength}>
                                <SelectTrigger id="length">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="short">Short</SelectItem>
                                    <SelectItem value="medium">Medium</SelectItem>
                                    <SelectItem value="long">Long</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                )}

                {/* Generate Button */}
                <Button
                    onClick={handleGenerate}
                    disabled={isLoading || !prompt.trim() || hasReachedLimit}
                    className="w-full"
                    size="lg"
                >
                    {isLoading ? 'Generating...' : 'Generate Content'}
                </Button>

                {/* Usage Counter for Anonymous Users */}
                {!isAuthenticated && (
                    <div className="text-center space-y-2">
                        {hasReachedLimit ? (
                            <div className="space-y-2">
                                <p className="text-sm text-destructive font-medium">
                                    You've reached your free generation limit
                                </p>
                                <p className="text-sm text-muted-foreground">
                                    <Link href="/auth/sign-up" className="text-primary underline underline-offset-4">
                                        Sign up
                                    </Link>
                                    {' '}or{' '}
                                    <Link href="/auth/login" className="text-primary underline underline-offset-4">
                                        Sign in
                                    </Link>
                                    {' '}for unlimited access
                                </p>
                            </div>
                        ) : (
                            <p className="text-sm text-muted-foreground">
                                💡 {remainingGenerations}/5 free generations remaining •{' '}
                                <Link href="/auth/sign-up" className="text-primary underline underline-offset-4">
                                    Sign in for unlimited
                                </Link>
                            </p>
                        )}
                    </div>
                )}

                {/* Error Display */}
                {error && (
                    <div className="p-4 bg-destructive/10 text-destructive rounded-md text-sm">
                        {error}
                    </div>
                )}
            </Card>

            {/* Generated Content */}
            <GenerationResult content={generatedContent} isLoading={isLoading} />
        </div>
    )
}
