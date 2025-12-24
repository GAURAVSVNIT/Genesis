'use client'

import { useEffect } from 'react'

/**
 * Initialize guest session on first visit
 * Generates and stores guest ID in localStorage
 */
export function GuestSessionInit() {
    useEffect(() => {
        // Only run on client
        if (typeof window === 'undefined') return

        // Check if guest ID exists
        const existingGuestId = localStorage.getItem('guestId')

        if (!existingGuestId) {
            // Generate new guest ID
            const newGuestId = crypto.randomUUID()
            localStorage.setItem('guestId', newGuestId)
            console.log('🆔 Generated new guest ID:', newGuestId)
        } else {
            console.log('🆔 Using existing guest ID:', existingGuestId)
        }
    }, [])

    // This component doesn't render anything
    return null
}
