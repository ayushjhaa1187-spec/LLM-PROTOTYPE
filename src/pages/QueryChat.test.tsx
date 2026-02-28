import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import QueryChat from './QueryChat';
import * as api from '../lib/api';

vi.mock('../lib/api', () => ({
    apiFetch: vi.fn(),
    getUser: () => ({ role: 'analyst' }),
}));

describe('QueryChat Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('loads available documents into the scope dropdown', async () => {
        // Mock the initial documents list fetch
        vi.mocked(api.apiFetch).mockResolvedValue({
            ok: true,
            json: async () => ([
                { id: "doc1", filename: "Test_Document_1.pdf" },
                { id: "doc2", filename: "Policy_Doc.docx" },
            ]),
        } as any);

        render(
            <BrowserRouter>
                <QueryChat />
            </BrowserRouter>
        );

        // After loading, the scope dropdown should contain these docs
        await waitFor(() => {
            expect(screen.getByText('Test_Document_1.pdf')).toBeInTheDocument();
            expect(screen.getByText('Policy_Doc.docx')).toBeInTheDocument();
        });
    });

    it('submits a query with the selected document context', async () => {
        // 1. Initial doc load mock
        vi.mocked(api.apiFetch).mockResolvedValue({
            ok: true,
            json: async () => ([
                { id: "doc1", filename: "Test.pdf" },
            ]),
        } as any);

        render(
            <BrowserRouter>
                <QueryChat />
            </BrowserRouter>
        );

        // Wait for doc fetch to settle
        await waitFor(() => {
            expect(screen.getByText('Test.pdf')).toBeInTheDocument();
        });

        // 2. We mock the actual query POST request
        const postMock = vi.mocked(api.apiFetch).mockResolvedValue({
            ok: true,
            json: async () => ({
                id: "q1",
                answer: "This is a RAG response.",
                confidence: 0.95,
                citations: []
            }),
        } as any);

        // 3. User selects the document from the dropdown
        const select = document.querySelector('select') as HTMLSelectElement;
        fireEvent.change(select, { target: { value: 'doc1' } });

        // 4. User types a query and sends
        const input = document.querySelector('textarea') as HTMLTextAreaElement;
        fireEvent.change(input, { target: { value: 'What is the policy?' } });

        const button = document.querySelector('button[type="submit"]') as HTMLButtonElement;
        fireEvent.click(button);

        // 5. Verify the POST hit was called correctly with doc scoped
        await waitFor(() => {
            expect(postMock).toHaveBeenCalledWith('/api/v1/query', expect.objectContaining({
                method: "POST",
                body: expect.stringContaining('"document_ids":["doc1"]')
            }));
        });
    });
});
