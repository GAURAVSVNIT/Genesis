'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { getGuestId } from '@/lib/utils/migration'

interface Conversation {
    id: string
    title: string
    message_count: number
    platform: string
    created_at: string
    messages: ChatMessage[]
}

interface ChatMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    created_at: string
    seo_score?: number
    uniqueness_score?: number
    engagement_score?: number
    cost_usd?: number
}

export function HistoryList({ isAuthenticated }: { isAuthenticated: boolean }) {
    const [conversations, setConversations] = useState<Conversation[]>([])
    const [guestConversations, setGuestConversations] = useState<Conversation[]>([])
    const [loading, setLoading] = useState(false)
    const [selectedConversation, setSelectedConversation] = useState<string | null>(null)

    useEffect(() => {
        const fetchHistory = async () => {
            setLoading(true)
            try {
                if (isAuthenticated) {
                    // Fetch authenticated user conversations
                    const supabase = createClient()
                    const { data: { user } } = await supabase.auth.getUser()

                    if (user) {
                        const { data, error } = await supabase
                            .from('chats')
                            .select('*')
                            .eq('user_id', user.id)
                            .order('created_at', { ascending: false })
                            .limit(100)

                        if (error) {
                            console.error('Error fetching history:', error)
                        } else if (data) {
                            // Group messages by conversation (simple grouping by user messages)
                            const grouped = groupMessagesByConversation(data)
                            setConversations(grouped)
                        }
                    }
                } else {
                    // Fetch guest conversations from backend
                    const guestId = getGuestId()
                    if (guestId) {
                        const response = await fetch(`/v1/guest/chat/${guestId}`)
                        if (response.ok) {
                            const messages = await response.json()
                            const grouped = groupMessagesByConversation(messages)
                            setGuestConversations(grouped)
                        }
                    }
                }
            } catch (error) {
                console.error('Error fetching history:', error)
            } finally {
                setLoading(false)
            }
        }

        fetchHistory()
    }, [isAuthenticated])

    const groupMessagesByConversation = (messages: any[]): Conversation[] => {
        const convMap = new Map<string, Conversation>()
        let currentConvId = '1'
        let userMessageCount = 0

        messages.forEach((msg, index) => {
            if (msg.role === 'user') {
                currentConvId = msg.id
                userMessageCount = 0
            }

            if (!convMap.has(currentConvId)) {
                convMap.set(currentConvId, {
                    id: currentConvId,
                    title: msg.content.substring(0, 50) + (msg.content.length > 50 ? '...' : ''),
                    message_count: 0,
                    platform: msg.platform || 'api',
                    created_at: msg.created_at,
                    messages: []
                })
            }

            const conv = convMap.get(currentConvId)!
            conv.messages.push(msg)
            conv.message_count++
        })

        return Array.from(convMap.values()).sort(
            (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
    }

    const formatScore = (score: number | undefined) => {
        if (score === undefined) return 'N/A'
        return (score * 100).toFixed(1) + '%'
    }

    const activeConversations = isAuthenticated ? conversations : guestConversations

    if (loading) {
        return (
            <div className="w-full max-w-4xl mx-auto mt-8">
                <div className="text-center text-muted-foreground">Loading history...</div>
            </div>
        )
    }

    if (activeConversations.length === 0) return null

    return (
        <div className="w-full max-w-4xl mx-auto space-y-4 mt-8">
            <h2 className="text-2xl font-bold px-1">
                {isAuthenticated ? 'Your Conversations' : 'Guest Conversations'}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Conversation List */}
                <div className="md:col-span-1 space-y-2 max-h-96 overflow-y-auto">
                    {activeConversations.map((conv) => (
                        <Card
                            key={conv.id}
                            className={`p-3 cursor-pointer transition-colors ${
                                selectedConversation === conv.id
                                    ? 'bg-primary text-primary-foreground'
                                    : 'hover:bg-muted'
                            }`}
                            onClick={() => setSelectedConversation(conv.id)}
                        >
                            <h3 className="font-semibold text-sm truncate">{conv.title}</h3>
                            <p className="text-xs opacity-75">
                                {new Date(conv.created_at).toLocaleDateString()}
                            </p>
                            <div className="mt-1 flex gap-1">
                                <Badge variant="outline" className="text-xs">
                                    {conv.message_count} messages
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                    {conv.platform}
                                </Badge>
                            </div>
                        </Card>
                    ))}
                </div>

                {/* Conversation Details */}
                <div className="md:col-span-2">
                    {selectedConversation ? (
                        (() => {
                            const selected = activeConversations.find(c => c.id === selectedConversation)
                            return selected ? (
                                <Card className="p-6 space-y-4 max-h-96 overflow-y-auto">
                                    <div>
                                        <h3 className="font-bold text-lg mb-2">{selected.title}</h3>
                                        <div className="flex gap-2 mb-4">
                                            <Badge>{selected.platform}</Badge>
                                            <Badge variant="outline">
                                                {new Date(selected.created_at).toLocaleString()}
                                            </Badge>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {selected.messages.map((msg) => (
                                            <div
                                                key={msg.id}
                                                className={`p-3 rounded-lg ${
                                                    msg.role === 'assistant'
                                                        ? 'bg-muted/50 border-l-4 border-l-primary'
                                                        : 'bg-background border-l-4 border-l-muted-foreground'
                                                }`}
                                            >
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="font-semibold text-sm uppercase text-muted-foreground">
                                                        {msg.role}
                                                    </span>
                                                    <span className="text-xs text-muted-foreground">
                                                        {new Date(msg.created_at).toLocaleTimeString()}
                                                    </span>
                                                </div>
                                                <p className="text-sm whitespace-pre-wrap mb-2 line-clamp-3">
                                                    {msg.content}
                                                </p>

                                                {/* Quality Scores */}
                                                {msg.role === 'assistant' && (
                                                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/50">
                                                        {msg.seo_score !== undefined && (
                                                            <div className="text-xs">
                                                                <span className="text-muted-foreground">SEO:</span>{' '}
                                                                <span className="font-semibold">
                                                                    {formatScore(msg.seo_score)}
                                                                </span>
                                                            </div>
                                                        )}
                                                        {msg.uniqueness_score !== undefined && (
                                                            <div className="text-xs">
                                                                <span className="text-muted-foreground">Unique:</span>{' '}
                                                                <span className="font-semibold">
                                                                    {formatScore(msg.uniqueness_score)}
                                                                </span>
                                                            </div>
                                                        )}
                                                        {msg.engagement_score !== undefined && (
                                                            <div className="text-xs">
                                                                <span className="text-muted-foreground">Engage:</span>{' '}
                                                                <span className="font-semibold">
                                                                    {formatScore(msg.engagement_score)}
                                                                </span>
                                                            </div>
                                                        )}
                                                        {msg.cost_usd !== undefined && (
                                                            <div className="text-xs">
                                                                <span className="text-muted-foreground">Cost:</span>{' '}
                                                                <span className="font-semibold">
                                                                    ${msg.cost_usd.toFixed(5)}
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </Card>
                            ) : null
                        })()
                    ) : (
                        <Card className="p-6 text-center text-muted-foreground">
                            Select a conversation to view details
                        </Card>
                    )}
                </div>
            </div>
        </div>
    )
}
