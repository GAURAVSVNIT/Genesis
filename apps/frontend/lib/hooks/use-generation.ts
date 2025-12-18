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
            const promptMessage = `Generate a ${request.tone} ${request.length} blog post about: ${request.prompt}`

            // Save prompt
            if (!isAuthenticated && guestId) {
                // Guest: Save to Redis
                await saveGuestMessage(guestId, {
                    role: 'user',
                    content: promptMessage,
                    timestamp: new Date().toISOString()
                })
            } else if (isAuthenticated) {
                // Authenticated: Save to Supabase
                const supabase = createClient()
                const { data: { user } } = await supabase.auth.getUser()
                if (user) {
                    await supabase.from('chats').insert({
                        user_id: user.id,
                        role: 'user',
                        content: promptMessage,
                        created_at: new Date().toISOString()
                    })
                }
            }

            const response = await generateBlog(request)
            setGeneratedContent(response.content)
            setMetrics(response)

            // Save response
            if (!isAuthenticated && guestId) {
                // Guest: Save to Redis
                await saveGuestMessage(guestId, {
                    role: 'assistant',
                    content: response.blog,
                    timestamp: new Date().toISOString()
                })
            } else if (isAuthenticated) {
                // Authenticated: Save to Supabase
                const supabase = createClient()
                const { data: { user } } = await supabase.auth.getUser()
                if (user) {
                    await supabase.from('chats').insert({
                        user_id: user.id,
                        role: 'assistant',
                        content: response.blog,
                        created_at: new Date().toISOString()
                    })
                }
            }

            // Increment usage for anonymous users
            if (!isAuthenticated) {
                incrementUsage()
                setRemainingGenerationsState(getRemainingGenerations())
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to generate content')
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
