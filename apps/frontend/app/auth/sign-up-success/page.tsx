'use client'

import { useEffect, useState } from 'react'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card'
import { createClient } from '@/lib/supabase/client'
import { performCompleteMigration } from '@/lib/utils/migration'
import { Loader2 } from 'lucide-react'

export default function Page() {
    const [isMigrating, setIsMigrating] = useState(false)
    const [migrationStatus, setMigrationStatus] = useState('')

    useEffect(() => {
        const handleMigration = async () => {
            const guestId = localStorage.getItem('guestId')
            if (!guestId) return

            setIsMigrating(true)
            setMigrationStatus('Checking for temporary chat history...')

            try {
                const result = await performCompleteMigration(guestId)

                if (result.success) {
                    if (result.messageCount > 0) {
                        setMigrationStatus(`✓ Successfully migrated ${result.messageCount} messages!`)
                    } else {
                        setMigrationStatus('No chat history to migrate.')
                    }
                } else {
                    setMigrationStatus(`Migration failed: ${result.error}`)
                }
            } catch (error) {
                console.error('Migration error:', error)
                setMigrationStatus('An unexpected error occurred during migration.')
            } finally {
                setIsMigrating(false)
            }
        }

        handleMigration()
    }, [])

    return (
        <div className="flex min-h-svh w-full items-center justify-center p-6 md:p-10">
            <div className="w-full max-w-sm">
                <div className="flex flex-col gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-2xl">Thank you for signing up!</CardTitle>
                            <CardDescription>Check your email to confirm</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-sm text-muted-foreground">
                                You&apos;ve successfully signed up. Please check your email to confirm your account
                                before signing in.
                            </p>

                            {/* Migration Status */}
                            {(isMigrating || migrationStatus) && (
                                <div className="p-4 bg-muted/50 rounded-lg flex items-center gap-3">
                                    {isMigrating && <Loader2 className="h-4 w-4 animate-spin" />}
                                    <p className="text-sm font-medium">{migrationStatus}</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
