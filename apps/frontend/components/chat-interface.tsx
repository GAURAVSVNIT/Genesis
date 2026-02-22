'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useGeneration } from '@/lib/hooks/use-generation'
import { classifyIntent, IntentClassificationResponse } from '@/lib/api/classifier'
import { saveContext, loadContext, createCheckpoint, listCheckpoints, restoreCheckpoint, deleteCheckpoint } from '@/lib/api/context'
import { cn } from '@/lib/utils'
import { User, Bot, Edit2, RefreshCw, Save, PanelRight, Clock, BookmarkPlus, Trash2, X } from 'lucide-react'
import ClientSideCustomEditor from './client-side-custom-editor'
import SidebarEditor from './sidebar-editor'
import { VoiceInput } from '@/components/ui/voice-input'
import ReactMarkdown from 'react-markdown'
import { toast } from "sonner" // Import toast
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { LogoutButton } from '@/components/logout-button'
import type { User as SupabaseUser } from '@supabase/supabase-js'
import { Settings as SettingsIcon } from 'lucide-react'
import { SettingsModal } from '@/components/settings/SettingsModal'

interface ChatInterfaceProps {
    isAuthenticated: boolean
}

type Message = {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    type: 'chat' | 'blog' | 'edit' | 'rewrite' | 'image' // Expanded intents
    tone?: string
    length?: string
    image_url?: string
    topic?: string
    refined_query?: string
}

type BlogCheckpoint = {
    id: string
    blogMessageId: string
    content: string
    title: string
    createdAt: Date
    chatContextAtTime: Message[]
}

