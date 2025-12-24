'use client'

import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function SignupMigrationHandler() {
    const searchParams = useSearchParams()
    const hasShown = useRef(false)
    const [showNotification, setShowNotification] = useState(false)

    useEffect(() => {
        if (hasShown.current) return
        
        // Check if migration happened during signup confirmation
        const migrated = searchParams.get('migrated')
        
        if (migrated === 'true') {
            hasShown.current = true
            setShowNotification(true)
            console.log('SignupMigrationHandler: Migration notification shown')
            
            // Auto-hide after 6 seconds
            setTimeout(() => {
                setShowNotification(false)
            }, 6000)
        }
    }, [searchParams])

    if (!showNotification) return null

    return (
        <div className="fixed top-4 right-4 z-50">
            <Card className="bg-green-50 border-green-200 shadow-lg max-w-md">
                <div className="p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                            <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-green-900">
                                ✅ Welcome! Your guest conversations have been transferred to your account!
                            </p>
                        </div>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowNotification(false)}
                        className="text-green-600 hover:text-green-700 hover:bg-green-100"
                    >
                        ✕
                    </Button>
                </div>
            </Card>
        </div>
    )
}
