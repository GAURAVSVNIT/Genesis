// Usage tracking for anonymous users

const USAGE_KEY = 'genesis_usage_count'
const MAX_FREE_GENERATIONS = 5

export function getUsageCount(): number {
    if (typeof window === 'undefined') return 0
    const count = localStorage.getItem(USAGE_KEY)
    return count ? parseInt(count, 10) : 0
}

export function incrementUsage(): number {
    if (typeof window === 'undefined') return 0
    const current = getUsageCount()
    const newCount = current + 1
    localStorage.setItem(USAGE_KEY, newCount.toString())
    return newCount
}

export function getRemainingGenerations(): number {
    return Math.max(0, MAX_FREE_GENERATIONS - getUsageCount())
}

export function hasReachedLimit(): boolean {
    return getUsageCount() >= MAX_FREE_GENERATIONS
}

export function resetUsage(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem(USAGE_KEY)
}
