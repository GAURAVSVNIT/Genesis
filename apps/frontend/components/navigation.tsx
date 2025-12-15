import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { LogoutButton } from '@/components/logout-button'

export async function Navigation() {
    const supabase = await createClient()
    const { data } = await supabase.auth.getClaims()
    const user = data?.claims

    return (
        <nav className="border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between items-center h-16">
                    <div className="flex items-center gap-8">
                        <Link href="/" className="text-xl font-bold">
                            Genesis
                        </Link>
                    </div>

                    <div className="flex items-center gap-4">
                        {user ? (
                            <>
                                <span className="text-sm text-muted-foreground">{user.email}</span>
                                <LogoutButton />
                            </>
                        ) : (
                            <>
                                <Link
                                    href="/auth/login"
                                    className="text-sm font-medium hover:text-primary transition-colors"
                                >
                                    Sign In
                                </Link>
                                <Link
                                    href="/auth/sign-up"
                                    className="text-sm font-medium bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 transition-colors"
                                >
                                    Sign Up
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    )
}
