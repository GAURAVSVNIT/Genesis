// API client for blog generation

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface BlogRequest {
    prompt: string
    tone: string
    length: string
    guestId?: string | null
}

export interface BlogResponse {
    success: boolean
    content: string
    seo_score: number
    uniqueness_score: number
    engagement_score: number
    cost_usd: number
    total_cost_usd: number
    cached: boolean
    cache_hit_rate?: number
    generation_time_ms: number
    rate_limit_remaining: number
    rate_limit_reset_after: number
    safety_checks?: Record<string, unknown>
    tokens_used?: number
    image_url?: string
    seo_data?: Record<string, unknown>
    trend_data?: Record<string, unknown>
}

export async function generateBlog(request: BlogRequest): Promise<BlogResponse> {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/content/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request),
        })

        if (!response.ok) {
            throw new Error(`Failed to generate blog: ${response.statusText}`)
        }

        return await response.json()
    } catch (error) {
        console.error('Blog generation error:', error)
        throw error
    }
}
