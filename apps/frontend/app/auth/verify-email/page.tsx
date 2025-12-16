export default function VerifyEmailPage() {
    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="max-w-md w-full space-y-8 text-center">
                <div className="space-y-4">
                    <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                        <svg
                            className="w-8 h-8 text-primary"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                            />
                        </svg>
                    </div>

                    <h1 className="text-3xl font-bold">Check your email</h1>

                    <p className="text-muted-foreground">
                        We've sent you a verification link. Please check your email and click the link to complete your signup.
                    </p>

                    <div className="pt-4 space-y-2">
                        <p className="text-sm text-muted-foreground">
                            Didn't receive the email?
                        </p>
                        <p className="text-xs text-muted-foreground">
                            Check your spam folder or contact support
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
