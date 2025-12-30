"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { LinkedInConnection } from '@/components/settings/LinkedInConnection';
import { TwitterConnection } from '@/components/settings/TwitterConnection';
import { Settings } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    userId: string;
}

export function SettingsModal({ isOpen, onClose, userId }: SettingsModalProps) {
    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px] h-[80vh] flex flex-col p-0 gap-0 bg-slate-900 border-slate-800">
                <DialogHeader className="p-6 border-b border-slate-800">
                    <DialogTitle className="flex items-center gap-2 text-white">
                        <Settings className="w-5 h-5 text-blue-500" />
                        Settings
                    </DialogTitle>
                    <DialogDescription className="text-slate-400">
                        Manage your integrations and preferences.
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 flex overflow-hidden">
                    {/* Sidebar (Optional for future expansion) */}
                    <div className="w-48 border-r border-slate-800 bg-slate-900/50 p-4 hidden sm:block">
                        <div className="space-y-1">
                            <button className="w-full text-left px-3 py-2 rounded-lg bg-slate-800 text-white text-sm font-medium">
                                Integrations
                            </button>
                            {/* Add more tabs here later */}
                        </div>
                    </div>

                    {/* Content */}
                    <ScrollArea className="flex-1 p-6">
                        <div className="space-y-8">
                            <section>
                                <h3 className="text-lg font-medium text-white mb-4">Integrations</h3>
                                <div className="space-y-6">
                                    <LinkedInConnection userId={userId} />
                                    <TwitterConnection userId={userId} />
                                </div>
                            </section>
                        </div>
                    </ScrollArea>
                </div>
            </DialogContent>
        </Dialog>
    );
}
