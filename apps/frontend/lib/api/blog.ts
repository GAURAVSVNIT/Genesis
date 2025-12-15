// API client for blog generation

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface BlogRequest {
    prompt: string
    tone: string
    length: string
}

export interface BlogResponse {
    blog: string
}

export async function generateBlog(request: BlogRequest): Promise<BlogResponse> {
    try {
        const response = await fetch(`${BACKEND_URL}/v1/blog/generate`, {
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
