// API client for intent classification

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface IntentClassificationRequest {
    prompt: string
    context_summary?: string
}

export interface IntentClassificationResponse {
    intent: 'chat' | 'blog' | 'edit' | 'rewrite' | 'image'
    confidence: number
    topic?: string
    refined_query?: string
    reasoning: string
    cached: boolean
}

export async function classifyIntent(request: IntentClassificationRequest): Promise<IntentClassificationResponse> {
    try {
        const url = `${BACKEND_URL}/v1/classify/intent`
        console.log('[DEBUG] classifyIntent calling:', url)
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        })

        if (!response.ok) {
            throw new Error(`Classification failed: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Intent classification error:', error)
        throw error
    }
}

export async function classifierHealth() {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/classify/health`)
        return await response.json()
    } catch (error) {
        console.error('Classifier health check failed:', error)
        return { status: 'unknown' }
    }
}
