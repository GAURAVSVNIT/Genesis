'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Card } from '@/components/ui/card'

interface ChatMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    created_at: string
}

export function HistoryList({ isAuthenticated }: { isAuthenticated: boolean }) {
    const [history, setHistory] = useState<ChatMessage[]>([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (!isAuthenticated) {
            setHistory([])
            return
        }

        const fetchHistory = async () => {
            setLoading(true)
            const supabase = createClient()

            const { data, error } = await supabase
                .from('chats')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(50)

            if (error) {
                console.error('Error fetching history:', error)
            } else if (data) {
                setHistory(data)
            }
            setLoading(false)
        }

        fetchHistory()
    }, [isAuthenticated])

    if (!isAuthenticated || history.length === 0) return null

    return (
        <div className="w-full max-w-4xl mx-auto space-y-4 mt-8">
            <h2 className="text-2xl font-bold px-1">Your History</h2>
            <div className="space-y-4">
                {history.map((msg) => (
                    <Card key={msg.id} className={`p-4 ${msg.role === 'assistant'
                        ? 'bg-muted/50 border-l-4 border-l-primary'
                        : 'bg-background border-l-4 border-l-muted-foreground'
                        }`}>
                        <div className="flex justify-between items-start mb-2">
                            <span className="font-semibold text-sm uppercase text-muted-foreground">
                                {msg.role}
                            </span>
                            <span className="text-xs text-muted-foreground">
                                {new Date(msg.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <div className="prose dark:prose-invert max-w-none text-sm whitespace-pre-wrap">
                            {msg.content}
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    )
}
