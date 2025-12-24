import { type EmailOtpType } from '@supabase/supabase-js'
import { type NextRequest, NextResponse } from 'next/server'

import { createClient } from '@/lib/supabase/server'

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url)
    const token_hash = searchParams.get('token_hash')
    const type = searchParams.get('type') as EmailOtpType | null
    const next = searchParams.get('next') ?? '/'

    const redirectTo = request.nextUrl.clone()
    redirectTo.pathname = next
    redirectTo.searchParams.delete('token_hash')
    redirectTo.searchParams.delete('type')

    const code = searchParams.get('code')
    if (code) {
        const supabase = await createClient()
        const { error, data } = await supabase.auth.exchangeCodeForSession(code)
        if (!error && data?.user) {
            // Trigger migration for signup confirmation
            const guestId = request.cookies.get('pendingMigrationGuestId')?.value
            if (guestId) {
                try {
                    await fetch('http://localhost:8000/v1/guest/migrate/' + guestId, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ authenticated_user_id: data.user.id }),
                    })
                    // Mark migration as done
                    redirectTo.searchParams.set('migrated', 'true')
                } catch (err) {
                    console.error('Migration error:', err)
                }
            }
            if (next) {
                redirectTo.pathname = next
            }
            return NextResponse.redirect(redirectTo)
        } else {
            console.error('Auth Code Exchange Error:', error)
            redirectTo.pathname = '/auth/error'
            redirectTo.searchParams.set('error', error?.message || 'Unknown error')
            return NextResponse.redirect(redirectTo)
        }
    }

    if (token_hash && type) {
        const supabase = await createClient()

        const { error, data } = await supabase.auth.verifyOtp({
            type,
            token_hash,
        })
        if (!error && data?.user) {
            // Trigger migration for email verification
            const guestId = request.cookies.get('pendingMigrationGuestId')?.value
            if (guestId) {
                try {
                    await fetch('http://localhost:8000/v1/guest/migrate/' + guestId, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ authenticated_user_id: data.user.id }),
                    })
                    // Mark migration as done
                    redirectTo.searchParams.set('migrated', 'true')
                } catch (err) {
                    console.error('Migration error:', err)
                }
            }
            redirectTo.searchParams.delete('next')
            return NextResponse.redirect(redirectTo)
        } else {
            console.error('Auth Verify OTP Error:', error)
            redirectTo.pathname = '/auth/error'
            redirectTo.searchParams.set('error', error?.message || 'Unknown error')
            return NextResponse.redirect(redirectTo)
        }
    }

    // return the user to an error page with some instructions
    redirectTo.pathname = '/auth/error'
    redirectTo.searchParams.set('error', 'Invalid confirmation link (No code or token_hash)')
    return NextResponse.redirect(redirectTo)
}
