'use client'

import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { LogoutButton } from '@/components/logout-button'
import { useEffect, useState } from 'react'
import type { User } from '@supabase/supabase-js'

export function Navigation() {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)

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
            <nav className="sticky top-0 z-50 border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
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
        <nav className="sticky top-0 z-50 border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl shadow-lg">
            <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                    Genesis
                </Link>

                <div className="flex items-center gap-4">
                    {user ? (
                        <>
                            <span className="text-sm text-slate-300">{user.email}</span>
                            <LogoutButton />
                        </>
                    ) : (
                        <>
                            <Link
                                href="/auth/login"
                                className="text-sm font-medium text-slate-300 hover:text-blue-400 transition-colors duration-200"
                            >
                                Sign In
                            </Link>
                            <Link
                                href="/auth/sign-up"
                                className="text-sm font-medium bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white px-4 py-2 rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl"
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
