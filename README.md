# Agentic Cart Assistant

Agentic Cart Assistant is a browser-based AI shopping assistant. Users describe what they want to buy, the AI finds, ranks, and aggregates products across multiple retailers, and redirects them to a centralized cart with a **simulated checkout** experience.  

This repo includes both **frontend** and **backend** code.

---

## Project Structure

| Folder      | Stack |
|------------|--------|
| `frontend/` | Vite, React 18, TypeScript, React Query, shadcn/ui, Tailwind CSS |
| `backend/`  | Python 3.10+, FastAPI, Uvicorn |

---

## Quick Start (Terminal-Friendly)

We recommend **two terminals**: one for frontend, one for backend.

---

### **1️⃣ Terminal 1 – Frontend**

```bash
# Go to frontend folder
cd frontend

# Install dependencies (only once)
npm install

# Start frontend
npm run dev
Frontend will run at: http://localhost:8080
Make sure .env has the correct API URL:
VITE_API_URL=http://localhost:3001


# Go to backend folder
cd backend

# Create virtual environment (only once)
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server (must use port 3001 for frontend)
uvicorn app.main:app --reload --port 3001

Backend will run at: http://localhost:3001