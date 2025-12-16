import { deleteGuestHistory, getGuestHistory } from '@/lib/api/guest'
import { createClient } from '@/lib/supabase/client'

export async function performCompleteMigration(guestId: string): Promise<MigrationResult> {
    const result = await migrateGuestChatToSupabase(guestId)

    if (result.success) {
        // Keeping guest history in Redis for now (Copy instead of Move)
        // await deleteGuestHistory(guestId).catch(console.error)
    }

    // Always cleanup local guest session
    cleanupGuestSession(guestId)

    return result
}

export interface MigrationResult {
    success: boolean
    messageCount: number
    error?: string
}

/**
 * Migrates guest chat history from Redis to Supabase
 * @param guestId - The guest session ID from localStorage
 * @returns Migration result with success status and message count
 */
export async function migrateGuestChatToSupabase(guestId: string): Promise<MigrationResult> {
    try {
        // 1. Fetch guest chat history from Redis (via backend API)
        const history = await getGuestHistory(guestId)

        if (!history || history.length === 0) {
            return {
                success: true,
                messageCount: 0,
                error: 'No chat history found'
            }
        }

        // 2. Get current authenticated user
        const supabase = createClient()
        const { data: { user }, error: userError } = await supabase.auth.getUser()

        if (userError || !user) {
            throw new Error('User not authenticated')
        }

        // 3. Insert chat history into Supabase 'chats' table
        const { error: insertError } = await supabase.from('chats').insert(
            history.map(msg => ({
                user_id: user.id,
                role: msg.role,
                content: msg.content,
                created_at: msg.timestamp
            }))
        )

        if (insertError) {
            throw new Error(`Failed to insert chat history: ${insertError.message}`)
        }

        return {
            success: true,
            messageCount: history.length
        }
    } catch (error) {
        console.error('Migration error:', error)
        return {
            success: false,
            messageCount: 0,
            error: error instanceof Error ? error.message : 'Unknown error'
        }
    }
}

/**
 * Cleanup guest session data from localStorage
 * @param guestId - The guest session ID to remove
 */
export function cleanupGuestSession(guestId: string): void {
    localStorage.removeItem('guestId')
    console.log(`Cleaned up guest session: ${guestId}`)
}
