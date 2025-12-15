'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card'

interface AuthGateProps {
    feature: 'image' | 'video'
}

export function AuthGate({ feature }: AuthGateProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle className="text-2xl">Sign in required</CardTitle>
                    <CardDescription>
                        {feature === 'image' ? 'Image' : 'Video'} generation is available for authenticated users only
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-4">
                    <p className="text-sm text-muted-foreground">
                        Create a free account to unlock:
                    </p>
                    <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                        <li>Unlimited text generation</li>
                        <li>Image generation</li>
                        <li>Video generation</li>
                        <li>Save your generation history</li>
                    </ul>
                    <div className="flex gap-3 mt-4">
                        <Button asChild className="flex-1">
                            <Link href="/auth/login">Sign In</Link>
                        </Button>
                        <Button asChild variant="outline" className="flex-1">
                            <Link href="/auth/sign-up">Sign Up</Link>
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
