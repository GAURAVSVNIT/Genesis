'use client'

import { useEffect, useRef, useState } from 'react'
import { usePathname } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { performCompleteMigration } from '@/lib/utils/migration'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function GuestMigrationHandler() {
    // strict mode double invocation protection
    const hasRun = useRef(false)
    const pathname = usePathname()
    const [migrationStatus, setMigrationStatus] = useState<{
        show: boolean
        type: 'success' | 'error'
        message: string
        count?: number
    }>({ show: false, type: 'success', message: '' })

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
                    setMigrationStatus({
                        show: true,
                        type: 'success',
                        message: `✅ Your ${result.messageCount} guest conversations have been transferred to your account!`,
                        count: result.messageCount
                    })
                    console.log(`Success! Migrated ${result.messageCount} guest chats!`)
                    
                    // Auto-hide after 6 seconds
                    setTimeout(() => {
                        setMigrationStatus(prev => ({ ...prev, show: false }))
                    }, 6000)
                } else if (!result.success) {
                    console.error('Migration failed silently:', result.error)
                }
            } catch (error) {
                console.error('Migration handler error:', error)
                setMigrationStatus({
                    show: true,
                    type: 'error',
                    message: 'Failed to migrate guest conversations. They are still available but not linked to your account.'
                })
            }
        }

        checkAndMigrate()
    }, [pathname])

    if (!migrationStatus.show) return null

    return (
        <div className="fixed top-4 right-4 z-50 max-w-sm">
            <Card className={`p-4 border-2 ${
                migrationStatus.type === 'success'
                    ? 'border-green-500/50 bg-green-50 dark:bg-green-950'
                    : 'border-red-500/50 bg-red-50 dark:bg-red-950'
            }`}>
                <div className="flex items-start justify-between">
                    <div className={`text-sm font-medium ${
                        migrationStatus.type === 'success'
                            ? 'text-green-900 dark:text-green-100'
                            : 'text-red-900 dark:text-red-100'
                    }`}>
                        {migrationStatus.message}
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setMigrationStatus(prev => ({ ...prev, show: false }))}
                        className="ml-2"
                    >
                        ✕
                    </Button>
                </div>
            </Card>
        </div>
    )
}
