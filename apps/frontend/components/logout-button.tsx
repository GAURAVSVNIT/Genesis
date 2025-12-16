'use client'

import { createClient } from '@/lib/supabase/client'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export function LogoutButton() {
    const [isLoading, setIsLoading] = useState(false)
    const router = useRouter()

    const handleLogout = async () => {
        setIsLoading(true)
        const supabase = createClient()

        try {
            await supabase.auth.signOut()
            router.refresh()
            router.push('/')
        } catch (error) {
            console.error('Error logging out:', error)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Button onClick={handleLogout} disabled={isLoading} variant="outline">
            {isLoading ? 'Logging out...' : 'Logout'}
        </Button>
    )
}
