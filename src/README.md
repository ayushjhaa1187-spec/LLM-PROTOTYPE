# Frontend Architecture - LLM Prototype

This directory contains the React frontend for the LLM Prototype application.

## Directory Structure

- `src/components/`: Reusable UI components (Buttons, Inputs, Modals, etc.).
- `src/layouts/`: Layout components (e.g., `DashboardLayout`) that provide consistent page structures.
- `src/lib/`: Core libraries and utilities, including API helpers (`api.ts`).
- `src/pages/`: Individual page components corresponding to routes.
- `src/App.tsx`: Main application entry point and route definitions.
- `src/main.tsx`: React DOM mounting point.

## Key Technologies

- **React 19**: Modern UI library.
- **Vite**: Ultra-fast build tool and dev server.
- **Tailwind CSS**: Utility-first styling.
- **Motion (Framer Motion)**: Smooth animations and transitions.
- **React Router 7**: Client-side routing.

## Authentication Flow

Authentication is handled via JWT tokens stored in `localStorage`. 
- `AuthLogin.tsx` handles both login and registration.
- `api.ts` provides a wrapper (`apiFetch`) that automatically adds the `Authorization: Bearer <token>` header to requests.

## Error Handling

- **Global Error Boundary**: Located in `src/components/ErrorBoundary.tsx`, catches unhandled component crashes and displays a premium error screen.
- **API Error Handling**: `apiFetch` in `src/lib/api.ts` handles 401 Unauthorized errors by clearing authentication and redirecting to login.
- **Form Validation**: Client-side trimming and server-side response parsing ensure data integrity.

## Development

Run the development server:
```bash
npm run dev
```

Build for production:
```bash
npm run build
```
