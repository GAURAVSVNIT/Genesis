'use client'

import { useEffect, useRef } from 'react'
import { usePathname } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { performCompleteMigration } from '@/lib/utils/migration'

export function GuestMigrationHandler() {
    // strict mode double invocation protection
    const hasRun = useRef(false)
    const pathname = usePathname()

    useEffect(() => {
        const checkAndMigrate = async () => {
            if (hasRun.current) return
            hasRun.current = true

            // Skip migration on auth pages to avoid interference with email verification
            if (pathname?.startsWith('/auth/')) {
                console.log('GuestMigrationHandler: Skipping on auth page')
                return
            }

            console.log('GuestMigrationHandler: Mounting...')

            const supabase = createClient()
            const { data: { user } } = await supabase.auth.getUser()

            console.log('GuestMigrationHandler: Status Check:', {
                isLoggedIn: !!user,
                userId: user?.id
            })

            // Only proceed if user is logged in (guestId will be auto-detected)
            if (!user) {
                return
            }

            console.log('GuestMigrationHandler: User logged in. Attempting migration...')

            try {
                // performCompleteMigration will auto-detect guestId from localStorage or sessionStorage
                const result = await performCompleteMigration()
                if (result.success && result.messageCount > 0) {
                    console.log(`Success! We've saved your ${result.messageCount} guest chats to your history.`)
                } else if (!result.success) {
                    console.error('Migration failed silently:', result.error)
                }
            } catch (error) {
                console.error('Migration handler error:', error)
            }
        }

        checkAndMigrate()
    }, [pathname])

    return null
}
