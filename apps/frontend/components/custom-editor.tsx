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
        return <div className="p-4 text-red-500">Error loading editor!</div>;
    }

    if (cloud.status === 'loading') {
        return <div className="p-4 text-slate-400">Loading editor...</div>;
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
        <div className="ck-content text-black">
            <CKEditor
                editor={ClassicEditor}
                data={initialData}
                config={{
                    licenseKey: 'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3OTc3MjQ3OTksImp0aSI6ImRmNzA5ZDc5LTZiMzAtNGRjYi04MzFkLWNiOWU3MGM5ZmVmOSIsImxpY2Vuc2VkSG9zdHMiOlsiMTI3LjAuMC4xIiwibG9jYWxob3N0IiwiMTkyLjE2OC4qLioiLCIxMC4qLiouKiIsIjE3Mi4qLiouKiIsIioudGVzdCIsIioubG9jYWxob3N0IiwiKi5sb2NhbCJdLCJ1c2FnZUVuZHBvaW50IjoiaHR0cHM6Ly9wcm94eS1ldmVudC5ja2VkaXRvci5jb20iLCJkaXN0cmlidXRpb25DaGFubmVsIjpbImNsb3VkIiwiZHJ1cGFsIl0sImxpY2Vuc2VUeXBlIjoiZGV2ZWxvcG1lbnQiLCJmZWF0dXJlcyI6WyJEUlVQIiwiRTJQIiwiRTJXIl0sInJlbW92ZUZlYXR1cmVzIjpbIlBCIiwiUkYiLCJTQ0giLCJUQ1AiLCJUTCIsIlRDUiIsIklSIiwiU1VBIiwiQjY0QSIsIkxQIiwiSEUiLCJSRUQiLCJQRk8iLCJXQyIsIkZBUiIsIkJLTSIsIkZQSCIsIk1SRSJdLCJ2YyI6IjQxNDllYzRiIn0.rVAFEwnSsbW_lZRcKsFVp4tMpeOB3sDGVlNYUX_f5Fwc2TEguS8t8RHi1L9F_jdqHp3InadZKeFRo6BNXodk4A',
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
