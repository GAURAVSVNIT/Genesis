import { deleteGuestHistory, getGuestHistory } from '@/lib/api/guest'
import { createClient } from '@/lib/supabase/client'

export interface MigrationResult {
    success: boolean
    messageCount: number
    error?: string
}

/**
 * Get guest ID from localStorage or sessionStorage (fallback for auth flows)
 * @returns Guest ID or null if not found
 */
function getGuestIdForMigration(): string | null {
    // First try localStorage (normal case)
    let guestId = localStorage.getItem('guestId')

    if (!guestId) {
        // Fallback to sessionStorage (for post-auth migration)
        guestId = sessionStorage.getItem('pendingMigrationGuestId')
        console.log('Migration: Using sessionStorage fallback for guestId:', guestId)
    }

    return guestId
}

/**
 * Migrates guest chat history from Redis to Supabase
 * @param guestId - The guest session ID from localStorage
 * @returns Migration result with success status and message count
 */
export async function migrateGuestChatToSupabase(guestId: string): Promise<MigrationResult> {
    console.log(`📦 [MIGRATION START] Guest ID: ${guestId}`)
    try {
        // 1. Fetch guest chat history from Redis (via backend API)
        console.log('⏳ [STEP 1/4] Fetching chat history from Redis...')
        const history = await getGuestHistory(guestId)
        console.log(`✓ [STEP 1/4] Redis returned ${history.length} messages`)

        if (!history || history.length === 0) {
            console.log('ℹ️ [MIGRATION END] No chat history found - nothing to migrate')
            return {
                success: true,
                messageCount: 0,
                error: 'No chat history found'
            }
        }

        // 2. Get current authenticated user
        console.log('⏳ [STEP 2/4] Verifying user authentication...')
        const supabase = createClient()
        const { data: { user }, error: userError } = await supabase.auth.getUser()

        if (userError || !user) {
            console.error('❌ [STEP 2/4] Auth failed:', userError?.message)
            throw new Error('User not authenticated')
        }
        console.log(`✓ [STEP 2/4] User authenticated: ${user.id}`)

        // 3. Insert chat history into Supabase 'chats' table
        console.log(`⏳ [STEP 3/4] Inserting ${history.length} messages into Supabase...`)
        const { error: insertError } = await supabase.from('chats').insert(
            history.map(msg => ({
                user_id: user.id,
                role: msg.role,
                content: msg.content,
                created_at: msg.timestamp
            }))
        )

        if (insertError) {
            console.error('❌ [STEP 3/4] Insert failed:', insertError.message)
            throw new Error(`Failed to insert chat history: ${insertError.message}`)
        }
        console.log(`✓ [STEP 3/4] Successfully inserted ${history.length} messages`)

        console.log('✅ [MIGRATION END] Success!')
        return {
            success: true,
            messageCount: history.length
        }
    } catch (error) {
        console.error('❌ [MIGRATION ERROR]', error)
        return {
            success: false,
            messageCount: 0,
            error: error instanceof Error ? error.message : 'Unknown error'
        }
    }
}

/**
 * Cleanup guest session data from both localStorage and sessionStorage
 * @param guestId - The guest session ID to remove
 */
export function cleanupGuestSession(guestId: string): void {
    console.log(`🧹 [CLEANUP] Removing guest session: ${guestId}`)
    localStorage.removeItem('guestId')
    sessionStorage.removeItem('pendingMigrationGuestId')
    console.log('✓ [CLEANUP] Complete - localStorage and sessionStorage cleared')
}

/**
 * Complete migration workflow: migrate data and cleanup
 * Uses both localStorage and sessionStorage to find guestId
 * @param guestId - Optional guest ID (if not provided, will auto-detect)
 * @returns Migration result
 */
export async function performCompleteMigration(guestId?: string): Promise<MigrationResult> {
    console.log('🚀 [performCompleteMigration] Starting...')

    // Use provided guestId or auto-detect from storage
    const targetGuestId = guestId || getGuestIdForMigration()

    if (!targetGuestId) {
        // User signed up/in without creating guest chats - this is normal, not an error
        console.log('ℹ️ [performCompleteMigration] No guest session found - skipping migration')
        return {
            success: true,
            messageCount: 0
        }
    }

    console.log(`✓ [performCompleteMigration] Found guest ID: ${targetGuestId}`)
    const result = await migrateGuestChatToSupabase(targetGuestId)

    // Always cleanup guest session, even if migration failed
    cleanupGuestSession(targetGuestId)

    return result
}
