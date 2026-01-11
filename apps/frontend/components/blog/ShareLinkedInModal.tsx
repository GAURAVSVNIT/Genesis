"use client";

import { useState, useEffect } from 'react';
import { socialApi } from '@/lib/api/social';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Send } from 'lucide-react';


interface ShareLinkedInModalProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string;
    initialContent: string;
    blogTitle?: string;
    blogUrl?: string;
}

interface LinkedInTarget {
    urn: string;
    name: string;
    type: string;
}

export function ShareLinkedInModal({
    isOpen,
    onClose,
    userId,
    initialContent,
    blogTitle,
    blogUrl
}: ShareLinkedInModalProps) {
    const [content, setContent] = useState(initialContent);
    const [isLoading, setIsLoading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    // Target Selection State
    const [targets, setTargets] = useState<LinkedInTarget[]>([]);
    const [selectedTarget, setSelectedTarget] = useState<string>("");
    const [isLoadingTargets, setIsLoadingTargets] = useState(false);

    // Fetch targets when modal opens
    useEffect(() => {
        if (isOpen && userId) {
            setIsLoadingTargets(true);
            socialApi.getLinkedInTargets(userId)
                .then(data => {
                    setTargets(data);
                    // Default to first target (Profile) if no selection yet
                    if (data.length > 0 && !selectedTarget) {
                        setSelectedTarget(data[0].urn);
                    } else if (data.length > 0 && selectedTarget) {
                        // Check if previously selected target is still valid, else default
                        const exists = data.find(t => t.urn === selectedTarget);
                        if (!exists) setSelectedTarget(data[0].urn);
                    }
                })
                .catch(err => {
                    console.error("Failed to fetch LinkedIn targets", err);
                    // Don't show error toast immediately to avoid spam, just log
                })
                .finally(() => setIsLoadingTargets(false));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen, userId]);

    const handleShare = async () => {
        setIsLoading(true);
        setStatus('idle');
        try {
            await socialApi.shareToLinkedIn(userId, content, blogUrl, blogTitle, selectedTarget);
            setStatus('success');
            setTimeout(() => {
                onClose();
                setStatus('idle');
            }, 2000);
        } catch (error: unknown) {
            console.error(error);
            setStatus('error');
            const err = error as { response?: { data?: { detail?: string } } };
            setErrorMessage(err.response?.data?.detail || "Failed to share post.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        Share to LinkedIn
                    </DialogTitle>
                    <DialogDescription>
                        Customize your post before sharing with your network.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {status === 'success' ? (
                        <div className="flex flex-col items-center justify-center py-8 text-green-600">
                            <Send className="h-12 w-12 mb-2" />
                            <p className="font-semibold text-lg">Posted Successfully!</p>
                        </div>
                    ) : (
                        <>
                            {/* Target Selector */}
                            {targets.length > 0 && (
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Post As</label>
                                    <Select
                                        value={selectedTarget}
                                        onValueChange={(v) => setSelectedTarget(v)}
                                        disabled={isLoading || isLoadingTargets}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select Account" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {targets.map(t => (
                                                <SelectItem key={t.urn} value={t.urn}>
                                                    <span className="font-medium">{t.name}</span>
                                                    {t.type === 'organization' && <span className="text-xs text-muted-foreground ml-2">(Company Page)</span>}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                            )}

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Post Content</label>
                                <Textarea
                                    value={content}
                                    onChange={(e) => setContent(e.target.value)}
                                    className="min-h-[150px]"
                                    placeholder="What do you want to talk about?"
                                />
                            </div>

                            {blogUrl && (
                                <div className="p-3 bg-muted rounded-md text-sm text-muted-foreground border">
                                    <strong>Attached Article:</strong> <br />
                                    {blogTitle || blogUrl}
                                </div>
                            )}

                            {status === 'error' && (
                                <p className="text-sm text-red-600">{errorMessage}</p>
                            )}
                        </>
                    )}
                </div>

                {status !== 'success' && (
                    <DialogFooter>
                        <Button variant="outline" onClick={onClose} disabled={isLoading}>
                            Cancel
                        </Button>
                        <Button onClick={handleShare} disabled={isLoading || !content.trim()}>
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Post
                        </Button>
                    </DialogFooter>
                )}
            </DialogContent>
        </Dialog>
    );
}
