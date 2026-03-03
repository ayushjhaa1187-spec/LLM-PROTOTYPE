# Backend API - LLM Prototype

This directory contains the FastAPI backend for the LLM Prototype application.

## Directory Structure

- `app/main.py`: Application entry point and router registration.
- `app/routes/`: API endpoint definitions (Auth, Documents, Queries, Admin).
- `app/models/`: SQLAlchemy database models.
- `app/services/`: Business logic, RAG implementation, and Vector Store management.
- `app/utils/`: Security helpers, rate limiting, and core utilities.
- `app/database.py`: Database engine and session management.
- `app/config.py`: Configuration and environment variable management.
- `tests/`: Automated test suite.

## Key Technologies

- **FastAPI**: Modern, fast (high-performance) web framework.
- **SQLAlchemy**: SQL toolkit and ORM.
- **SQLite**: Default local database.
- **SlowAPI**: Rate limiting.
- **Pydantic**: Data validation and settings management.
- **Gemini AI**: Underlying LLM for extraction and chat.

## Setup & Run

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the server**:
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```

3.  **API Documentation**:
    - Swagger UI: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
    - ReDoc: [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

## Authentication

The backend uses JWT (JSON Web Tokens) for authentication. Tokens are generated upon login/registration and must be included in the `Authorization: Bearer <token>` header for protected routes.

## Audit Logs

All sensitive actions (Login, Register, Query execution) are automatically logged to the `audit_logs` table in the database.
