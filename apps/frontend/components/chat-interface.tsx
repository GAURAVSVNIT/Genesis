'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useGeneration } from '@/lib/hooks/use-generation'
import { classifyIntent } from '@/lib/api/classifier'
import { saveContext, loadContext, createCheckpoint, listCheckpoints, restoreCheckpoint, deleteCheckpoint } from '@/lib/api/context'
import { cn } from '@/lib/utils'
import { User, Bot, Edit2, RefreshCw, Save, X, PanelRight, Clock, BookmarkPlus, Trash2 } from 'lucide-react'
import ClientSideCustomEditor from './client-side-custom-editor'
import SidebarEditor from './sidebar-editor'
import ReactMarkdown from 'react-markdown'
import { toast } from "sonner" // Import toast
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
    type: 'chat' | 'blog' | 'modify' | 'rewrite' // chat: conversation, blog: new content, modify: enhance, rewrite: fresh start
    tone?: string
    length?: string
    image_url?: string
}

type BlogCheckpoint = {
    id: string
    blogMessageId: string
    content: string
    title: string
    createdAt: Date
    chatContextAtTime: Message[] // Chat messages at the time this checkpoint was created
}

export function ChatInterface({ isAuthenticated }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [tone, setTone] = useState('informative')
    const [length, setLength] = useState('medium')
    const [sidebarEditingId, setSidebarEditingId] = useState<string | null>(null)
    const [showEditorPanel, setShowEditorPanel] = useState(true)
    const [classifyingIntent, setClassifyingIntent] = useState(false)
    const [checkpoints, setCheckpoints] = useState<BlogCheckpoint[]>([])
    const [showCheckpoints, setShowCheckpoints] = useState(false)
    const [conversationId] = useState(() => crypto.randomUUID())
    const [userId] = useState(() => isAuthenticated ? 'user' : 'guest')
    const scrollRef = useRef<HTMLDivElement>(null)

    const { generate, isLoading, error } = useGeneration(isAuthenticated)

    // Load checkpoints when component mounts
    useEffect(() => {
        loadCheckpointsList()
    }, [conversationId, userId])

    // Auto-save context to backend whenever messages change
    useEffect(() => {
        if (messages.length === 0) return

        const saveContextToDB = async () => {
            try {
                const chatMessages = messages.filter(m => m.type === 'chat')
                // Find the latest content message (blog, modify, or rewrite)
                const blogMsg = messages
                    .slice()
                    .reverse()
                    .find(m => (m.type === 'blog' || m.type === 'modify' || m.type === 'rewrite') && m.role === 'assistant')

                await saveContext({
                    conversation_id: conversationId,
                    user_id: userId,
                    messages: messages.map(m => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        type: m.type,
                        timestamp: m.timestamp.toISOString(),
                        tone: m.tone,
                        length: m.length
                    })),
                    chat_messages: chatMessages.map(m => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        type: m.type,
                        timestamp: m.timestamp.toISOString(),
                        tone: m.tone,
                        length: m.length
                    })),
                    current_blog_content: blogMsg?.content
                })
            } catch (error) {
                console.error('Error saving context:', error)
                // Fail silently - context saving is not critical
            }
        }

        // Debounce context saving to every 2 seconds
        const timer = setTimeout(saveContextToDB, 2000)
        return () => clearTimeout(timer)
    }, [messages, conversationId, userId])

    // Get context summary for classifier
    const getContextSummary = (): string => {
        const chatMessages = messages.filter(m => m.type === 'chat')
        return chatMessages
            .slice(-4) // Last 4 chat messages for context
            .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`)
            .join('\n')
    }

    // Classify intent using backend classifier
    const classifyPromptType = async (text: string): Promise<'blog' | 'chat' | 'modify' | 'rewrite'> => {
        try {
            setClassifyingIntent(true)
            const contextSummary = getContextSummary()

            const result = await classifyIntent({
                prompt: text,
                context_summary: contextSummary || undefined
            })

            console.log('[DEBUG] Classification result:', result)
            return result.intent
        } catch (error) {
            console.error('Classification failed, falling back to frontend detection:', error)
            // Fallback to keyword-based if API fails
            return fallbackClassifyPromptType(text)
        } finally {
            setClassifyingIntent(false)
        }
    }

    // Fallback keyword-based classification for when API fails
    const fallbackClassifyPromptType = (text: string): 'blog' | 'chat' | 'modify' | 'rewrite' => {
        const lowerText = text.toLowerCase()

        // Check for rewrite keywords FIRST (highest priority)
        const rewriteKeywords = ['rewrite', 'restart', 'start over', 'from scratch', 'completely new', 'fresh', 'different angle']
        if (rewriteKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'rewrite'
        }

        // Check if there's an existing blog to modify
        const existingBlog = messages.find(m => m.type === 'blog' && m.role === 'assistant')

        // Check for modify keywords
        const modifyKeywords = ['improve', 'enhance', 'better', 'add', 'more', 'expand', 'polish', 'refine', 'strengthen', 'update', 'modify', 'edit']
        if (existingBlog && modifyKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'modify'
        }

        // Check for blog creation keywords
        const blogKeywords = [
            'write', 'create', 'generate', 'draft', 'compose', 'blog', 'article', 'post',
            'content', 'story', 'guide', 'email', 'copy', 'description'
        ]
        if (blogKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'blog'
        }

        // Default to chat
        return 'chat'
    }

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, isLoading])

    // Auto-select the latest blog/modify/rewrite message when it's added
    useEffect(() => {
        const lastContentMsg = messages
            .filter(m => (m.type === 'blog' || m.type === 'modify' || m.type === 'rewrite') && m.role === 'assistant')
            .pop()
        if (lastContentMsg && lastContentMsg.id !== sidebarEditingId) {
            setSidebarEditingId(lastContentMsg.id)
        }
    }, [messages])



    const handleSend = async () => {
        if (!input.trim() || isLoading || classifyingIntent) return

        // Classify using backend classifier
        const messageType = await classifyPromptType(input)

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: 'user',
            content: input,
            timestamp: new Date(),
            type: messageType,
            tone,
            length
        }

        const updatedMessages = [...messages, userMsg]
        setMessages(updatedMessages)
        setInput('')

        await processGeneration(userMsg, updatedMessages)
    }

    const processGeneration = async (msg: Message, allMessages: Message[]) => {
        // Build complete conversation history (all messages for full context)
        const fullHistory = allMessages
            .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`)
            .join('\n\n')

        // Get conversation context - all chat messages for context
        const chatContext = allMessages.filter(m => m.type === 'chat')
        const contextSummary = chatContext
            .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`)
            .join('\n')

        // Get current blog content for modification context - use LATEST content
        const currentBlogMsg = allMessages
            .slice()
            .reverse()
            .find(m => (m.type === 'blog' || m.type === 'modify' || m.type === 'rewrite') && m.role === 'assistant')
        const blogContext = currentBlogMsg ? `Current content:\n${currentBlogMsg.content}` : ''

        // Get the actual action type from classifier (blog, modify, or rewrite)
        let actionType = msg.type
        if (msg.type === 'blog' || msg.type === 'modify' || msg.type === 'rewrite') {
            // msg.type already contains the correct action
            actionType = msg.type
        }

        let finalPrompt = msg.content

        if (actionType === 'chat') {
            // Chat mode: include full conversation history so AI remembers context
            if (fullHistory) {
                finalPrompt = `Previous conversation:\n${fullHistory}\n\nAnswer the user's question while remembering the full conversation context above.`
            } else {
                finalPrompt = msg.content
            }
        } else if (actionType === 'blog') {
            // Blog mode: new content creation
            finalPrompt = msg.content
        } else if (actionType === 'modify') {
            // Modify mode: include current blog context
            if (blogContext) {
                finalPrompt = `${blogContext}\n\nUser request: ${msg.content}`
            } else {
                finalPrompt = msg.content
            }
        } else if (actionType === 'rewrite') {
            // Rewrite mode: ignore current blog, start fresh
            // But keep conversation context
            if (contextSummary) {
                finalPrompt = `Based on this conversation:\n${contextSummary}\n\nUser request: ${msg.content.replace(/rewrite|restart|start over|from scratch|completely new/gi, '').trim() || 'Create a blog'}`
            } else {
                finalPrompt = msg.content
            }
        }

        const result = await generate({
            prompt: finalPrompt,
            tone: msg.tone || 'informative',
            length: msg.length || 'medium'
        })



        if (result) {
            // Check for missing image in blog response and notify user
            if ((msg.type === 'blog' || msg.type === 'modify' || msg.type === 'rewrite') && !result.image_url) {
                toast.warning("Image not generated", {
                    description: "The blog post was created, but we couldn't generate a header image at this time.",
                    duration: 5000,
                })
            }

            const assistantMsg: Message = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: result.content,
                image_url: result.image_url,
                timestamp: new Date(),
                type: msg.type
            }

            setMessages(prev => {
                const newMessages = [...prev, assistantMsg]
                // Auto-select blog, modify, and rewrite messages for editor
                if (msg.type === 'blog' || msg.type === 'modify' || msg.type === 'rewrite') {
                    // Trigger toast here if possible. 
                    // Since I cannot easily add new UI dependencies blindly, 
                    // I will check if 'sonner' or 'react-hot-toast' is in use in the project.
                    // Previous files showed 'components/ui/...' so maybe 'use-toast'?
                    // I will look for 'components/ui/use-toast.ts' in a separate step or just assume console for now.

                    setTimeout(() => {
                        setSidebarEditingId(assistantMsg.id)
                        setShowCheckpoints(false)  // Close checkpoints panel if open
                        setShowEditorPanel(true)   // Ensure editor panel is visible
                    }, 0)
                }
                return newMessages
            })
        }
    }

    const handleEdit = (msg: Message) => {
        setSidebarEditingId(msg.id)
    }

    const handleSaveEdit = async (content: string) => {
        if (sidebarEditingId) {
            setMessages(prev => prev.map(m =>
                m.id === sidebarEditingId ? { ...m, content } : m
            ))
            setSidebarEditingId(null)
        }
    }

    const handleCloseSidebar = () => {
        setSidebarEditingId(null)
    }

    // Create blog checkpoint
    const handleCreateCheckpoint = async () => {
        const blogMsg = messages.find(m => (m.type === 'blog' || m.type === 'modify' || m.type === 'rewrite') && m.role === 'assistant')
        if (!blogMsg) {
            alert('No blog content to checkpoint')
            return
        }

        try {
            const title = `Blog Version ${checkpoints.length + 1}`
            const chatContext = messages
                .filter(m => m.type === 'chat')
                .map(m => ({ id: m.id, role: m.role, content: m.content, timestamp: m.timestamp.toISOString(), tone: m.tone, length: m.length }))

            await createCheckpoint({
                conversation_id: conversationId,
                user_id: userId,
                title,
                content: blogMsg.content,
                description: `Saved at ${new Date().toLocaleString()}`,
                tone: tone,
                length: length,
                context_snapshot: {
                    chatContext,
                    timestamp: new Date().toISOString(),
                    tone: tone,
                    length: length
                }
            })

            // Refresh checkpoints list
            loadCheckpointsList()
            alert('Checkpoint created successfully!')
        } catch (error) {
            console.error('Error creating checkpoint:', error)
            alert('Failed to create checkpoint')
        }
    }

    // Load checkpoints list
    const loadCheckpointsList = async () => {
        try {
            const checkpointsList = await listCheckpoints(conversationId, userId)
            setCheckpoints(checkpointsList as any[])
        } catch (error) {
            console.error('Error loading checkpoints:', error)
        }
    }

    // Restore checkpoint with full context
    const handleRestoreCheckpoint = async (checkpointId: string) => {
        try {
            const restored = await restoreCheckpoint(checkpointId, userId, conversationId)

            // Update editor with restored content
            setSidebarEditingId(null)

            // Restore context snapshot if available
            let restoredMessages: Message[] = []

            if (restored.context_snapshot && restored.context_snapshot.chatContext) {
                // Reconstruct messages from context snapshot
                const contextChat = (restored.context_snapshot.chatContext as any[])
                const restoredChatMessages = contextChat.map((msg: any) => ({
                    id: msg.id || crypto.randomUUID(),
                    role: msg.role as 'user' | 'assistant',
                    content: msg.content,
                    timestamp: new Date(msg.timestamp),
                    type: 'chat' as const,
                    tone: msg.tone,
                    length: msg.length
                }))

                restoredMessages = restoredMessages.concat(restoredChatMessages)
            }

            // Create a message with restored blog content
            const restoredMsg: Message = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: restored.content,
                timestamp: new Date(),
                type: 'blog',
                tone: restored.tone || tone,
                length: restored.length || length
            }

            restoredMessages.push(restoredMsg)
            setMessages(restoredMessages)

            setSidebarEditingId(restoredMsg.id)
            setShowCheckpoints(false)

            // Update tone and length from checkpoint if available
            if (restored.tone) setTone(restored.tone)
            if (restored.length) setLength(restored.length)

            alert(`Restored checkpoint: ${restored.title}\n\nContext has been restored with full conversation history.`)
        } catch (error) {
            console.error('Error restoring checkpoint:', error)
            alert('Failed to restore checkpoint')
        }
    }

    // Delete checkpoint
    const handleDeleteCheckpoint = async (checkpointId: string) => {
        if (!confirm('Delete this checkpoint?')) return

        try {
            await deleteCheckpoint(checkpointId, userId)
            setCheckpoints(prev => prev.filter((cp: any) => cp.id !== checkpointId))
            alert('Checkpoint deleted')
        } catch (error) {
            console.error('Error deleting checkpoint:', error)
            alert('Failed to delete checkpoint')
        }
    }

    const currentEditingMessage = messages.find(m =>
        m.id === sidebarEditingId && (m.type === 'blog' || m.type === 'modify' || m.type === 'rewrite') && m.role === 'assistant'
    )

    return (
        <div className="flex h-screen w-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
            {/* Main Chat Area */}
            <div className={cn(
                "flex flex-col flex-1 transition-all duration-300",
                showEditorPanel ? "w-1/2" : "w-full"
            )}>
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
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowCheckpoints(!showCheckpoints)}
                                className={cn(
                                    "text-slate-300 hover:text-white hover:bg-slate-700/50",
                                    showCheckpoints && "bg-slate-700/50 text-white"
                                )}
                                title="View checkpoints"
                            >
                                <Clock className="w-4 h-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleCreateCheckpoint}
                                disabled={!(messages.find(m => (m.type === 'blog' || m.type === 'modify' || m.type === 'rewrite') && m.role === 'assistant') || (showEditorPanel && sidebarEditingId && (() => { const msg = messages.find(m => m.id === sidebarEditingId); return msg && (msg.type === 'blog' || msg.type === 'modify' || msg.type === 'rewrite'); })()))}
                                className="text-slate-300 hover:text-white hover:bg-slate-700/50 disabled:opacity-50"
                                title="Create checkpoint"
                            >
                                <BookmarkPlus className="w-4 h-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowEditorPanel(!showEditorPanel)}
                                className={cn(
                                    "text-slate-300 hover:text-white hover:bg-slate-700/50",
                                    showEditorPanel && "bg-slate-700/50 text-white"
                                )}
                                title={showEditorPanel ? "Hide editor" : "Show editor"}
                            >
                                <PanelRight className="w-4 h-4" />
                            </Button>
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

                            {messages
                                .filter(msg => !(msg.role === 'assistant' && (msg.type === 'blog' || msg.type === 'modify' || msg.type === 'rewrite')))
                                .map((msg) => (
                                    <div
                                        key={msg.id}
                                        className={cn(
                                            "flex gap-4 group animate-in fade-in-50 slide-in-from-bottom-3 duration-300",
                                            msg.role === 'user' && "flex-row-reverse"
                                        )}
                                    >
                                        <div className={cn(
                                            "flex flex-col gap-2 max-w-2xl",
                                            msg.role === 'user' ? "items-end" : "items-start"
                                        )}>
                                            <div className={cn(
                                                "px-4 py-3 rounded-2xl transition-all duration-200",
                                                msg.role === 'user'
                                                    ? "bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-br-none shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30"
                                                    : "bg-slate-800 text-slate-100 rounded-bl-none border border-slate-700/50 hover:border-slate-700"
                                            )}>
                                                <div className="prose prose-invert max-w-none prose-p:m-0 prose-p:leading-relaxed text-sm leading-relaxed break-words">
                                                    {msg.content.includes('<') ? (
                                                        <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                                                    ) : (
                                                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                    )}
                                                    {msg.image_url && (
                                                        <div className="mt-4 rounded-xl overflow-hidden border border-slate-700/50">
                                                            <img
                                                                src={msg.image_url}
                                                                alt="Generated visual"
                                                                className="w-full h-auto object-cover max-h-[400px]"
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 px-2 text-xs text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <span>{new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>

                                        <Avatar className={cn(
                                            "w-9 h-9 mt-1 flex-shrink-0 border",
                                            msg.role === 'user'
                                                ? "bg-slate-700 border-slate-600"
                                                : "bg-gradient-to-br from-blue-500 to-cyan-500 border-blue-400/50"
                                        )}>
                                            <div className={cn(
                                                "w-full h-full rounded-full flex items-center justify-center",
                                                msg.role === 'user'
                                                    ? "bg-slate-700"
                                                    : "bg-gradient-to-br from-blue-500 to-cyan-500"
                                            )}>
                                                {msg.role === 'user' ? (
                                                    <User className="w-5 h-5 text-slate-300" />
                                                ) : (
                                                    <Bot className="w-5 h-5 text-white" />
                                                )}
                                            </div>
                                        </Avatar>
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
                                    placeholder="Ask anything about your blog, get writing tips, or request content creation..."
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
                                    disabled={isLoading || !input.trim() || classifyingIntent}
                                    className="flex-shrink-0 rounded-lg bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 disabled:from-slate-700 disabled:to-slate-700 text-white font-medium text-sm shadow-lg hover:shadow-blue-500/50 transition-all duration-200 px-4 py-2"
                                    size="sm"
                                >
                                    {isLoading ? (
                                        <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                                            Generating
                                        </div>
                                    ) : classifyingIntent ? (
                                        <div className="flex items-center gap-2">
                                            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                                            Analyzing
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
                                <span className="text-slate-600">•</span>
                                <span className="text-slate-500">AI auto-detects intent (chat vs content)</span>
                            </div>
                            {messages.length > 0 && (
                                <span className="flex items-center gap-2 text-blue-400/70 font-medium">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-500/60"></div>
                                    {messages.filter(m => m.type === 'chat').length} chat | {messages.filter(m => m.type === 'blog').length} content
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Sidebar - Editor or Checkpoints */}
            {showEditorPanel && (
                <div className="w-1/2 border-l border-slate-800/50 bg-slate-900/50 flex flex-col">
                    {showCheckpoints ? (
                        // Checkpoints Panel
                        <div className="flex flex-col h-full">
                            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-800/50">
                                <h3 className="font-semibold text-lg text-white flex items-center gap-2">
                                    <Clock className="w-5 h-5" />
                                    Checkpoints
                                </h3>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setShowCheckpoints(false)}
                                    className="h-8 w-8 p-0"
                                >
                                    <X className="w-4 h-4" />
                                </Button>
                            </div>
                            <ScrollArea className="flex-1">
                                <div className="p-4 space-y-2">
                                    {checkpoints.length === 0 ? (
                                        <p className="text-slate-400 text-sm text-center py-8">No checkpoints yet. Create one to save your progress.</p>
                                    ) : (
                                        checkpoints.map((cp: any) => (
                                            <div
                                                key={cp.id}
                                                className="p-3 rounded-lg bg-slate-800 border border-slate-700 hover:border-slate-600 transition-all group"
                                            >
                                                <div className="flex items-start justify-between gap-2">
                                                    <div className="flex-1 min-w-0">
                                                        <p className="font-medium text-white text-sm truncate">{cp.title}</p>
                                                        <p className="text-xs text-slate-400">v{cp.version_number} • {new Date(cp.created_at).toLocaleDateString()}</p>
                                                        {cp.description && (
                                                            <p className="text-xs text-slate-500 mt-1 line-clamp-2">{cp.description}</p>
                                                        )}
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        {!cp.is_active && (
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => handleRestoreCheckpoint(cp.id)}
                                                                className="h-7 w-7 p-0 text-blue-400 hover:text-blue-300 hover:bg-blue-950"
                                                                title="Restore this version"
                                                            >
                                                                <RefreshCw className="w-3 h-3" />
                                                            </Button>
                                                        )}
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => handleDeleteCheckpoint(cp.id)}
                                                            className="h-7 w-7 p-0 text-red-400 hover:text-red-300 hover:bg-red-950"
                                                            title="Delete checkpoint"
                                                        >
                                                            <Trash2 className="w-3 h-3" />
                                                        </Button>
                                                    </div>
                                                </div>
                                                {cp.is_active && (
                                                    <div className="mt-2 text-xs font-medium text-green-400">✓ Active</div>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            </ScrollArea>
                        </div>
                    ) : currentEditingMessage ? (
                        // Editor Panel
                        <SidebarEditor
                            initialData={currentEditingMessage.content}
                            onSave={handleSaveEdit}
                            onClose={handleCloseSidebar}
                            title={`Blog Editor - ${new Date(currentEditingMessage.timestamp).toLocaleString()}`}
                            userId={userId}
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full space-y-4 text-slate-400">
                            <PanelRight className="w-12 h-12 opacity-50" />
                            <p className="text-center max-w-xs">Request content creation or use words like "write", "create", "generate" to populate the editor</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
