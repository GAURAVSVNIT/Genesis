"use client";

import { useState, useEffect } from 'react';
import { socialApi } from '@/lib/api/social';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Send, Linkedin, Twitter } from 'lucide-react';
import { toast } from 'sonner';

interface ShareSocialModalProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string;
    initialContent: string;
    blogTitle?: string;
    blogUrl?: string;
    platform: 'linkedin' | 'twitter';
}

interface Target {
    urn: string;
    name: string;
    type: string;
}

export function ShareSocialModal({
    isOpen,
    onClose,
    userId,
    initialContent,
    blogTitle,
    blogUrl,
    platform
}: ShareSocialModalProps) {
    const [content, setContent] = useState(initialContent);
    const [isLoading, setIsLoading] = useState(false);
    const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
    const [errorMessage, setErrorMessage] = useState('');

    // Target Selection State (LinkedIn Only currently)
    const [targets, setTargets] = useState<Target[]>([]);
    const [selectedTarget, setSelectedTarget] = useState<string>("");
    const [isLoadingTargets, setIsLoadingTargets] = useState(false);

    const [targetsError, setTargetsError] = useState<string | null>(null);

    const isTwitter = platform === 'twitter';
    const maxLength = isTwitter ? 280 : 3000;
    const remainingChars = maxLength - content.length;

    // Fetch targets when modal opens (only for LinkedIn)
    useEffect(() => {
        if (isOpen && userId && platform === 'linkedin') {
            setIsLoadingTargets(true);
            setTargetsError(null);
            socialApi.getLinkedInTargets(userId)
                .then(data => {
                    setTargets(data);
                    if (data.length > 0 && !selectedTarget) {
                        setSelectedTarget(data[0].urn);
                    } else if (data.length > 0 && selectedTarget) {
                        const exists = data.find(t => t.urn === selectedTarget);
                        if (!exists) setSelectedTarget(data[0].urn);
                    }
                })
                .catch(err => {
                    console.error("Failed to fetch targets", err);
                    setTargetsError("Failed to load accounts. Please check your LinkedIn connection.");
                })
                .finally(() => setIsLoadingTargets(false));
        }
    }, [isOpen, userId, platform]);


    // Helper to convert HTML to plain text
    const stripHtml = (html: string): string => {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || '';
    };

    const handleShare = async () => {
        setIsLoading(true);
        setStatus('idle');
        try {
            // Strip HTML for social platforms (they expect plain text)
            let plainTextContent = stripHtml(content);

            // Truncate to platform limit (LinkedIn: 3000, Twitter: 280)
            const limit = isTwitter ? 280 : 3000;
            if (plainTextContent.length > limit) {
                plainTextContent = plainTextContent.substring(0, limit - 3) + '...';
            }

            await socialApi.shareContent(userId, platform, plainTextContent, blogUrl, blogTitle, selectedTarget);
            // Note: `shareToLinkedIn` is a misnomer in API client if we misuse it, 
            // but the backend `share_content` endpoint handles generic platforms. 
            // We should ideally rename `shareToLinkedIn` to `shareContent` in client,
            // but for now we pass the right props. 
            // WAIT - the current client method hardcodes 'linkedin'. We need to fix that or use a new method.
            // Let's assume we will refactor the client method briefly or add a new one. 
            // Actually, let's fix the client method in the next step. 
            // For now, I'll use a new generic method call structure assuming I update api.ts next.

            // Correction: I haven't updated api.ts to be generic yet, it was `shareToLinkedIn`.
            // I will update the API client to have a generic `share` method.

            setStatus('success');
            setTimeout(() => {
                onClose();
                setStatus('idle');
            }, 2000);
        } catch (error: any) {
            console.error(error);
            setStatus('error');
            setErrorMessage(error.response?.data?.detail || "Failed to share post.");
        } finally {
            setIsLoading(false);
        }
    };

    // Temporary fix until client update:
    // We need to call a generic share endpoint. I'll implement `handleShare` assuming the client is fixed.

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-700 shadow-xl z-50">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2 capitalize">
                        {platform === 'linkedin' && <Linkedin className="w-5 h-5 text-[#0077b5]" />}
                        {platform === 'twitter' && <Twitter className="w-5 h-5 text-sky-500" />}
                        Share to {platform}
                    </DialogTitle>
                    <DialogDescription>
                        Draft your post for {platform}.
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
                            {/* Loading State */}
                            {isLoadingTargets && platform === 'linkedin' && (
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    <span>Loading accounts...</span>
                                </div>
                            )}

                            {/* Error State */}
                            {targetsError && platform === 'linkedin' && (
                                <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-600">
                                    {targetsError}
                                </div>
                            )}

                            {/* Target Selector (LinkedIn Only) */}
                            {platform === 'linkedin' && targets.length > 0 && !isLoadingTargets && (
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Post As</label>
                                    <Select
                                        value={selectedTarget}
                                        onValueChange={setSelectedTarget}
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
                                <div className="flex justify-between items-center">
                                    <label className="text-sm font-medium">Post Content</label>
                                    <div className="flex items-center gap-2">
                                        {remainingChars < 0 && (
                                            <Button 
                                                variant="ghost" 
                                                size="sm" 
                                                className="h-7 px-2 text-[10px] text-red-600 hover:text-red-700 hover:bg-red-50 bg-red-50/50"
                                                onClick={() => setContent(content.substring(0, maxLength))}
                                            >
                                                Trim Content
                                            </Button>
                                        )}
                                        <span className={`text-xs ${remainingChars < 0 ? 'text-red-500 font-bold' : 'text-muted-foreground'}`}>
                                            {remainingChars} chars left
                                        </span>
                                    </div>
                                </div>
                                <Textarea
                                    value={content}
                                    onChange={(e) => setContent(e.target.value)}
                                    className={`min-h-[150px] ${remainingChars < 0 ? 'border-red-200 focus-visible:ring-red-500' : ''}`}
                                    placeholder={isTwitter ? "What's happening?" : "What do you want to talk about?"}
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
                        <Button onClick={handleShare} disabled={isLoading || !content.trim() || (isTwitter && remainingChars < 0)}>
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Post
                        </Button>
                    </DialogFooter>
                )}
            </DialogContent>
        </Dialog>
    );
}
