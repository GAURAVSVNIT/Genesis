'use client';

import dynamic from 'next/dynamic';

const ClientSideCustomEditor = dynamic(
    () => import('@/components/custom-editor'),
    { ssr: false }
);

export default ClientSideCustomEditor;
