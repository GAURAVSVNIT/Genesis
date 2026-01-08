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
                    licenseKey: 'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3OTk0NTI3OTksImp0aSI6IjQ1Nzc4ZGNkLTFhZWItNDU3MS05NWVmLWJhYjJjMWI1ODUxNiIsInVzYWdlRW5kcG9pbnQiOiJodHRwczovL3Byb3h5LWV2ZW50LmNrZWRpdG9yLmNvbSIsImRpc3RyaWJ1dGlvbkNoYW5uZWwiOlsiY2xvdWQiLCJkcnVwYWwiXSwiZmVhdHVyZXMiOlsiRFJVUCIsIkUyUCIsIkUyVyJdLCJyZW1vdmVGZWF0dXJlcyI6WyJQQiIsIlJGIiwiU0NIIiwiVENQIiwiVEwiLCJUQ1IiLCJJUiIsIlNVQSIsIkI2NEEiLCJMUCIsIkhFIiwiUkVEIiwiUEZPIiwiV0MiLCJGQVIiLCJCS00iLCJGUEgiLCJNUkUiXSwidmMiOiI5ZWZiZjY0ZSJ9.mx4I_HNQu5MH_Rt2fak8nFFTeF-SFLXlC_FFgO_jQ2bfdjuyCUEQ02bvXM2ixV6ujmmJLzu6GobkMC9j3deDSQ',
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
