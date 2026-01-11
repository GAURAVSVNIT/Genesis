"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

import { createPortal } from "react-dom"

const Dialog = ({
    open,
    onOpenChange,
    children,
}: {
    open?: boolean
    onOpenChange?: (open: boolean) => void
    children: React.ReactNode
}) => {
    const [mounted, setMounted] = React.useState(false)

    React.useEffect(() => {
        setMounted(true)
        return () => setMounted(false)
    }, [])

    if (!open || !mounted) return null

    return createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
                onClick={() => onOpenChange?.(false)}
            />
            {/* Content Container */}
            <div className="relative z-[101] w-full pointer-events-none flex justify-center p-4">
                {/* pointer-events-auto is needed on the content itself, handled by DialogContent usually but let's be safe */}
                {children}
            </div>
        </div>,
        document.body
    )
}

const DialogContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement> & { className?: string }
>(({ className, children, ...props }, ref) => {
    // We need access to onOpenChange to close it via [X] button, but context is overkill for this simple file.
    // We'll rely on the parent rendering this to handle closure via backdrop or internal buttons.
    // Ideally we'd use Context, but let's keep it simple. User can pass onClose to this if needed or just put Button inside.
    // Actually, Radix/Shadcn structure usually implies Context.
    // Let's implement a tiny Context.
    return (
        <div
            ref={ref}
            className={cn(
                "relative w-full max-w-lg mx-auto gap-4 border border-slate-800 bg-slate-900 p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg pointer-events-auto",
                className
            )}
            {...props}
        >
            {children}
            {/* Close Button is usually separate or passed down. We'll skip auto-close button for now or add it if we had context. */}
        </div>
    )
})
DialogContent.displayName = "DialogContent"

const DialogHeader = ({
    className,
    ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
    <div
        className={cn(
            "flex flex-col space-y-1.5 text-center sm:text-left",
            className
        )}
        {...props}
    />
)
DialogHeader.displayName = "DialogHeader"

const DialogFooter = ({
    className,
    ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
    <div
        className={cn(
            "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
            className
        )}
        {...props}
    />
)
DialogFooter.displayName = "DialogFooter"

const DialogTitle = React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
    <h3
        ref={ref}
        className={cn(
            "text-lg font-semibold leading-none tracking-tight text-slate-100",
            className
        )}
        {...props}
    />
))
DialogTitle.displayName = "DialogTitle"

const DialogDescription = React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
    <p
        ref={ref}
        className={cn("text-sm text-slate-400", className)}
        {...props}
    />
))
DialogDescription.displayName = "DialogDescription"

export {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogFooter,
    DialogTitle,
    DialogDescription,
}