export function ChatInterface({ isAuthenticated }: ChatInterfaceProps) {
    const [user, setUser] = useState<SupabaseUser | null>(null)
    const [isSettingsOpen, setIsSettingsOpen] = useState(false)
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [tone, setTone] = useState('informative')
    const [length, setLength] = useState('medium')
    const [sidebarEditingId, setSidebarEditingId] = useState<string | null>(null)
    const [showEditorPanel, setShowEditorPanel] = useState(false)
    const [classifyingIntent, setClassifyingIntent] = useState(false)
    const [checkpoints, setCheckpoints] = useState<BlogCheckpoint[]>([])
    const [showCheckpoints, setShowCheckpoints] = useState(false)
    const [activeEditorImage, setActiveEditorImage] = useState<string | null>(null)
    const [conversationId] = useState(() => crypto.randomUUID())
    const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash')
    const userId = user?.id || 'guest-user-id';
    const scrollRef = useRef<HTMLDivElement>(null)

    const modelOptions = [
        { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
        { value: 'gpt-4o', label: 'GPT-4o' },
        { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B (Groq)' },
        { value: 'mixtral-8x7b', label: 'Mixtral 8x7B (Groq)' },
    ]

    const { generate, isLoading, error } = useGeneration(isAuthenticated)

    // Auto-open editor when content is generated
    useEffect(() => {
        const lastMsg = messages[messages.length - 1]
        if (lastMsg?.role === 'assistant' &&
            (lastMsg.type === 'blog' || lastMsg.type === 'edit' || lastMsg.type === 'rewrite')) {
            setShowEditorPanel(true)
            setSidebarEditingId(lastMsg.id)
        }
    }, [messages])

    // Auth Effect
    useEffect(() => {
        const supabase = createClient()
        // Get initial user
        supabase.auth.getUser().then(({ data: { user } }) => {
            setUser(user)
        })

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null)
        })

        return () => subscription.unsubscribe()
    }, [])

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
                // Find the latest content message
                const blogMsg = messages
                    .slice()
                    .reverse()
                    .find(m => (m.type === 'blog' || m.type === 'edit' || m.type === 'rewrite') && m.role === 'assistant')

                await saveContext({
                    conversation_id: conversationId,
                    user_id: userId,
                    messages: messages.map(m => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        type: m.type as any, // Cast or update context API type separately if needed
                        timestamp: m.timestamp.toISOString(),
                        tone: m.tone,
                        length: m.length,
                        image_url: m.image_url
                    })),
                    chat_messages: chatMessages.map(m => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        type: m.type as any,
                        timestamp: m.timestamp.toISOString(),
                        tone: m.tone,
                        length: m.length,
                        image_url: m.image_url
                    })),
                    current_blog_content: blogMsg?.content
                })
            } catch (error) {
                console.error('Error saving context:', error)
            }
        }

        const timer = setTimeout(saveContextToDB, 2000)
        return () => clearTimeout(timer)
    }, [messages, conversationId, userId])

    // Get context summary for classifier
    const getContextSummary = (): string => {
        const chatMessages = messages.filter(m => m.type === 'chat')
        return chatMessages
            .slice(-4)
            .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`)
            .join('\n')
    }

    // Classify intent using backend classifier
    const classifyPromptType = async (text: string): Promise<IntentClassificationResponse> => {
        try {
            setClassifyingIntent(true)
            const contextSummary = getContextSummary()

            const result = await classifyIntent({
                prompt: text,
                context_summary: contextSummary || undefined
            })

            console.log('[DEBUG] Classification result:', result)
            return result
        } catch (error) {
            console.error('Classification failed, falling back to frontend detection:', error)
            const fallbackIntent = fallbackClassifyPromptType(text)
            return {
                intent: fallbackIntent,
                confidence: 0.5,
                reasoning: 'Fallback frontend detection',
                cached: false
            }
        } finally {
            setClassifyingIntent(false)
        }
    }

    // Fallback keyword-based classification
    const fallbackClassifyPromptType = (text: string): 'blog' | 'chat' | 'edit' | 'rewrite' | 'image' => {
        const lowerText = text.toLowerCase()

        // Check for IMAGE keywords FIRST
        const imageKeywords = ['image', 'picture', 'photo', 'drawing', 'illustration', 'logo', 'visual', 'generate an image']
        if (imageKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'image'
        }

        // Check for rewrite keywords
        const rewriteKeywords = ['rewrite', 'restart', 'start over', 'from scratch', 'completely new', 'fresh', 'different angle']
        if (rewriteKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'rewrite'
        }

        // Check if there's an existing blog to edit
        const existingBlog = messages.find(m => m.type === 'blog' && m.role === 'assistant')

        // Check for edit keywords
        const editKeywords = ['improve', 'enhance', 'better', 'add', 'more', 'expand', 'polish', 'refine', 'strengthen', 'update', 'modify', 'edit', 'change']
        if (existingBlog && editKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'edit'
        }

        // Check for blog creation keywords
        const blogKeywords = [
            'write', 'create', 'generate', 'draft', 'compose', 'blog', 'article', 'post',
            'content', 'story', 'guide', 'email', 'copy', 'description'
        ]
        if (blogKeywords.some(keyword => lowerText.includes(keyword))) {
            return 'blog'
        }

        return 'chat'
    }

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, isLoading])

    // Auto-select the latest content message
    useEffect(() => {
        const lastContentMsg = messages
            .filter(m => (m.type === 'blog' || m.type === 'edit' || m.type === 'rewrite') && m.role === 'assistant')
            .pop()
        if (lastContentMsg && lastContentMsg.id !== sidebarEditingId) {
            setSidebarEditingId(lastContentMsg.id)
        }
    }, [messages])


    const handleTranscription = (text: string) => {
        setInput(prev => prev ? `${prev} ${text}` : text)
    }

    const handleSend = async () => {
        if (!input.trim() || isLoading || classifyingIntent) return

        const classificationResult = await classifyPromptType(input)
        const messageType = classificationResult.intent

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: 'user',
            content: input,
            timestamp: new Date(),
            type: messageType,
            tone,
            length,
            topic: classificationResult.topic,
            refined_query: classificationResult.refined_query
        }

        const updatedMessages = [...messages, userMsg]
        setMessages(updatedMessages)
        setInput('')

        await processGeneration(userMsg, updatedMessages)
    }

    const processGeneration = async (msg: Message, allMessages: Message[]) => {
        // Build complete conversation history
        const fullHistory = allMessages
            .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`)
            .join('\n\n')

        // Get conversation context
        const chatContext = allMessages.filter(m => m.type === 'chat')
        const contextSummary = chatContext
            .map(m => `${m.role === 'user' ? 'User' : 'AI'}: ${m.content}`)
            .join('\n')

        // Get current blog content for edit context
        const currentBlogMsg = allMessages
            .slice()
            .reverse()
            .find(m => (m.type === 'blog' || m.type === 'edit' || m.type === 'rewrite') && m.role === 'assistant')
        const blogContext = currentBlogMsg ? `Current content:\n${currentBlogMsg.content}` : ''

        let actionType = msg.type
        let finalPrompt = msg.content

        if (actionType === 'chat') {
            if (fullHistory) {
                finalPrompt = `Previous conversation:\n${fullHistory}\n\nAnswer the user's question while remembering the full conversation context above.`
            }
        } else if (actionType === 'blog') {
            finalPrompt = msg.content
        } else if (actionType === 'edit') {
            if (blogContext) {
                finalPrompt = `${blogContext}\n\nUser request: ${msg.content}`
            }
        } else if (actionType === 'rewrite') {
            if (contextSummary) {
                finalPrompt = `Based on this conversation:\n${contextSummary}\n\nUser request: ${msg.content.replace(/rewrite|restart|start over|from scratch|completely new/gi, '').trim() || 'Create a blog'}`
            }
        } else if (actionType === 'image') {
            // Image intent: just pass the prompt, the backend handles it as standalone
            finalPrompt = msg.content
        }

        const result = await generate({
            prompt: finalPrompt,
            intent: msg.type, // Pass the detected intent!
            tone: msg.tone || 'informative',
            length: msg.length || 'medium',
            model: selectedModel,
            topic: msg.topic,
            refined_query: msg.refined_query
        })



        if (result) {
            // Check for missing image in blog response and notify user
            if ((msg.type === 'blog' || msg.type === 'edit' || msg.type === 'rewrite') && !result.image_url) {
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
                if (msg.type === 'blog' || msg.type === 'edit' || msg.type === 'rewrite') {
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
        const blogMsg = messages.find(m => (m.type === 'blog' || m.type === 'edit' || m.type === 'rewrite') && m.role === 'assistant')
        if (!blogMsg) {
            alert('No blog content to checkpoint')
            return
        }

        try {
            const title = `Blog Version ${checkpoints.length + 1}`
            const chatContext = messages
                .filter(m => ['chat', 'image', 'blog', 'edit', 'rewrite'].includes(m.type))
                .map(m => ({
                    id: m.id,
                    role: m.role,
                    content: m.content,
                    timestamp: m.timestamp.toISOString(),
                    tone: m.tone,
                    length: m.length,
                    image_url: m.image_url,
                    type: m.type // Also save type to restore correctly
                }))

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
                    type: (msg.type as any) || 'chat',
                    tone: msg.tone,
                    length: msg.length,
                    image_url: msg.image_url
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
                length: restored.length || length,
                image_url: restored.image_url
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
        m.id === sidebarEditingId && (m.type === 'blog' || m.type === 'edit' || m.type === 'rewrite') && m.role === 'assistant'
    )

    return (
        <div className="flex h-screen w-full bg-background relative overflow-hidden">
            {/* Animated background elements */}
            {/* Solid Background - No Blobs */}
            <div className="absolute inset-0 bg-background pointer-events-none"></div>

            {/* Main Chat Area */}
            <div className={cn(
                "flex flex-col flex-1 transition-all duration-300",
                showEditorPanel ? "w-1/2" : "w-full"
            )}>
                {/* Premium Header with Glass Morphism */}
                {/* Modern Premium Header with Glass Morphism */}
                <div className="sticky top-0 z-20 border-b border-border/40 bg-background/80 backdrop-blur-md shadow-sm">
                    <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                        {/* Brand Section */}
                        <div className="flex items-center gap-4">
                            <div className="relative w-10 h-10 bg-primary/10 flex items-center justify-center rounded-xl border border-primary/20 shadow-[0_0_15px_-3px_var(--primary)]">
                                <Bot className="w-6 h-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold bg-gradient-to-r from-white via-blue-100 to-blue-200 bg-clip-text text-transparent tracking-tight">
                                    Verbix AI
                                </h1>
                            </div>
                        </div>

                        {/* Controls Section */}
                        <div className="flex items-center gap-4">
                            {/* Editor Controls - Only show if messages exist */}
                            {messages.length > 0 && (
                                <>
                                    <div className="flex gap-1 bg-secondary/30 border border-border/50 p-1 shadow-inner rounded-lg hidden md:flex backdrop-blur-sm">
                                        <Select value={tone} onValueChange={setTone}>
                                            <SelectTrigger className="w-[120px] bg-transparent border-0 text-sm text-muted-foreground hover:text-foreground font-medium focus:ring-0 transition-colors">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent className="bg-popover/95 border-border backdrop-blur-xl">
                                                <SelectItem value="informative">Informative</SelectItem>
                                                <SelectItem value="casual">Casual</SelectItem>
                                                <SelectItem value="professional">Professional</SelectItem>
                                                <SelectItem value="creative">Creative</SelectItem>
                                                <SelectItem value="humorous">Humorous</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <div className="w-px bg-border/40 my-1"></div>
                                        <Select value={length} onValueChange={setLength}>
                                            <SelectTrigger className="w-[100px] bg-transparent border-0 text-sm text-muted-foreground hover:text-foreground font-medium focus:ring-0 transition-colors">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent className="bg-popover/95 border-border backdrop-blur-xl">
                                                <SelectItem value="short">Short</SelectItem>
                                                <SelectItem value="medium">Medium</SelectItem>
                                                <SelectItem value="long">Long</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <div className="w-px bg-border/40 my-1"></div>
                                        <Select value={selectedModel} onValueChange={setSelectedModel}>
                                            <SelectTrigger className="w-[150px] bg-transparent border-0 text-sm text-muted-foreground hover:text-foreground font-medium focus:ring-0 transition-colors">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent className="bg-popover/95 border-border backdrop-blur-xl">
                                                {modelOptions.map(opt => (
                                                    <SelectItem key={opt.value} value={opt.value}>
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="w-px h-8 bg-border/40 mx-2"></div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setShowCheckpoints(!showCheckpoints)}
                                        className={cn(
                                            "h-9 w-9 p-0 rounded-lg transition-all hover:bg-secondary/50 text-muted-foreground hover:text-foreground",
                                            showCheckpoints && "bg-primary/20 text-primary hover:bg-primary/30"
                                        )}
                                        title="View checkpoints"
                                    >
                                        <Clock className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleCreateCheckpoint}
                                        disabled={!(messages.find(m => (m.type === 'blog' || m.type === 'edit' || m.type === 'rewrite') && m.role === 'assistant') || (showEditorPanel && sidebarEditingId && (() => { const msg = messages.find(m => m.id === sidebarEditingId); return msg && (msg.type === 'blog' || msg.type === 'edit' || msg.type === 'rewrite'); })()))}
                                        className="h-9 w-9 p-0 rounded-lg transition-all hover:bg-secondary/50 text-muted-foreground hover:text-foreground disabled:opacity-30"
                                        title="Create checkpoint"
                                    >
                                        <BookmarkPlus className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setShowEditorPanel(!showEditorPanel)}
                                        className={cn(
                                            "h-9 w-9 p-0 rounded-lg transition-all hover:bg-secondary/50 text-muted-foreground hover:text-foreground",
                                            showEditorPanel && "bg-primary/20 text-primary hover:bg-primary/30"
                                        )}
                                        title={showEditorPanel ? "Hide editor" : "Show editor"}
                                    >
                                        <PanelRight className="w-4 h-4" />
                                    </Button>
                                </>
                            )}

                            {/* User Controls */}
                            {user ? (
                                <>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setIsSettingsOpen(true)}
                                        className="text-muted-foreground hover:text-foreground hover:bg-secondary/50 rounded-lg transition-all duration-300"
                                        title="Settings"
                                    >
                                        <SettingsIcon className="w-5 h-5" />
                                    </Button>
                                    <LogoutButton />

                                    <SettingsModal
                                        isOpen={isSettingsOpen}
                                        onClose={() => setIsSettingsOpen(false)}
                                        userId={user.id}
                                    />
                                </>
                            ) : (
                                <>
                                    <Link
                                        href="/auth/login"
                                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors duration-200"
                                    >
                                        Sign In
                                    </Link>
                                    <Link
                                        href="/auth/sign-up"
                                        className="text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all duration-200"
                                    >
                                        Sign Up
                                    </Link>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Messages Area - Professional Layout */}
                <div className="flex-1 overflow-hidden relative">
                    <ScrollArea className="h-full w-full">
                        <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
                            {messages.length === 0 && (
                                <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 animate-in fade-in-50 slide-in-from-bottom-5 duration-500">
                                    <div className="flex justify-center">
                                        <div className="relative">
                                            <div className="relative w-20 h-20 bg-background/50 border border-border flex items-center justify-center rounded-3xl shadow-2xl shadow-primary/10 backdrop-blur-xl">
                                                <Bot className="w-10 h-10 text-primary animate-pulse" />
                                            </div>
                                            <div className="absolute -inset-4 bg-primary/20 rounded-[40px] blur-3xl -z-10 animate-pulse"></div>
                                        </div>
                                    </div>
                                    <div className="space-y-4 text-center">
                                        <h3 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-100 to-blue-200 inline-block px-6 py-2">
                                            Welcome to Verbix AI
                                        </h3>
                                        <p className="text-muted-foreground max-w-lg mx-auto leading-relaxed text-lg font-light">
                                            Powered by advanced AI agents, ready to generate professional content tailored to your needs.
                                        </p>
                                    </div>

                                    {/* Centered Input Area for Empty State */}
                                    <div className="w-full max-w-2xl mx-auto space-y-6">
                                        <div className="relative group">
                                            <div className="relative flex gap-3 items-end bg-secondary/30 border border-border/50 rounded-2xl px-5 py-4 transition-all duration-300 shadow-sm hover:shadow-md hover:bg-secondary/40 backdrop-blur-md">
                                                <Textarea
                                                    value={input}
                                                    onChange={(e) => setInput(e.target.value)}
                                                    placeholder="Ask anything about your blog, get writing tips, or request content creation..."
                                                    className="flex-1 resize-none max-h-32 min-h-[80px] bg-transparent border-0 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-0 text-base leading-relaxed"
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
                                                    className="flex-shrink-0 h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground text-primary-foreground font-bold border border-white/10 shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all duration-200 flex items-center justify-center p-0"
                                                >
                                                    {isLoading ? (
                                                        <div className="w-5 h-5 bg-white rounded-full animate-pulse"></div>
                                                    ) : (
                                                        <span className="text-xl">→</span>
                                                    )}
                                                </Button>
                                            </div>

                                            <VoiceInput
                                                onTranscription={handleTranscription}
                                                className="absolute right-16 bottom-3.5 z-10 hover:bg-secondary/80"
                                                isCompact={true}
                                            />
                                        </div>

                                        <div className="grid grid-cols-3 gap-4">
                                            <div className="p-3 bg-secondary/30 border border-border/50 rounded-xl flex items-center justify-between backdrop-blur-sm group hover:bg-secondary/50 transition-colors">
                                                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider pl-2">Tone</p>
                                                <Select value={tone} onValueChange={setTone}>
                                                    <SelectTrigger className="w-[110px] h-8 bg-transparent border-0 text-sm text-foreground font-medium hover:bg-white/5 rounded-lg text-right px-2 shadow-none focus:ring-0">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent className="bg-popover/95 border-border backdrop-blur-xl">
                                                        <SelectItem value="informative">Informative</SelectItem>
                                                        <SelectItem value="casual">Casual</SelectItem>
                                                        <SelectItem value="professional">Professional</SelectItem>
                                                        <SelectItem value="creative">Creative</SelectItem>
                                                        <SelectItem value="humorous">Humorous</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="p-3 bg-secondary/30 border border-border/50 rounded-xl flex items-center justify-between backdrop-blur-sm group hover:bg-secondary/50 transition-colors">
                                                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider pl-2">Length</p>
                                                <Select value={length} onValueChange={setLength}>
                                                    <SelectTrigger className="w-[100px] h-8 bg-transparent border-0 text-sm text-foreground font-medium hover:bg-white/5 rounded-lg text-right px-2 shadow-none focus:ring-0">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent className="bg-popover/95 border-border backdrop-blur-xl">
                                                        <SelectItem value="short">Short</SelectItem>
                                                        <SelectItem value="medium">Medium</SelectItem>
                                                        <SelectItem value="long">Long</SelectItem>
                                                        <SelectItem value="extended">Extended</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                            <div className="p-3 bg-secondary/30 border border-border/50 rounded-xl flex items-center justify-between backdrop-blur-sm group hover:bg-secondary/50 transition-colors">
                                                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider pl-2">Model</p>
                                                <Select value={selectedModel} onValueChange={setSelectedModel}>
                                                    <SelectTrigger className="w-[130px] h-8 bg-transparent border-0 text-sm text-foreground font-medium hover:bg-white/5 rounded-lg text-right px-2 shadow-none focus:ring-0">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent className="bg-popover/95 border-border backdrop-blur-xl">
                                                        {modelOptions.map(opt => (
                                                            <SelectItem key={opt.value} value={opt.value}>
                                                                {opt.label}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {messages
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
                                                "px-6 py-4 border transition-all duration-200 shadow-sm",
                                                msg.role === 'user'
                                                    ? "bg-primary text-primary-foreground border-primary/20 rounded-2xl rounded-tr-sm"
                                                    : "bg-secondary/40 text-card-foreground border-border/50 rounded-2xl rounded-tl-sm backdrop-blur-sm"
                                            )}>
                                                <div className="prose prose-invert max-w-none prose-p:m-0 prose-p:leading-relaxed text-sm leading-relaxed break-words font-light">
                                                    {(msg.role === 'user' || (msg.type !== 'blog' && msg.type !== 'edit' && msg.type !== 'rewrite')) && (
                                                        msg.content.includes('<') ? (
                                                            <div dangerouslySetInnerHTML={{ __html: msg.content }} />
                                                        ) : (
                                                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                        )
                                                    )}
                                                    {msg.image_url && (
                                                        <div className="mt-4 rounded-xl overflow-hidden border border-slate-700/50 relative group/image">
                                                            <img
                                                                src={msg.image_url}
                                                                alt="Generated visual"
                                                                className="w-full h-auto object-cover max-h-[400px]"
                                                            />
                                                            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover/image:opacity-100 transition-opacity duration-200 flex flex-col items-center justify-center gap-3">
                                                                <Button
                                                                    size="sm"
                                                                    variant="secondary"
                                                                    className="bg-white/95 text-black hover:bg-white shadow-lg"
                                                                    onClick={() => {
                                                                        // If editor is already open, just update the image to be inserted
                                                                        if (showEditorPanel && sidebarEditingId) {
                                                                            setActiveEditorImage(msg.image_url || null)
                                                                        } else {
                                                                            // Otherwise, open editor for this message
                                                                            setSidebarEditingId(msg.id)
                                                                            setActiveEditorImage(msg.image_url || null)
                                                                            setShowEditorPanel(true)
                                                                        }
                                                                    }}
                                                                >
                                                                    <PanelRight className="w-4 h-4 mr-2" />
                                                                    Insert into Blog
                                                                </Button>
                                                                <Button
                                                                    size="sm"
                                                                    variant="secondary"
                                                                    className="bg-white/95 text-black hover:bg-white shadow-lg"
                                                                    onClick={async () => {
                                                                        try {
                                                                            toast.info("Regenerating image...")
                                                                            const response = await fetch('http://localhost:8000/v1/content/regenerate-image', {
                                                                                method: 'POST',
                                                                                headers: { 'Content-Type': 'application/json' },
                                                                                body: JSON.stringify({ content: msg.content })
                                                                            })
                                                                            const data = await response.json()
                                                                            if (data.image_url) {
                                                                                // Update local message state with new image
                                                                                setMessages(prev => prev.map(m =>
                                                                                    m.id === msg.id ? { ...m, image_url: data.image_url } : m
                                                                                ))
                                                                                toast.success("Image regenerated!")

                                                                                // If this message is currently being edited, update the editor too
                                                                                if (currentEditingMessage?.id === msg.id) {
                                                                                    // Force update via sidebar props (it listens to message updates if we pass specific props, but right now it takes initialData)
                                                                                    // Since SidebarEditor is open, we might need to close and reopen or pass the new URL dynamically.
                                                                                    // The SidebarEditor receives `imageUrl` prop from `currentEditingMessage`.
                                                                                    // So updating `setMessages` should propagate if `currentEditingMessage` is derived from `messages`.
                                                                                    // Check how `currentEditingMessage` is defined.
                                                                                }
                                                                            } else {
                                                                                toast.error("Failed to regenerate image")
                                                                            }
                                                                        } catch (e) {
                                                                            toast.error("Error regenerating image")
                                                                        }
                                                                    }}
                                                                >
                                                                    <RefreshCw className="w-4 h-4 mr-2" />
                                                                    Regenerate
                                                                </Button>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 px-2 text-xs text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <span>{new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
                                            </div>
                                        </div>

                                        <Avatar className={cn(
                                            "w-9 h-9 mt-1 flex-shrink-0 border border-white/10 shadow-lg",
                                            msg.role === 'user'
                                                ? "bg-secondary"
                                                : "bg-primary/20"
                                        )}>
                                            <div className={cn(
                                                "w-full h-full flex items-center justify-center rounded-full",
                                                msg.role === 'user'
                                                    ? "bg-secondary text-secondary-foreground"
                                                    : "bg-primary/10 text-primary"
                                            )}>
                                                {msg.role === 'user' ? (
                                                    <User className="w-5 h-5" />
                                                ) : (
                                                    <Bot className="w-5 h-5" />
                                                )}
                                            </div>
                                        </Avatar>
                                    </div>
                                ))}

                            {isLoading && (
                                <div className="flex gap-4 group animate-in fade-in-50 slide-in-from-bottom-3 duration-500">
                                    <Avatar className="w-10 h-10 mt-1 flex-shrink-0 border-2 border-blue-400/50 shadow-lg shadow-blue-500/30">
                                        <div className="w-full h-full rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                                            <Bot className="w-5 h-5 text-white animate-pulse" />
                                        </div>
                                    </Avatar>
                                    <div className="flex items-center gap-3 px-5 py-3.5 rounded-2xl bg-slate-800/80 border border-slate-700/50 backdrop-blur-sm rounded-bl-sm">
                                        <div className="flex gap-1.5">
                                            <div className="w-2.5 h-2.5 bg-blue-400/60 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                            <div className="w-2.5 h-2.5 bg-cyan-400/60 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                            <div className="w-2.5 h-2.5 bg-blue-400/60 rounded-full animate-bounce"></div>
                                        </div>
                                        <span className="text-xs text-slate-400 ml-1 font-medium">AI is thinking...</span>
                                    </div>
                                </div>
                            )}
                            <div ref={scrollRef} />
                        </div>
                    </ScrollArea>
                </div>



                {/* Neo-Brutalist Input Footer - ONLY SHOW IF MESSAGES EXIST */}
                {
                    messages.length > 0 && (
                        <div className="sticky bottom-0 border-t-2 border-border bg-background shadow-none z-10">
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
                                    <div className="relative flex gap-3 items-end bg-secondary/30 border border-border/50 rounded-2xl px-5 py-4 transition-all duration-300 shadow-sm hover:shadow-md hover:bg-secondary/40 backdrop-blur-md">
                                        <Textarea
                                            value={input}
                                            onChange={(e) => setInput(e.target.value)}
                                            placeholder="Ask anything about your blog, get writing tips, or request content creation..."
                                            className="flex-1 resize-none max-h-24 bg-transparent border-0 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-0 text-sm leading-relaxed"
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
                                            className="flex-shrink-0 rounded-xl bg-primary hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground text-primary-foreground font-bold uppercase text-xs border border-white/10 shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all duration-200 px-4 py-2"
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
                                    <VoiceInput
                                        onTranscription={handleTranscription}
                                        className="absolute right-24 bottom-2 z-10 hover:bg-secondary/80"
                                        isCompact={true}
                                    />
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
                    )
                }
            </div >


            {/* Right Sidebar - Editor or Checkpoints */}
            {
                showEditorPanel && (
                    <div className="w-1/2 border-l-2 border-border bg-background flex flex-col">
                        {showCheckpoints ? (
                            // Checkpoints Panel
                            <div className="flex flex-col h-full">
                                <div className="flex items-center justify-between p-4 border-b-2 border-border bg-card">
                                    <h3 className="font-semibold text-lg text-foreground flex items-center gap-2">
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
                                                    className="p-4 bg-card border-2 border-border hover:border-primary transition-all group shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px]"
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
                                key={currentEditingMessage?.id}
                                initialData={currentEditingMessage?.content || ''}
                                onSave={handleSaveEdit}
                                onClose={handleCloseSidebar}
                                title={`Blog Editor - ${currentEditingMessage?.timestamp ? new Date(currentEditingMessage.timestamp).toLocaleString() : ''}`}
                                userId={userId}
                                imageUrl={activeEditorImage}
                            />
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full space-y-4 text-slate-400">
                                <PanelRight className="w-12 h-12 opacity-50" />
                                <p className="text-center max-w-xs">Request content creation or use words like "write", "create", "generate" to populate the editor</p>
                            </div>
                        )}
                    </div>
                )
            }
        </div >
    )
}
