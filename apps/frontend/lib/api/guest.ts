// API client for guest chat sessions

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface ChatMessage {
    role: string
    content: string
    timestamp: string
}

export async function saveGuestMessage(guestId: string, message: ChatMessage): Promise<void> {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/guest/chat/${guestId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(message),
        })

        if (!response.ok) {
            console.error('Failed to save guest message', await response.text())
        }
    } catch (error) {
        console.error('Error saving guest message:', error)
    }
}

export async function getGuestHistory(guestId: string): Promise<ChatMessage[]> {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/guest/chat/${guestId}`)

        if (!response.ok) {
            throw new Error(`Failed to fetch guest history: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Error fetching guest history:', error)
        return []
    }
}
