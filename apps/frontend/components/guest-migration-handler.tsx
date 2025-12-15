'use client'

import { useEffect, useRef } from 'react'
import { createClient } from '@/lib/supabase/client'
import { performCompleteMigration } from '@/lib/utils/migration'

export function GuestMigrationHandler() {
    // strict mode double invocation protection
    const hasRun = useRef(false)

    useEffect(() => {
        const checkAndMigrate = async () => {
            if (hasRun.current) return
            hasRun.current = true

            const guestId = localStorage.getItem('guestId')
            if (!guestId) return

            const supabase = createClient()
            const { data: { user } } = await supabase.auth.getUser()

            if (user) {
                console.log('User logged in and guest session found. Attempting migration...')
                try {
                    const result = await performCompleteMigration(guestId)
                    if (result.success && result.messageCount > 0) {
                        console.log(`Success! We've saved your ${result.messageCount} guest chats to your history.`)
                    } else if (!result.success) {
                        console.error('Migration failed silently:', result.error)
                    }
                } catch (error) {
                    console.error('Migration handler error:', error)
                }
            }
        }

        checkAndMigrate()
    }, [])

    return null
}
