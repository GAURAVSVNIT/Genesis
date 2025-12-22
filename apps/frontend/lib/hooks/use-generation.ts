import { useState, useEffect } from 'react'
import { generateBlog, type BlogRequest, type BlogResponse } from '@/lib/api/blog'
import { incrementUsage, hasReachedLimit, getRemainingGenerations } from '@/lib/api/usage'
import { saveGuestMessage } from '@/lib/api/guest'
import { createClient } from '@/lib/supabase/client'

export function useGeneration(isAuthenticated: boolean) {
    const [isLoading, setIsLoading] = useState(false)
    const [generatedContent, setGeneratedContent] = useState<string | null>(null)
    const [metrics, setMetrics] = useState<Partial<BlogResponse> | undefined>()
    const [error, setError] = useState<string | null>(null)
    const [remainingGenerations, setRemainingGenerationsState] = useState(5) // Default value to avoid hydration mismatch
    const [guestId, setGuestId] = useState<string | null>(null)

    useEffect(() => {
        // Update remaining generations after hydration
        setRemainingGenerationsState(getRemainingGenerations())
        
        if (!isAuthenticated) {
            let id = localStorage.getItem('guestId')
            if (!id) {
                id = crypto.randomUUID()
                localStorage.setItem('guestId', id)
            }
            setGuestId(id)
        }
    }, [isAuthenticated])

    const generate = async (request: BlogRequest) => {
        // Check usage limit for anonymous users
        if (!isAuthenticated && hasReachedLimit()) {
            setError('You\'ve reached your free generation limit. Please sign in to continue.')
            return
        }

        setIsLoading(true)
        setError(null)

        try {
            console.log('[DEBUG] Starting blog generation with request:', request)
            const promptMessage = `Generate a ${request.tone} ${request.length} blog post about: ${request.prompt}`

            // Note: The backend /v1/content/generate already saves all conversations and messages
            // to both conversation_cache and message_cache tables. No need for separate frontend calls.

            console.log('[DEBUG] Calling generateBlog API...')
            // Inject guestId if not authenticated
            const requestWithGuestId = {
                ...request,
                guestId: !isAuthenticated ? guestId : undefined
            }
            const response = await generateBlog(requestWithGuestId)
            console.log('[DEBUG] Received response:', response)
            setGeneratedContent(response.content)
            setMetrics(response)

            // Note: Backend handles all persistence (conversation_cache + message_cache)

            // Increment usage for anonymous users
            if (!isAuthenticated) {
                incrementUsage()
                setRemainingGenerationsState(getRemainingGenerations())
            }
            
            return response.content
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate content')
            return null
        } finally {
            setIsLoading(false)
        }
    }

    return {
        generate,
        isLoading,
        generatedContent,
        metrics,
        error,
        remainingGenerations,
        hasReachedLimit: !isAuthenticated && hasReachedLimit(),
    }
}
