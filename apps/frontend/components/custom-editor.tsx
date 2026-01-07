'use client';

import React from 'react';
import { CKEditor, useCKEditorCloud } from '@ckeditor/ckeditor5-react';

interface CustomEditorProps {
    initialData: string;
    onChange?: (data: string) => void;
}

const CustomEditor: React.FC<CustomEditorProps> = ({ initialData, onChange }) => {
    const cloud = useCKEditorCloud({
        version: '44.1.0', // Using a recent stable version
        premium: true
    });

    if (cloud.status === 'error') {
        return <div className="p-4 text-destructive">Error loading editor!</div>;
    }

    if (cloud.status === 'loading') {
        return <div className="p-4 text-muted-foreground">Loading editor...</div>;
    }

    const {
        ClassicEditor,
        Essentials,
        Paragraph,
        Bold,
        Italic,
        List,
        Heading,
        Link,
        BlockQuote,
        Undo,
        Indent
    } = cloud.CKEditor;

    return (
        <div className="ck-content text-foreground">
            <CKEditor
                editor={ClassicEditor}
                data={initialData}
                config={{
                    // licenseKey removed
                    plugins: [
                        Essentials, Paragraph, Bold, Italic,
                        List, Heading, Link, BlockQuote, Undo, Indent
                    ],
                    toolbar: [
                        'undo', 'redo', '|',
                        'heading', '|',
                        'bold', 'italic', '|',
                        'link', 'bulletedList', 'numberedList', 'blockQuote', 'outdent', 'indent'
                    ]
                }}
                onChange={(event, editor) => {
                    const data = editor.getData();
                    if (onChange) {
                        onChange(data);
                    }
                }}
            />
        </div>
    );
};

export default CustomEditor;
