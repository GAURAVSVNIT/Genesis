'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useGeneration } from '@/lib/hooks/use-generation'
import { cn } from '@/lib/utils'
import { User, Bot, Edit2, RefreshCw, Save, X } from 'lucide-react'
import ClientSideCustomEditor from './client-side-custom-editor'
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
    const [editingContent, setEditingContent] = useState('')
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

    const handleEdit = (msg: Message) => {
        setEditingId(msg.id)
        setEditingContent(msg.content)
    }

    const handleSaveEdit = (id: string) => {
        setMessages(prev => prev.map(m =>
            m.id === id ? { ...m, content: editingContent } : m
        ))
        setEditingId(null)
        setEditingContent('')
    }

    const handleCancelEdit = () => {
        setEditingId(null)
        setEditingContent('')
    }

    return (
        <div className="flex flex-col h-screen w-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            {/* Premium Header */}
            <div className="sticky top-0 z-20 border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl shadow-lg">
                <div className="max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
                    {/* Brand Section */}
                    <div className="flex items-center gap-4">
                        <div className="relative w-10 h-10">
                            <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl blur opacity-75"></div>
                            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                                <Bot className="w-6 h-6 text-white" />
                            </div>
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                                Genesis
                            </h1>
                            <p className="text-xs text-slate-400 font-medium">Advanced AI Content Generation</p>
                        </div>
                    </div>

                    {/* Controls Section */}
                    <div className="flex items-center gap-4">
                        <div className="flex gap-2 bg-slate-800/50 rounded-lg p-1.5 border border-slate-700/50">
                            <Select value={tone} onValueChange={setTone}>
                                <SelectTrigger className="w-[150px] bg-transparent border-0 text-sm text-white font-medium hover:bg-slate-700/30 focus:bg-slate-700/30">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-800 border-slate-700">
                                    <SelectItem value="informative"> Informative</SelectItem>
                                    <SelectItem value="casual"> Casual</SelectItem>
                                    <SelectItem value="professional">Professional</SelectItem>
                                    <SelectItem value="creative">Creative</SelectItem>
                                    <SelectItem value="humorous">Humorous</SelectItem>
                                </SelectContent>
                            </Select>
                            <div className="w-px bg-slate-700/50"></div>
                            <Select value={length} onValueChange={setLength}>
                                <SelectTrigger className="w-[130px] bg-transparent border-0 text-sm text-white font-medium hover:bg-slate-700/30 focus:bg-slate-700/30">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-800 border-slate-700">
                                    <SelectItem value="short">📝 Short</SelectItem>
                                    <SelectItem value="medium">📄 Medium</SelectItem>
                                    <SelectItem value="long">📚 Long</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Messages Area - Professional Layout */}
            <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full w-full">
                    <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
                        {messages.length === 0 && (
                            <div className="text-center py-32 space-y-8">
                                <div className="flex justify-center">
                                    <div className="relative">
                                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full blur-2xl"></div>
                                        <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-slate-700/50 flex items-center justify-center">
                                            <Bot className="w-10 h-10 text-blue-400" />
                                        </div>
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <h3 className="text-2xl font-bold text-white">Welcome to Genesis</h3>
                                    <p className="text-slate-400 max-w-md mx-auto leading-relaxed">
                                        Powered by advanced AI agents, ready to generate professional content tailored to your needs.
                                    </p>
                                    <div className="pt-4 grid grid-cols-3 gap-4 max-w-md mx-auto">
                                        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                                            <p className="text-xs text-slate-400">Tone</p>
                                            <p className="text-sm font-semibold text-white capitalize">{tone}</p>
                                        </div>
                                        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                                            <p className="text-xs text-slate-400">Length</p>
                                            <p className="text-sm font-semibold text-white capitalize">{length}</p>
                                        </div>
                                        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
                                            <p className="text-xs text-slate-400">Status</p>
                                            <p className="text-sm font-semibold text-green-400">Ready</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={cn(
                                    "flex gap-4 group animate-in fade-in-50 slide-in-from-bottom-3 duration-300",
                                    msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                                )}
                            >
                                {msg.role === 'assistant' && (
                                    <Avatar className="w-9 h-9 mt-1 flex-shrink-0 border border-slate-700/50">
                                        <div className="w-full h-full rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                                            <Bot className="w-5 h-5 text-white" />
                                        </div>
                                    </Avatar>
                                )}

                                <div className={cn(
                                    "flex flex-col gap-2 max-w-2xl",
                                    msg.role === 'user' && "items-end"
                                )}>
                                    <div className={cn(
                                        "px-4 py-3 rounded-2xl transition-all duration-200",
                                        msg.role === 'user'
                                            ? "bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-none shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30"
                                            : "bg-slate-800 text-slate-100 rounded-bl-none border border-slate-700/50 hover:border-slate-700 hover:bg-slate-800/80"
                                    )}>
                                        <div className="prose prose-invert max-w-none prose-p:m-0 prose-p:leading-relaxed text-sm leading-relaxed break-words">
                                            {editingId === msg.id ? (
                                                <div className="space-y-4">
                                                    <div className="bg-white rounded-lg overflow-hidden">
                                                        <ClientSideCustomEditor
                                                            initialData={editingContent}
                                                            onChange={setEditingContent}
                                                        />
                                                    </div>
                                                    <div className="flex gap-2 justify-end">
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            onClick={handleCancelEdit}
                                                            className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            onClick={() => handleSaveEdit(msg.id)}
                                                            className="h-8 px-3 bg-green-600 hover:bg-green-700 text-white"
                                                        >
                                                            <Save className="w-4 h-4 mr-2" />
                                                            Save
                                                        </Button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <>
                                                    {msg.content.includes('<') ? (
                                                        <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                                                    ) : (
                                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 px-2 text-xs text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                        {msg.role === 'assistant' && (
                                            <span className="flex items-center gap-1">
                                                <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                                                AI Generated
                                            </span>
                                        )}
                                        <span>{new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                                        {msg.role === 'assistant' && editingId !== msg.id && (
                                            <button
                                                onClick={() => handleEdit(msg)}
                                                className="ml-2 p-1 hover:bg-slate-700 rounded transition-colors text-slate-400 hover:text-blue-400"
                                                title="Edit with CKEditor"
                                            >
                                                <Edit2 className="w-3.5 h-3.5" />
                                            </button>
                                        )}
                                    </div>
                                </div>

                                {msg.role === 'user' && (
                                    <Avatar className="w-9 h-9 mt-1 flex-shrink-0 bg-slate-700 border border-slate-600">
                                        <div className="w-full h-full rounded-full bg-slate-700 flex items-center justify-center">
                                            <User className="w-5 h-5 text-slate-300" />
                                        </div>
                                    </Avatar>
                                )}
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex gap-4 group">
                                <Avatar className="w-9 h-9 mt-1 flex-shrink-0 border border-slate-700/50">
                                    <div className="w-full h-full rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center animate-pulse">
                                        <Bot className="w-5 h-5 text-white" />
                                    </div>
                                </Avatar>
                                <div className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-slate-800 border border-slate-700/50">
                                    <div className="flex gap-1.5">
                                        <div className="w-2.5 h-2.5 bg-slate-400/40 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                        <div className="w-2.5 h-2.5 bg-slate-400/40 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                        <div className="w-2.5 h-2.5 bg-slate-400/40 rounded-full animate-bounce"></div>
                                    </div>
                                    <span className="text-xs text-slate-400 ml-1">Generating response...</span>
                                </div>
                            </div>
                        )}
                        <div ref={scrollRef} />
                    </div>
                </ScrollArea>
            </div>

            {/* Premium Input Footer */}
            <div className="sticky bottom-0 border-t border-slate-800/50 bg-slate-900/80 backdrop-blur-xl shadow-2xl">
                <div className="max-w-4xl mx-auto px-6 py-6 space-y-4">
                    {/* Error Display */}
                    {error && (
                        <div className="p-4 bg-red-900/20 border border-red-700/30 rounded-lg text-red-200 text-sm flex items-start gap-3 animate-in fade-in-50 duration-300">
                            <span className="text-lg flex-shrink-0 mt-0.5">⚠️</span>
                            <div>
                                <p className="font-medium">Error occurred</p>
                                <p className="text-red-300/80 text-xs mt-1">{error}</p>
                            </div>
                        </div>
                    )}

                    {/* Input Box */}
                    <div className="relative group">
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 to-cyan-500/0 group-focus-within:from-blue-500/10 group-focus-within:to-cyan-500/10 rounded-2xl blur transition-all duration-300"></div>
                        <div className="relative flex gap-3 items-end bg-slate-800/50 border border-slate-700/50 group-focus-within:border-slate-700 rounded-2xl px-4 py-3 transition-all duration-300 hover:bg-slate-800/60">
                            <Textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Describe your content idea here. What would you like to create?"
                                className="flex-1 resize-none max-h-24 bg-transparent border-0 text-white placeholder-slate-500 focus:outline-none focus:ring-0 text-sm leading-relaxed"
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
                                className="flex-shrink-0 rounded-lg bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 disabled:from-slate-700 disabled:to-slate-700 text-white font-medium text-sm shadow-lg hover:shadow-blue-500/50 transition-all duration-200 px-4 py-2"
                                size="sm"
                            >
                                {isLoading ? (
                                    <div className="flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                                        Generating
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-2">
                                        <span>→</span>
                                        Send
                                    </div>
                                )}
                            </Button>
                        </div>
                    </div>

                    {/* Helper Text */}
                    <div className="flex items-center justify-between text-xs text-slate-400 px-2">
                        <div className="flex items-center gap-3">
                            <span className="flex items-center gap-1">
                                <span className="text-slate-600">⌨️</span>
                                Press <span className="font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">Enter</span> to send
                            </span>
                            <span className="text-slate-600">•</span>
                            <span className="flex items-center gap-1">
                                <span className="text-slate-600">⇧</span>
                                <span className="font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">Shift+Enter</span> for new line
                            </span>
                        </div>
                        {messages.length > 0 && (
                            <span className="flex items-center gap-2 text-blue-400/70 font-medium">
                                <div className="w-1.5 h-1.5 rounded-full bg-green-500/60"></div>
                                {messages.length} messages in conversation
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
