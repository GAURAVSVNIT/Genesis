'use client'

import { useState, useCallback, useEffect } from 'react'
import { CKEditor, useCKEditorCloud } from '@ckeditor/ckeditor5-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { X, Save, RotateCcw } from 'lucide-react'
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
}

export function SidebarEditor({ initialData, onSave, onClose, title = 'Edit Content' }: SidebarEditorProps) {
    const [content, setContent] = useState(initialData)
    const [isSaving, setIsSaving] = useState(false)
    const [imagePosition, setImagePosition] = useState('inline')
    const [textColor, setTextColor] = useState('black')
    const [backgroundColor, setBackgroundColor] = useState('white')
    const [isDirty, setIsDirty] = useState(false)
    const [editor, setEditor] = useState<any>(null)

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
        <div className="flex flex-col h-full bg-slate-900 border-l border-slate-800">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-800/50">
                <h3 className="font-semibold text-lg text-white">{title}</h3>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={onClose}
                    className="h-8 w-8 p-0"
                >
                    <X className="w-4 h-4" />
                </Button>
            </div>

            {/* Toolbar Options */}
            <div className="p-4 border-b border-slate-800 space-y-3 bg-slate-800/50">
                <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-2">
                        Image Position
                    </label>
                    <Select value={imagePosition} onValueChange={applyImagePosition}>
                        <SelectTrigger className="h-8 text-xs bg-slate-800 border-slate-700 text-white">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="inline">Inline</SelectItem>
                            <SelectItem value="left">Left Align</SelectItem>
                            <SelectItem value="center">Center</SelectItem>
                            <SelectItem value="right">Right Align</SelectItem>
                            <SelectItem value="full">Full Width</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                <div>
                    <label className="text-xs font-semibold text-slate-300 block mb-2">
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
                    <label className="text-xs font-semibold text-slate-300 block mb-2">
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
            <ScrollArea className="flex-1 overflow-auto bg-slate-800">
                <div
                    className="p-4 ck-content text-slate-100"
                    style={{
                        color: '#e2e8f0',
                        backgroundColor: '#1e293b'
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
            </ScrollArea>

            {/* Footer Actions */}
            <div className="flex gap-2 p-4 border-t border-slate-800 bg-slate-800/50">
                <Button
                    onClick={handleReset}
                    variant="outline"
                    size="sm"
                    disabled={!isDirty || isSaving}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
                >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                </Button>
                <Button
                    onClick={handleSave}
                    size="sm"
                    disabled={!isDirty || isSaving}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white"
                >
                    <Save className="w-4 h-4 mr-2" />
                    {isSaving ? 'Saving...' : 'Save Changes'}
                </Button>
            </div>

            <style jsx global>{`
                .ck-editor__main {
                    background-color: #1e293b;
                }

                .ck.ck-editor__editable {
                    background-color: #1e293b;
                    color: #e2e8f0;
                }

                .ck.ck-content {
                    background-color: #1e293b;
                    color: #e2e8f0;
                }

                .ck-editor__top,
                .ck-toolbar {
                    background-color: #0f172a;
                    border-bottom-color: #334155;
                }

                .ck-toolbar__separator {
                    background-color: #334155;
                }

                .ck-button,
                .ck.ck-button {
                    background-color: #334155;
                    color: #e2e8f0;
                    border-color: #334155;
                }

                .ck-button:hover:not(:disabled),
                .ck.ck-button:hover:not(:disabled) {
                    background-color: #475569;
                    border-color: #475569;
                }

                .ck-button:active,
                .ck.ck-button:active {
                    background-color: #1e293b;
                }

                .ck.ck-editor__editable.ck-focused {
                    border-color: #3b82f6;
                }

                .ck-editor__editable p {
                    color: #e2e8f0;
                }

                .ck-editor__editable a {
                    color: #60a5fa;
                }

                .ck-editor__editable blockquote {
                    border-left-color: #3b82f6;
                    color: #cbd5e1;
                }

                .ck-editor__editable code {
                    background-color: #0f172a;
                    color: #f87171;
                }

                .ck-dropdown__panel,
                .ck.ck-panel {
                    background-color: #1e293b;
                    border-color: #334155;
                }

                .ck-dropdown__panel-visible,
                .ck.ck-panel.ck-panel_visible {
                    background-color: #1e293b;
                }

                .ck.ck-list__item {
                    color: #e2e8f0;
                }

                .ck.ck-list__item:hover:not(.ck-disabled) {
                    background-color: #334155;
                }

                .ck-image-upload-complete-message {
                    background-color: #1e293b;
                    color: #e2e8f0;
                }
            `}</style>
        </div>
    )
}

export default SidebarEditor
