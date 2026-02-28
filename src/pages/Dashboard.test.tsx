import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from './Dashboard';
import * as api from '../lib/api';

// Mock the API behavior and user hook
vi.mock('../lib/api', () => ({
    apiFetch: vi.fn(),
    getUser: () => ({ role: 'admin' }),
}));

describe('Dashboard Component', () => {
    it('renders a loading skeleton initially', () => {
        // Return a delayed promise so it stays loading
        vi.mocked(api.apiFetch).mockImplementation(() => new Promise(() => { }));

        render(
            <BrowserRouter>
                <Dashboard />
            </BrowserRouter>
        );

        expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('renders system statistics correctly after fetching', async () => {
        // Mock a successful API response with fake stats
        vi.mocked(api.apiFetch).mockResolvedValue({
            ok: true,
            json: async () => ({
                total_users: 42,
                queries_today: 15,
                total_queries: 100,
                estimated_cost: "5.00",
                total_documents: 10,
                vector_chunks: 500,
                avg_confidence: 0.85,
                avg_response_time_ms: 200,
                total_tokens: 5000,
            }),
        } as any);

        render(
            <BrowserRouter>
                <Dashboard />
            </BrowserRouter>
        );

        await waitFor(() => {
            // Look for one of the loaded values
            expect(screen.getByText('42')).toBeInTheDocument();
            expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
            // It should render multiple stat blocks
            expect(screen.getByText('System Summary')).toBeInTheDocument();
        });
    });
});
