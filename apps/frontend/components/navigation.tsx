'use client'

import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { LogoutButton } from '@/components/logout-button'
import { useEffect, useState } from 'react'
import type { User } from '@supabase/supabase-js'
import { Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SettingsModal } from '@/components/settings/SettingsModal'

export function Navigation() {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)
    const [isSettingsOpen, setIsSettingsOpen] = useState(false)

    useEffect(() => {
        const supabase = createClient()

        // Get initial user
        supabase.auth.getUser().then(({ data: { user } }) => {
            setUser(user)
            setLoading(false)
        })

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null)
        })

        return () => subscription.unsubscribe()
    }, [])

    if (loading) {
        return (
            <nav className="sticky top-0 z-50 border-b-2 border-border bg-background">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary via-blue-400 to-cyan-400 bg-clip-text text-transparent hover:opacity-90 transition-opacity">
                        Genesis
                    </Link>
                    <div className="flex items-center gap-4">
                        {/* Loading state */}
                    </div>
                </div>
            </nav>
        )
    }

    return (
        <nav className="sticky top-0 z-50 border-b-2 border-border bg-background shadow-none">
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary via-blue-400 to-cyan-400 bg-clip-text text-transparent hover:opacity-90 transition-opacity uppercase tracking-wider">
                    Genesis
                </Link>

                <div className="flex items-center gap-4">
                    {user ? (
                        <>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setIsSettingsOpen(true)}
                                className="text-muted-foreground hover:text-foreground hover:bg-muted border-2 border-transparent hover:border-border rounded-none transition-all duration-300"
                                title="Settings"
                            >
                                <Settings className="w-5 h-5" />
                            </Button>
                            <span className="text-sm text-muted-foreground hidden sm:inline font-bold">{user.email}</span>
                            <LogoutButton />

                            <SettingsModal
                                isOpen={isSettingsOpen}
                                onClose={() => setIsSettingsOpen(false)}
                                userId={user.id}
                            />
                        </>
                    ) : (
                        <>
                            <Link
                                href="/auth/login"
                                className="text-sm font-bold uppercase text-muted-foreground hover:text-primary transition-colors duration-200"
                            >
                                Sign In
                            </Link>
                            <Link
                                href="/auth/sign-up"
                                className="text-sm font-bold uppercase bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 border-2 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:shadow-none hover:translate-x-[2px] hover:translate-y-[2px] transition-all duration-200"
                            >
                                Sign Up
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    )
}
