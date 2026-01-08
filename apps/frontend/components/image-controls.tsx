'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { RefreshCw, ImagePlus, Trash2, Loader2, Image as ImageIcon } from 'lucide-react'
import { toast } from 'sonner'

interface ImageControlsProps {
    content: string
    currentImageUrl: string | null
    onImageUpdate: (url: string | null) => void
}

export function ImageControls({ content, currentImageUrl, onImageUpdate }: ImageControlsProps) {
    const [isGenerating, setIsGenerating] = useState(false)

    const handleAction = async (action: 'add' | 'regenerate' | 'remove') => {
        if (action === 'remove') {
            onImageUpdate(null)
            toast.success("Image removed")
            return
        }

        setIsGenerating(true)
        try {
            // Call the regenerate-image endpoint
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/content/regenerate-image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content
                }),
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to generate image')
            }

            const data = await response.json()
            if (data.image_url) {
                onImageUpdate(data.image_url)
                toast.success(action === 'add' ? "Image added" : "Image regenerated")
            } else {
                toast.warning("No image returned by the generator")
            }

        } catch (error) {
            console.error('Image operation failed:', error)
            toast.error("Failed to generate image", {
                description: error instanceof Error ? error.message : "Unknown error"
            })
        } finally {
            setIsGenerating(false)
        }
    }

    return (
        <div className="flex items-center gap-1 bg-secondary/30 rounded-lg p-1 border border-border/50">
            {/* Add Image - Only show if NO image exists */}
            {!currentImageUrl && (
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAction('add')}
                    disabled={isGenerating}
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-primary hover:bg-primary/10"
                    title="Add Image"
                >
                    {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <ImagePlus className="h-4 w-4" />}
                </Button>
            )}

            {/* Regenerate & Remove - Only show if image EXISTS */}
            {currentImageUrl && (
                <>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleAction('regenerate')}
                        disabled={isGenerating}
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-primary hover:bg-primary/10"
                        title="Regenerate Image"
                    >
                        {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    </Button>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleAction('remove')}
                        disabled={isGenerating}
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        title="Remove Image"
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </>
            )}
        </div>
    )
}
