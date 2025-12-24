// API client for context and checkpoint management

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface MessageSnapshot {
    id: string
    role: 'user' | 'assistant'
    content: string
    type: 'chat' | 'blog'
    timestamp: string
    tone?: string
    length?: string
}

export interface SaveContextRequest {
    conversation_id: string
    user_id: string
    messages: MessageSnapshot[]
    chat_messages: MessageSnapshot[]
    current_blog_content?: string
}

export interface LoadContextResponse {
    context?: Record<string, unknown>
    messages: MessageSnapshot[]
    chat_messages: MessageSnapshot[]
    current_blog_content?: string
    message_count: number
}

export interface CreateCheckpointRequest {
    conversation_id: string
    user_id: string
    title: string
    content: string
    description?: string
    tone?: string
    length?: string
    context_snapshot?: Record<string, unknown>
}

export interface CheckpointResponse {
    id: string
    title: string
    content: string
    description?: string
    version_number: number
    created_at: string
    is_active: boolean
    tone?: string
    length?: string
}

// Save context to backend
export async function saveContext(request: SaveContextRequest): Promise<{
    status: string
    message_count: number
    timestamp: string
}> {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/context/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        })

        if (!response.ok) {
            throw new Error(`Failed to save context: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error saving context:', error)
        throw error
    }
}

// Load context from backend
export async function loadContext(
    conversation_id: string,
    user_id: string
): Promise<LoadContextResponse> {
    try {
        const response = await fetch(
            `${BACKEND_URL}/v1/context/load/${conversation_id}?user_id=${user_id}`
        )

        if (!response.ok) {
            throw new Error(`Failed to load context: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error loading context:', error)
        throw error
    }
}

// Create blog checkpoint
export async function createCheckpoint(
    request: CreateCheckpointRequest
): Promise<CheckpointResponse> {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/checkpoints/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        })

        if (!response.ok) {
            throw new Error(`Failed to create checkpoint: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error creating checkpoint:', error)
        throw error
    }
}

// List checkpoints
export async function listCheckpoints(
    conversation_id: string,
    user_id: string
): Promise<CheckpointResponse[]> {
    try {
        const response = await fetch(
            `${BACKEND_URL}/v1/checkpoints/list/${conversation_id}?user_id=${user_id}`
        )

        if (!response.ok) {
            throw new Error(`Failed to list checkpoints: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error listing checkpoints:', error)
        throw error
    }
}

// Get specific checkpoint
export async function getCheckpoint(
    checkpoint_id: string,
    user_id: string
): Promise<CheckpointResponse> {
    try {
        const response = await fetch(
            `${BACKEND_URL}/v1/checkpoints/${checkpoint_id}?user_id=${user_id}`
        )

        if (!response.ok) {
            throw new Error(`Failed to get checkpoint: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error getting checkpoint:', error)
        throw error
    }
}

// Restore checkpoint
export async function restoreCheckpoint(
    checkpoint_id: string,
    user_id: string,
    conversation_id?: string
): Promise<{
    status: string
    checkpoint_id: string
    version: number
    title: string
    content: string
    tone?: string
    length?: string
    context_snapshot?: Record<string, unknown>
    restored_at: string
}> {
    try {
        const params = new URLSearchParams({
            user_id: user_id,
            ...(conversation_id && { conversation_id: conversation_id })
        })
        
        const response = await fetch(
            `${BACKEND_URL}/v1/checkpoints/${checkpoint_id}/restore?${params.toString()}`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            }
        )

        if (!response.ok) {
            throw new Error(`Failed to restore checkpoint: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error restoring checkpoint:', error)
        throw error
    }
}

// Delete checkpoint
export async function deleteCheckpoint(
    checkpoint_id: string,
    user_id: string
): Promise<{ status: string; checkpoint_id: string }> {
    try {
        const response = await fetch(
            `${BACKEND_URL}/v1/checkpoints/${checkpoint_id}?user_id=${user_id}`,
            {
                method: 'DELETE',
            }
        )

        if (!response.ok) {
            throw new Error(`Failed to delete checkpoint: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error deleting checkpoint:', error)
        throw error
    }
}
