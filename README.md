# Enterprise LLM Prototype - RAG Document Engine

<div align="center">
  <img alt="RAG Engine Banner" src="https://img.shields.io/badge/Enterprise-RAG%20Engine-blue?style=for-the-badge&logo=openai" />
</div>

## Overview
A secure, scalable enterprise platform designed for internal document retrieval, augmented generation (RAG), and policy compliance checking. This prototype allows organization analysts to upload private documents, securely index them locally, and prompt advanced localized queries against them utilizing a highly available Fast-API architecture.

### Key Features
- **Local Vector Engine**: Pure python implementation ensuring data privacy and isolated knowledge retrieval. 
- **Role-Based Access Control**: Fully enforced admin and analyst roles locking down system settings, global queries, and file erasure logic natively built on FastAPI and SQL.
- **Micro-Chunk Resolution**: Accurate text retrieval indexing ensuring accurate generative responses natively bypassing payload limits. 
- **Zero-Trust Frontend**: A fully isolated Vite + React Dashboard handling encrypted JWT exchanges dynamically to the underlying Python services.

## Application Architecture

- **Frontend**: React 19 + Vite + TailwindCSS. Configured for high-performance SPA routing and deployment to Vercel.
- **Backend Service**: FastAPI Framework. Handles Auth, background vectorized indexing tasks, JWT tracking, routing, and system load. SQLite powers standard tabular user records.
- **LLM Integrations**: Configured implicitly around standard OpenAI API architectures inside the secure `rag_service.py`. Built resiliently for custom on-premises swaps.

---

## 🚀 Running Locally

### 1. Requirements
Ensure you have `Node 18+`, `Python 3.10+`, and access to a terminal environment. 

### 2. Backend Initialization
The backend server must be initialized securely. Open a terminal and run the following in the `backend/` directory:

```bash
cd backend
python -m venv venv

# Windows Virtual Environment Active
venv\Scripts\activate
# OR MacOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Configuration**: Duplicate `.env.example` manually if present, otherwise set `OPENAI_API_KEY` inside `.env` located inside the `/backend` folder.

**Boot Server**:
```bash
uvicorn app.main:app --reload
```

### 3. Frontend Initialization 
Open a new parallel terminal in the root directory:
```bash
npm install
npm run dev
```
Navigate your browser to `http://localhost:5173`. 

---

## ⚡ Deployment Information

### Vercel (Frontend Web App)
This repository contains a natively generated `vercel.json` SPA configuration hook, so simply pushing to GitHub and letting the Vercel integration read your root `package.json` initiates a seamless deployment. 

**Important Vercel Note**: Ensure you set `VITE_API_URL` within the Vercel Project Environment Variables explicitly pointing to your deployed Python endpoint *(i.e. `https://your-fastapi-backend.render.com`)* otherwise it defaults to internal Vercel URLs via relative paths and 404s your API hits.

### Render / AWS / Remote Hosts (Python Core APIs)
Vercel is not designed to reliably execute stateful database indexing or vectorized mapping storage across the ephemeral serverless Lambda structure. 

**Automated Render Deployment**:
We have included a `render.yaml` file that automatically configures everything for you on Render.com:
1. Go to your Render Dashboard and click **New > Blueprint**.
2. Connect this repository.
3. Render will automatically provision the **PostgreSQL Database**, **Persistent Disk** (for ChromaDB rules mapping), and the **FastAPI Web Service**.
4. Important: Set `OPENAI_API_KEY` in your Render Environment settings once deployed.

**(Alternative) Manual Deployment**:
1. Create a Web Service inside your cloud provider matching the internal `app.main` boot path. 
2. Point the build context to the nested `backend/Dockerfile`.
3. Configure persistent disks protecting SQLite/Chroma mappings, or supply an external `DATABASE_URL`.

---
### Comprehensive Testing Suite
Continuous integration hooks check Python `tests/` syntaxes securely guaranteeing regressions aren't shipped to the enterprise network. 
1. **Frontend Tests**: `npm run test` executes a full DOM simulated evaluation against Vite components. 
2. **Backend Tests**: Navigating into the internal `/backend` dir allows `pytest -v` checks against Auth logic.

*Built securely for strict compliance architectures.*
