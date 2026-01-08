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
 * Public helper to get current guest ID from localStorage
 * @returns Guest ID or null if not found
 */
export function getGuestId(): string | null {
    return localStorage.getItem('guestId')
}

/**
 * Perform complete guest-to-user migration
 * Migrates guest chat from backend PostgreSQL to authenticated user account
 */
export async function performCompleteMigration(guestId?: string): Promise<MigrationResult> {
    console.log('📦 [MIGRATION START] Checking for guest data...')
    try {
        // Get guestId from storage or use provided one
        const targetGuestId = guestId || getGuestIdForMigration()

        if (!targetGuestId) {
            console.log('ℹ️ [MIGRATION] No guest ID found - nothing to migrate')
            return {
                success: true,
                messageCount: 0
            }
        }

        // Get authenticated user
        console.log('⏳ [STEP 1/2] Verifying user authentication...')
        const supabase = createClient()
        const { data: { user }, error: userError } = await supabase.auth.getUser()

        if (userError || !user) {
            console.error('❌ [STEP 1/2] Auth failed:', userError?.message)
            throw new Error('User not authenticated')
        }
        console.log(`✓ [STEP 1/2] User authenticated: ${user.id}`)

        // Call backend migration endpoint
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        console.log(`⏳ [STEP 2/2] Calling backend migration for guest ${targetGuestId}...`)
        const response = await fetch(`${API_URL}/v1/guest/migrate/${targetGuestId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                authenticated_user_id: user.id
            })
        })

        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Migration failed')
        }

        const result = await response.json()
        console.log(`✓ [STEP 2/2] Backend migration successful`)

        // Clear guest ID
        console.log('🧹 [CLEANUP] Clearing guest session...')
        cleanupGuestSession(targetGuestId)

        console.log(`✅ [MIGRATION END] Success! Migrated ${result.messages_migrated} messages`)

        return {
            success: true,
            messageCount: result.messages_migrated || 0
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
