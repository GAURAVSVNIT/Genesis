'use client'

import { useState, useCallback, useEffect } from 'react'
import { CKEditor, useCKEditorCloud } from '@ckeditor/ckeditor5-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { X, Save, RotateCcw, Share2, Linkedin, Twitter } from 'lucide-react'
import { ShareSocialModal } from '@/components/blog/ShareSocialModal'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'

interface SidebarEditorProps {
    initialData: string
    onSave: (content: string) => Promise<void>
    onClose: () => void
    title?: string
    userId: string
}

export function SidebarEditor({ initialData, onSave, onClose, title = 'Edit Content', userId }: SidebarEditorProps) {
    const [content, setContent] = useState(initialData)
    const [isSaving, setIsSaving] = useState(false)
    const [imagePosition, setImagePosition] = useState('inline')
    const [textColor, setTextColor] = useState('black')
    const [backgroundColor, setBackgroundColor] = useState('white')
    const [isDirty, setIsDirty] = useState(false)
    const [editor, setEditor] = useState<any>(null)

    // Share State
    const [isShareModalOpen, setIsShareModalOpen] = useState(false)
    const [sharePlatform, setSharePlatform] = useState<'linkedin' | 'twitter'>('linkedin')

    const openShareModal = (platform: 'linkedin' | 'twitter') => {
        setSharePlatform(platform)
        setIsShareModalOpen(true)
    }

    const cloud = useCKEditorCloud({
        version: '44.1.0',
        premium: true
    })

    // Update content when initialData changes (e.g., when switching between messages or modifications)
    useEffect(() => {
        setContent(initialData)
        setIsDirty(false)
    }, [initialData])

    // Update editor data when content changes externally
    useEffect(() => {
        if (editor && editor.getData() !== content) {
            editor.setData(content)
        }
    }, [editor, content])

    const handleSave = useCallback(async () => {
        setIsSaving(true)
        try {
            await onSave(content)
            setIsDirty(false)
        } catch (error) {
            console.error('Save failed:', error)
        } finally {
            setIsSaving(false)
        }
    }, [content, onSave])

    const handleReset = () => {
        setContent(initialData)
        setIsDirty(false)
    }

    const applyTextColor = (color: string) => {
        if (editor) {
            setTextColor(color)
            // Map color names to hex values
            const colorMap: Record<string, string> = {
                'black': '#000000',
                'slate-700': '#374151',
                'blue-600': '#2563eb',
                'red-600': '#dc2626',
                'green-600': '#16a34a',
                'purple-600': '#7c3aed'
            }
            const hexColor = colorMap[color] || color
            editor.execute('fontColor', { value: hexColor })
        }
    }

    const applyBackgroundColor = (color: string) => {
        if (editor) {
            setBackgroundColor(color)
            // Map color names to hex values
            const colorMap: Record<string, string> = {
                'white': '#ffffff',
                'slate-100': '#f3f4f6',
                'blue-50': '#eff6ff',
                'yellow-50': '#fffbeb',
                'green-50': '#f0fdf4',
                'purple-50': '#faf5ff'
            }
            const hexColor = colorMap[color] || color
            editor.execute('fontBackgroundColor', { value: hexColor })
        }
    }

    const applyImagePosition = (position: string) => {
        if (editor) {
            setImagePosition(position)
            const imageCommand: Record<string, string> = {
                'inline': 'imageStyle:full',
                'left': 'imageStyle:alignLeft',
                'center': 'imageStyle:alignCenter',
                'right': 'imageStyle:alignRight',
                'full': 'imageStyle:full'
            }
            const command = imageCommand[position]
            if (command && editor.commands.get(command)) {
                editor.execute(command)
            }
        }
    }

    if (cloud.status === 'error') {
        return (
            <div className="flex flex-col h-full bg-red-50 p-4">
                <div className="text-red-500 mb-4">Error loading editor!</div>
                <Button variant="outline" onClick={onClose} className="ml-auto">
                    <X className="w-4 h-4" />
                </Button>
            </div>
        )
    }

    if (cloud.status === 'loading') {
        return (
            <div className="flex flex-col h-full bg-slate-50 p-4">
                <div className="text-slate-400 mb-4">Loading editor...</div>
            </div>
        )
    }

    const {
        ClassicEditor,
        Essentials,
        Clipboard,
        Paragraph,
        Bold,
        Italic,
        Underline,
        Strikethrough,
        Code,
        CodeBlock,
        List,
        ListProperties,
        Heading,
        HeadingButtonsUI,
        Link,
        AutoLink,
        BlockQuote,
        Undo,
        Indent,
        IndentBlock,
        Image,
        ImageCaption,
        ImageStyle,
        ImageToolbar,
        ImageResize,
        Table,
        TableToolbar,
        TableProperties,
        TableCellProperties,
        Font,
        FontColor,
        FontBackgroundColor,
        FontFamily,
        FontSize,
        Highlight,
        Alignment,
        HtmlEmbed,
        SourceEditing,
        TextTransformation,
        MediaEmbed,
        Markdown,
        ImageUpload,
        Base64UploadAdapter
    } = cloud.CKEditor

    return (
        <div className="flex flex-col h-full bg-background/95 backdrop-blur-md border-l border-border/50 shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border/50 bg-background/50 backdrop-blur-sm">
                <h3 className="font-medium text-lg text-foreground tracking-tight pl-2">{title}</h3>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="h-8 w-8 p-0 hover:bg-white/10 text-muted-foreground hover:text-foreground transition-all rounded-lg"
                >
                    <X className="w-4 h-4" />
                </Button>
            </div>

            {/* Toolbar Options */}
            <div className="p-4 border-b border-border/50 space-y-4 bg-background/50 backdrop-blur-sm">
                <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide block mb-2 pl-1">
                        Image Position
                    </label>
                    <Select value={imagePosition} onValueChange={applyImagePosition}>
                        <SelectTrigger className="h-9 text-xs bg-secondary/30 border border-border/50 text-foreground hover:bg-secondary/50 focus:ring-0 rounded-lg">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="backdrop-blur-xl bg-popover/90 border-border/50">
                            <SelectItem value="inline">Inline</SelectItem>
                            <SelectItem value="left">Left Align</SelectItem>
                            <SelectItem value="center">Center</SelectItem>
                            <SelectItem value="right">Right Align</SelectItem>
                            <SelectItem value="full">Full Width</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide block mb-2">
                        Text Color
                    </label>
                    <div className="flex gap-2">
                        {['black', 'slate-700', 'blue-600', 'red-600', 'green-600', 'purple-600'].map(color => (
                            <button
                                key={color}
                                className={`w-6 h-6 rounded border-2 transition-all ${textColor === color ? 'border-slate-100 scale-110' : 'border-slate-600'
                                    } bg-${color === 'black' ? 'black' : color}`}
                                onClick={() => applyTextColor(color)}
                                title={color}
                            />
                        ))}
                    </div>
                </div>

                <div>
                    <label className="text-xs font-semibold text-muted-foreground block mb-2">
                        Background Color
                    </label>
                    <div className="flex gap-2">
                        {['white', 'slate-100', 'blue-50', 'yellow-50', 'green-50', 'purple-50'].map(color => (
                            <button
                                key={color}
                                className={`w-6 h-6 rounded border-2 transition-all ${backgroundColor === color ? 'border-slate-100 scale-110' : 'border-slate-600'
                                    } bg-${color}`}
                                onClick={() => applyBackgroundColor(color)}
                                title={color}
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Editor */}
            <div className="flex-1 overflow-y-auto bg-background custom-scrollbar">
                <div
                    className="p-4 text-foreground min-h-full"
                    style={{
                        color: 'var(--foreground)',
                        backgroundColor: 'transparent'
                    }}
                >
                    <CKEditor
                        editor={ClassicEditor}
                        data={content}
                        config={{
                            licenseKey: 'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3OTc3MjQ3OTksImp0aSI6ImRmNzA5ZDc5LTZiMzAtNGRjYi04MzFkLWNiOWU3MGM5ZmVmOSIsImxpY2Vuc2VkSG9zdHMiOlsiMTI3LjAuMC4xIiwibG9jYWxob3N0IiwiMTkyLjE2OC4qLioiLCIxMC4qLiouKiIsIjE3Mi4qLiouKiIsIioudGVzdCIsIioubG9jYWxob3N0IiwiKi5sb2NhbCJdLCJ1c2FnZUVuZHBvaW50IjoiaHR0cHM6Ly9wcm94eS1ldmVudC5ja2VkaXRvci5jb20iLCJkaXN0cmlidXRpb25DaGFubmVsIjpbImNsb3VkIiwiZHJ1cGFsIl0sImxpY2Vuc2VUeXBlIjoiZGV2ZWxvcG1lbnQiLCJmZWF0dXJlcyI6WyJEUlVQIiwiRTJQIiwiRTJXIl0sInJlbW92ZUZlYXR1cmVzIjpbIlBCIiwiUkYiLCJTQ0giLCJUQ1AiLCJUTCIsIlRDUiIsIklSIiwiU1VBIiwiQjY0QSIsIkxQIiwiSEUiLCJSRUQiLCJQRk8iLCJXQyIsIkZBUiIsIkJLTSIsIkZQSCIsIk1SRSJdLCJ2YyI6IjQxNDllYzRiIn0.rVAFEwnSsbW_lZRcKsFVp4tMpeOB3sDGVlNYUX_f5Fwc2TEguS8t8RHi1L9F_jdqHp3InadZKeFRo6BNXodk4A',
                            plugins: [
                                Essentials,
                                Clipboard,
                                Paragraph,
                                Bold,
                                Italic,
                                Underline,
                                Strikethrough,
                                Code,
                                CodeBlock,
                                List,
                                ListProperties,
                                Heading,
                                HeadingButtonsUI,
                                Link,
                                AutoLink,
                                BlockQuote,
                                Undo,
                                Indent,
                                IndentBlock,
                                Image,
                                ImageCaption,
                                ImageStyle,
                                ImageToolbar,
                                ImageResize,
                                Table,
                                TableToolbar,
                                TableProperties,
                                TableCellProperties,
                                Font,
                                FontColor,
                                FontBackgroundColor,
                                FontFamily,
                                FontSize,
                                Highlight,
                                Alignment,
                                HtmlEmbed,
                                SourceEditing,
                                TextTransformation,
                                MediaEmbed,
                                Markdown,
                                ImageUpload,
                                Base64UploadAdapter
                            ],
                            toolbar: {
                                items: [
                                    'undo', '|',
                                    'heading', '|',
                                    'bold', 'italic', 'underline', 'strikethrough', 'code', '|',
                                    'fontFamily', 'fontSize', '|',
                                    'fontColor', 'fontBackgroundColor', 'highlight', '|',
                                    'alignment', '|',
                                    'bulletedList', 'numberedList', 'outdent', 'indent', '|',
                                    'link', 'uploadImage', 'mediaEmbed', 'insertTable', 'blockQuote', 'codeBlock', '|',
                                    'sourceEditing'
                                ],
                                shouldNotGroupWhenFull: true
                            },
                            table: {
                                contentToolbar: [
                                    'tableColumn',
                                    'tableRow',
                                    'mergeTableCells',
                                    'tableProperties',
                                    'tableCellProperties'
                                ]
                            },
                            image: {
                                resizeOptions: [
                                    {
                                        name: 'resizeImage:original',
                                        label: 'Original',
                                        value: null
                                    },
                                    {
                                        name: 'resizeImage:50',
                                        label: '50%',
                                        value: '50'
                                    },
                                    {
                                        name: 'resizeImage:75',
                                        label: '75%',
                                        value: '75'
                                    },
                                    {
                                        name: 'resizeImage:100',
                                        label: '100%',
                                        value: '100'
                                    }
                                ],
                                toolbar: [
                                    'imageTextAlternative',
                                    'imageStyle:alignLeft',
                                    'imageStyle:alignCenter',
                                    'imageStyle:alignRight',
                                    '|',
                                    'resizeImage'
                                ]
                            },
                            fontSize: {
                                options: [10, 12, 14, 'default', 18, 20, 22, 24, 26, 28, 30, 32]
                            },
                            fontFamily: {
                                options: [
                                    'default',
                                    'Arial, Helvetica, sans-serif',
                                    'Courier New, Courier, monospace',
                                    'Georgia, serif',
                                    'Lucida Console, Courier New, monospace',
                                    'Tahoma, Geneva, sans-serif',
                                    'Times New Roman, Times, serif',
                                    'Trebuchet MS, sans-serif',
                                    'Verdana, Geneva, sans-serif'
                                ]
                            },
                            heading: {
                                options: [
                                    { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
                                    { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
                                    { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
                                    { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
                                    { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' }
                                ]
                            }
                        }}
                        onChange={(event, editorInstance) => {
                            const data = editorInstance.getData()
                            setContent(data)
                            setIsDirty(true)
                            // Store editor reference for applying colors and styles
                            if (!editor) {
                                setEditor(editorInstance)
                            }
                        }}
                    />
                </div>
            </div>

            {/* Footer Actions */}
            <div className="flex gap-2 p-4 border-t border-border/50 bg-background/50 backdrop-blur-sm">
                <Button
                    onClick={handleReset}
                    variant="outline"
                    size="sm"
                    disabled={!isDirty || isSaving}
                    className="flex-1 bg-transparent hover:bg-destructive/10 text-destructive/80 hover:text-destructive border border-destructive/30 hover:border-destructive/50 rounded-lg transition-all"
                >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                </Button>

                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button
                            variant="secondary"
                            size="sm"
                            className="flex-1 bg-secondary/50 hover:bg-secondary/80 text-secondary-foreground border border-transparent rounded-lg"
                        >
                            <Share2 className="w-4 h-4 mr-2" />
                            Share
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="bg-popover/90 border-border/50 backdrop-blur-xl">
                        <DropdownMenuItem onClick={() => openShareModal('linkedin')} className="text-slate-200 hover:bg-white/10 cursor-pointer">
                            <Linkedin className="w-4 h-4 mr-2 text-[#0077b5]" />
                            Share to LinkedIn
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => openShareModal('twitter')} className="text-slate-200 hover:bg-white/10 cursor-pointer">
                            <Twitter className="w-4 h-4 mr-2 text-sky-500" />
                            Share to X (Twitter)
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>

                <Button
                    onClick={handleSave}
                    size="sm"
                    disabled={!isDirty || isSaving}
                    className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20 hover:shadow-primary/40 rounded-lg border border-white/10 transition-all font-medium"
                >
                    <Save className="w-4 h-4 mr-2" />
                    {isSaving ? 'Saving...' : 'Save Changes'}
                </Button>
            </div>

            <ShareSocialModal
                isOpen={isShareModalOpen}
                onClose={() => setIsShareModalOpen(false)}
                userId={userId}
                initialContent={content}
                blogTitle={title}
                platform={sharePlatform}
            />

            <style jsx global>{`
                .ck-editor__main {
                    background-color: transparent !important;
                }

                .ck.ck-editor__editable {
                    background-color: transparent !important;
                    color: var(--foreground) !important;
                }

                .ck.ck-content {
                    background-color: transparent !important;
                    color: var(--foreground) !important;
                }

                .ck-editor__top,
                .ck-toolbar {
                    background-color: hsl(var(--card)) !important;
                    border-bottom-color: var(--border) !important;
                    position: sticky !important;
                    top: 0;
                    z-index: 50 !important;
                    overflow: visible !important;
                }

                .ck-toolbar__items {
                    overflow: visible !important;
                }

                .ck-toolbar__separator {
                    background-color: var(--border) !important;
                }

                .ck-button,
                .ck.ck-button {
                    background-color: transparent !important;
                    color: var(--muted-foreground) !important;
                    border-color: transparent !important;
                }

                .ck-button:hover:not(:disabled),
                .ck.ck-button:hover:not(:disabled) {
                    background-color: var(--accent) !important;
                    color: var(--accent-foreground) !important;
                }

                .ck-button.ck-on,
                .ck.ck-button.ck-on {
                    background-color: var(--primary) !important;
                    color: var(--primary-foreground) !important;
                }

                .ck-button:active,
                .ck.ck-button:active {
                    background-color: var(--primary) !important;
                }

                .ck.ck-editor__editable.ck-focused {
                    border-color: var(--primary) !important;
                    box-shadow: 0 0 0 2px var(--ring) !important;
                }

                .ck-editor__editable p {
                    color: var(--foreground) !important;
                }

                .ck-editor__editable a {
                    color: var(--primary) !important;
                }

                .ck-editor__editable blockquote {
                    border-left-color: var(--primary) !important;
                    color: var(--muted-foreground) !important;
                    background-color: var(--card) !important;
                    padding: 0.5rem 1rem;
                }

                .ck-editor__editable code {
                    background-color: var(--muted) !important;
                    color: var(--destructive) !important;
                    padding: 0.125rem 0.25rem;
                    border-radius: 0.25rem;
                }

                .ck-dropdown__panel,
                .ck.ck-panel,
                .ck.ck-balloon-panel {
                    background-color: var(--popover) !important;
                    border-color: var(--border) !important;
                    color: var(--foreground) !important;
                    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.5) !important;
                    z-index: 99999 !important;
                }

                .ck-dropdown__panel-visible,
                .ck.ck-panel.ck-panel_visible,
                .ck.ck-balloon-panel.ck-balloon-panel_visible {
                    background-color: var(--popover) !important;
                }

                .ck.ck-list__item,
                .ck.ck-list__item .ck-button {
                    background-color: transparent !important;
                    color: var(--foreground) !important;
                    width: 100%;
                }

                .ck.ck-list__item .ck-button .ck-button__label {
                    color: var(--foreground) !important;
                }

                .ck.ck-list__item .ck-button:hover:not(.ck-disabled),
                .ck.ck-list__item:hover:not(.ck-disabled) {
                    background-color: var(--accent) !important;
                    color: var(--accent-foreground) !important;
                }

                .ck.ck-list__item .ck-button:hover .ck-button__label {
                    color: var(--accent-foreground) !important;
                }

                .ck.ck-list__item .ck-button.ck-on,
                .ck.ck-list__item .ck-button.ck-on:hover:not(.ck-disabled) {
                    background-color: var(--primary) !important;
                    color: var(--primary-foreground) !important;
                }

                .ck.ck-list__item .ck-button.ck-on .ck-button__label {
                    color: var(--primary-foreground) !important;
                }

                .ck-image-upload-complete-message {
                    background-color: var(--card) !important;
                    color: var(--card-foreground) !important;
                }

                /* Ensure portaled elements are on top */
                .ck-body-wrapper {
                    z-index: 99999 !important;
                    position: absolute;
                }
            `}</style>
        </div>
    )
}

export default SidebarEditor
