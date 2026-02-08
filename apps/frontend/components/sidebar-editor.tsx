'use client'

import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
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

import { ImageControls } from './image-controls'

interface SidebarEditorProps {
    initialData: string
    onSave: (content: string) => Promise<void>
    onClose: () => void
    title?: string
    userId: string
    imageUrl?: string | null
}

export function SidebarEditor({ initialData, onSave, onClose, title = 'Edit Content', userId, imageUrl: initialImageUrl }: SidebarEditorProps) {
    // Inject image into content if provided, placing it after the first header
    const injectImage = useCallback((content: string, imgUrl: string) => {
        if (content.includes(imgUrl)) return content

        // Check for HTML header
        const htmlHeaderRegex = /(<h[1-2][^>]*>.*?<\/h[1-2]>)/i
        const htmlMatch = content.match(htmlHeaderRegex)

        // Check for Markdown header (# Title or ## Title)
        const mdHeaderRegex = /(^#{1,2}\s+.*$)/m
        const mdMatch = content.match(mdHeaderRegex)

        const imageHtml = `<figure class="image"><img src="${imgUrl}" alt="Blog Header"></figure>`
        const imageMd = `\n\n![Blog Header](${imgUrl})\n\n`

        // Handle HTML content
        if (htmlMatch) {
            return content.replace(htmlHeaderRegex, `$1${imageHtml}`)
        }

        // Handle Handle Markdown content
        if (mdMatch) {
            return content.replace(mdHeaderRegex, `$1${imageMd}`)
        }

        // Fallback: Prepend
        return content.trim().startsWith('<')
            ? `${imageHtml}${content}`
            : `${imageMd}${content}`
    }, [])

    const [isSaving, setIsSaving] = useState(false)
    const [isDirty, setIsDirty] = useState(false)
    const [editor, setEditor] = useState<{
        setData: (data: string) => void
        getData: () => string
    } | null>(null)

    // Track the current image URL separately to pass to controls
    const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(initialImageUrl || null)

    const contentWithImage = useMemo(() => {
        if (initialImageUrl) {
            return injectImage(initialData, initialImageUrl)
        }
        return initialData
    }, [initialData, initialImageUrl, injectImage])

    const [content, setContent] = useState(contentWithImage)

    // Handle Image Updates from Controls
    const handleImageUpdate = useCallback((newUrl: string | null) => {
        setCurrentImageUrl(newUrl)

        let newContent = content

        // Regex to find existing images (Markdown or HTML) - now more flexible for extra classes
        const imgRegex = /(!\[[\s\S]*?\]\([\s\S]*?\))|(<figure\s+[^>]*class="[^"]*image[^"]*"[^>]*>[\s\S]*?<\/figure>)|(<img[^>]+src="([^">]+)"[^>]*>)/g

        console.log('[SidebarEditor] Current content length:', content.length)
        console.log('[SidebarEditor] Regex test:', imgRegex.test(content))
        // Reset regex lastIndex after test()
        imgRegex.lastIndex = 0

        const matches = content.match(imgRegex)
        console.log('[SidebarEditor] Found matches:', matches)

        if (!newUrl) {
            // REMOVE: Strip all images
            newContent = newContent.replace(imgRegex, '')
            console.log('[SidebarEditor] Removed images. New content length:', newContent.length)
        } else {
            // ADD / REPLACE
            if (imgRegex.test(newContent)) {
                // Reset regex lastIndex after test()
                imgRegex.lastIndex = 0
                // Replace existing
                newContent = newContent.replace(imgRegex, '')
                newContent = injectImage(newContent, newUrl)
            } else {
                // Add new
                newContent = injectImage(newContent, newUrl)
            }
        }

        setContent(newContent)
        // Update editor if instance is ready
        if (editor) {
            editor.setData(newContent)
        }
    }, [content, editor, injectImage])

    // Track previous initialImageUrl to detect external changes
    const prevInitialImageUrlRef = useRef(initialImageUrl)

    // Effect to handle external image updates ONLY when the prop changes
    useEffect(() => {
        if (initialImageUrl !== prevInitialImageUrlRef.current) {
            prevInitialImageUrlRef.current = initialImageUrl
            if (initialImageUrl) {
                handleImageUpdate(initialImageUrl)
            }
        }
    }, [initialImageUrl, handleImageUpdate])

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

    // Update editor data when content changes externally
    useEffect(() => {
        if (editor && editor.getData() !== content) {
            setTimeout(() => {
                editor.setData(content)
            }, 0)
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
                <h3 className="font-medium text-lg text-foreground tracking-tight pl-2 mr-auto">{title}</h3>
                <div className="flex items-center gap-2">
                    <ImageControls
                        content={content}
                        currentImageUrl={currentImageUrl}
                        onImageUpdate={handleImageUpdate}
                    />

                    <div className="w-px h-6 bg-border/40 mx-1"></div>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onClose}
                        className="h-8 w-8 p-0 hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-all rounded-lg"
                    >
                        <X className="w-4 h-4" />
                    </Button>
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
                            licenseKey: 'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3OTk0NTI3OTksImp0aSI6IjQ1Nzc4ZGNkLTFhZWItNDU3MS05NWVmLWJhYjJjMWI1ODUxNiIsInVzYWdlRW5kcG9pbnQiOiJodHRwczovL3Byb3h5LWV2ZW50LmNrZWRpdG9yLmNvbSIsImRpc3RyaWJ1dGlvbkNoYW5uZWwiOlsiY2xvdWQiLCJkcnVwYWwiXSwiZmVhdHVyZXMiOlsiRFJVUCIsIkUyUCIsIkUyVyJdLCJyZW1vdmVGZWF0dXJlcyI6WyJQQiIsIlJGIiwiU0NIIiwiVENQIiwiVEwiLCJUQ1IiLCJJUiIsIlNVQSIsIkI2NEEiLCJMUCIsIkhFIiwiUkVEIiwiUEZPIiwiV0MiLCJGQVIiLCJCS00iLCJGUEgiLCJNUkUiXSwidmMiOiI5ZWZiZjY0ZSJ9.mx4I_HNQu5MH_Rt2fak8nFFTeF-SFLXlC_FFgO_jQ2bfdjuyCUEQ02bvXM2ixV6ujmmJLzu6GobkMC9j3deDSQ',
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
                                    'undo', 'redo', '|',
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
                        onReady={(editorInstance) => {
                            setEditor(editorInstance)
                        }}
                        onChange={(event, editorInstance) => {
                            const data = editorInstance.getData()
                            setContent(data)
                            setIsDirty(true)
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
                    color: var(--foreground);
                }

                .ck.ck-content {
                    background-color: transparent !important;
                    color: var(--foreground);
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
                    color: var(--foreground);
                }

                .ck-editor__editable a {
                    color: var(--primary) !important;
                }

                .ck-editor__editable blockquote {
                    border-left-color: var(--primary) !important;
                    color: var(--muted-foreground);
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
