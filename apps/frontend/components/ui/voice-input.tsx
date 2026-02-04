'use client'

import { useState, useRef, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { Mic, Loader2, StopCircle } from 'lucide-react'
import { toast } from 'sonner'

interface VoiceInputProps {
    onTranscription: (text: string) => void
    className?: string
    isCompact?: boolean
}

export function VoiceInput({ onTranscription, className, isCompact = false }: VoiceInputProps) {
    const [isRecording, setIsRecording] = useState(false)
    const [isProcessing, setIsProcessing] = useState(false)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const chunksRef = useRef<Blob[]>([])

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const mediaRecorder = new MediaRecorder(stream) // Using default browser codec (usually webm/ogg)

            mediaRecorderRef.current = mediaRecorder
            chunksRef.current = []

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data)
                }
            }

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: mediaRecorder.mimeType })
                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop())

                await handleTranscription(audioBlob)
            }

            mediaRecorder.start()
            setIsRecording(true)
        } catch (error) {
            console.error('Error accessing microphone:', error)
            toast.error("Microphone Access Denied", {
                description: "Please check your browser permissions.",
            })
        }
    }, [])

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop()
            setIsRecording(false)
            setIsProcessing(true)
        }
    }, [isRecording])

    const handleTranscription = async (audioBlob: Blob) => {
        try {
            const formData = new FormData()
            formData.append('audio', audioBlob)

            const response = await fetch('/api/speech-to-text', {
                method: 'POST',
                body: formData,
            })

            const responseText = await response.text()
            let data

            try {
                data = JSON.parse(responseText)
            } catch (e) {
                console.error("Server raw response:", responseText)
                throw new Error(`Server response not JSON: ${responseText.slice(0, 100)}`)
            }

            if (!response.ok) {
                throw new Error(data.error || 'Transcription failed')
            }

            if (data.text) {
                onTranscription(data.text)
                toast.success("Transcription Complete");
            } else {
                toast.warning("No speech detected");
            }

        } catch (error) {
            console.error('Transcription error:', error)
            toast.error("Transcription Failed", {
                description: error instanceof Error ? error.message : "Failed to process audio."
            });
        } finally {
            setIsProcessing(false)
        }
    }

    return (
        <Button
            variant="ghost"
            size={isCompact ? "icon" : "default"}
            className={cn(
                "transition-all duration-300 relative",
                isRecording && "bg-red-500/10 text-red-500 hover:bg-red-500/20 hover:text-red-500 animate-pulse",
                isProcessing && "bg-blue-500/10 text-blue-500 cursor-wait",
                className
            )}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            title={isRecording ? "Stop Recording" : "Start Voice Input"}
        >
            {isProcessing ? (
                <Loader2 className={cn("animate-spin", isCompact ? "w-4 h-4" : "w-5 h-5 mr-2")} />
            ) : isRecording ? (
                <StopCircle className={cn(isCompact ? "w-4 h-4" : "w-5 h-5 mr-2")} />
            ) : (
                <Mic className={cn(isCompact ? "w-4 h-4" : "w-5 h-5 mr-2")} />
            )}

            {!isCompact && (
                <span>
                    {isProcessing ? "Processing..." : isRecording ? "Listening..." : "Voice Input"}
                </span>
            )}
        </Button>
    )
}
