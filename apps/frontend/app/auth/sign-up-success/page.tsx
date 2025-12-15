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
import { getGuestHistory } from '@/lib/api/guest'
import { Loader2 } from 'lucide-react'

export default function Page() {
    const [isMigrating, setIsMigrating] = useState(false)
    const [migrationStatus, setMigrationStatus] = useState('')

    useEffect(() => {
        const migrateChats = async () => {
            const guestId = localStorage.getItem('guestId')
            if (!guestId) return

            setIsMigrating(true)
            setMigrationStatus('Found temporary chat history...')

            try {
                // 1. Fetch from Redis
                const history = await getGuestHistory(guestId)

                if (history.length > 0) {
                    setMigrationStatus(`Migrating ${history.length} messages...`)
                    const supabase = createClient()

                    // 2. Get current user
                    const { data: { user } } = await supabase.auth.getUser()

                    if (user) {
                        // 3. Save to Supabase (Assumes 'chats' table exists)
                        // Note: You might need to adjust the table/column names
                        const { error } = await supabase.from('chats').insert(
                            history.map(msg => ({
                                user_id: user.id,
                                role: msg.role,
                                content: msg.content,
                                created_at: msg.timestamp
                            }))
                        )

                        if (error) {
                            console.error('Migration failed:', error)
                            setMigrationStatus('Failed to migrate history.')
                        } else {
                            setMigrationStatus('Chat history saved!')
                        }
                    }
                }
            } catch (error) {
                console.error('Migration error:', error)
            } finally {
                // 4. Cleanup
                localStorage.removeItem('guestId')
                setIsMigrating(false)
            }
        }

        migrateChats()
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
