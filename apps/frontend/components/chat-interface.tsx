'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useGeneration } from '@/lib/hooks/use-generation'
import { cn } from '@/lib/utils'
import { User, Bot, Edit2, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'

interface ChatInterfaceProps {
    isAuthenticated: boolean
}

type Message = {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    tone?: string
    length?: string
}

export function ChatInterface({ isAuthenticated }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [editingId, setEditingId] = useState<string | null>(null)
    const [tone, setTone] = useState('informative')
    const [length, setLength] = useState('medium')
    const scrollRef = useRef<HTMLDivElement>(null)

    const { generate, isLoading, error } = useGeneration(isAuthenticated)

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, isLoading])

    const handleSend = async () => {
        if (!input.trim() || isLoading) return

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: 'user',
            content: input,
            timestamp: new Date(),
            tone,
            length
        }

        setMessages(prev => [...prev, userMsg])
        setInput('')

        // If editing, remove messages after the edited one to "regenerate" from that point
        // For now, simpler approach: just append new interaction

        await processGeneration(userMsg)
    }

    const processGeneration = async (msg: Message) => {
        // Find the last assistant message to provide context
        const lastAssistantMsg = messages.filter(m => m.role === 'assistant').pop()

        let finalPrompt = msg.content
        if (lastAssistantMsg) {
            finalPrompt = `Context: ${lastAssistantMsg.content}\n\nRefinement Request: ${msg.content}`
        }

        const result = await generate({
            prompt: finalPrompt,
            tone: msg.tone || 'informative',
            length: msg.length || 'medium'
        })

        if (result) {
            const assistantMsg: Message = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: result,
                timestamp: new Date()
            }
            setMessages(prev => [...prev, assistantMsg])
        }
    }

    // Since useGeneration is designed for single-result state, we need to adapt it.
    // Ideally, useGeneration should return the result. 
    // Let's assume for a moment I will modify useGeneration or use api directly.
    // Actually, I'll modify useGeneration to return the data.

    return (
        <div className="flex flex-col h-[85vh] w-full max-w-4xl mx-auto border rounded-xl overflow-hidden bg-background shadow-sm">

            {/* Header */}
            <div className="p-4 border-b bg-muted/30 flex items-center justify-between">
                <div>
                    <h2 className="font-semibold text-lg flex items-center gap-2">
                        <Bot className="w-5 h-5 text-primary" />
                        AI Assistant
                    </h2>
                    <p className="text-xs text-muted-foreground">Modify requests and iterate on content</p>
                </div>
                <div className="flex gap-2">
                    <Select value={tone} onValueChange={setTone}>
                        <SelectTrigger className="w-[120px] h-8 text-xs">
                            <SelectValue placeholder="Tone" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="informative">Informative</SelectItem>
                            <SelectItem value="casual">Casual</SelectItem>
                            <SelectItem value="professional">Professional</SelectItem>
                        </SelectContent>
                    </Select>
                    <Select value={length} onValueChange={setLength}>
                        <SelectTrigger className="w-[100px] h-8 text-xs">
                            <SelectValue placeholder="Length" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="short">Short</SelectItem>
                            <SelectItem value="medium">Medium</SelectItem>
                            <SelectItem value="long">Long</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* Messages Area */}
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-6">
                    {messages.length === 0 && (
                        <div className="text-center text-muted-foreground py-20">
                            <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>Start a conversation to generate content.</p>
                        </div>
                    )}

                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={cn(
                                "flex gap-3",
                                msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                            )}
                        >
                            <Avatar className="w-8 h-8 mt-1">
                                <AvatarFallback className={msg.role === 'user' ? "bg-primary text-primary-foreground" : "bg-muted"}>
                                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                                </AvatarFallback>
                            </Avatar>

                            <div className={cn(
                                "group relative p-3 rounded-lg max-w-[80%] text-sm",
                                msg.role === 'user'
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted text-foreground"
                            )}>
                                {msg.role === 'user' && (
                                    <button
                                        onClick={() => {
                                            setInput(msg.content)
                                            setTone(msg.tone || 'informative')
                                            setLength(msg.length || 'medium')
                                            // Ideally we'd remove this and subsequent messages to restart from here
                                        }}
                                        className="absolute -left-8 top-1 p-1 opacity-0 group-hover:opacity-100 transition-opacity text-foreground"
                                        title="Edit"
                                        aria-label="Edit request"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                )}

                                <div className="prose prose-sm dark:prose-invert break-words">
                                    {msg.role === 'assistant' ? (
                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-3">
                            <Avatar className="w-8 h-8 mt-1">
                                <AvatarFallback className="bg-muted"><Bot className="w-4 h-4" /></AvatarFallback>
                            </Avatar>
                            <div className="bg-muted p-3 rounded-lg w-24">
                                <div className="flex gap-1 h-full items-center justify-center">
                                    <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                    <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce"></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            {/* Input Area */}
            <div className="p-4 bg-background border-t">
                <div className="relative">
                    <Textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your request here..."
                        className="resize-none pr-20 min-h-[80px]"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                handleSend()
                            }
                        }}
                    />
                    <Button
                        onClick={handleSend}
                        disabled={isLoading || !input.trim()}
                        className="absolute bottom-3 right-3"
                        size="sm"
                    >
                        Send
                    </Button>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="mt-2 p-2 bg-destructive/10 border border-destructive/30 rounded text-destructive text-sm">
                        ⚠️ {error}
                    </div>
                )}

                <div className="text-xs text-muted-foreground mt-2 text-right">
                    Press Enter to send, Shift+Enter for new line
                </div>
            </div>
        </div>
    )
}
