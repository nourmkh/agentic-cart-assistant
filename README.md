# 🛍️ Agentic Cart Assistant

The **Agentic Cart Assistant** is a next-generation AI shopping companion that revolutionizes the e-commerce experience. It acts as a universal personal shopper that not only finds and ranks products from **any online store** but also **autonomously navigates retailer websites** to add items to the cart and initiate checkout—all from a single, unified interface.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/backend-FastAPI-blue.svg)
![React](https://img.shields.io/badge/frontend-React_Vite-61dafb.svg)
![Agent](https://img.shields.io/badge/agent-Playwright-orange.svg)
![Memory](https://img.shields.io/badge/memory-Zep_MCP-purple.svg)

---

## 🏗️ How It Was Built: Frontend to Backend

This project uses a decoupled architecture where the **Frontend** handles the user experience and the **Backend** powers the AI agents. Here is a detailed breakdown of how we built it:

### 1️⃣ The Frontend (User Interface)

We started with a robust, modern React stack designed for speed and interactivity.

- **Fast Setup**: Initialized with **Vite** for lightning-fast HMR (Hot Module Replacement).
- **Styling**: Used **Tailwind CSS** for utility-first styling and **shadcn/ui** for accessible, pre-built components (buttons, dialogs, cards).
- **State Management**: Implemented **TanStack Query (React Query)** to handle async data fetching (search results, cart state) with caching and auto-refetching.
- **Routing**: **React Router** manages navigation between the Search, Smart Cart, and Checkout pages.

**Key Components:**
- `SmartCart.tsx`: The heart of the frontend. It displays aggregated items, handles quantity logic, and triggers the "Optimize Cart" features.
- `Checkout.tsx`: A simulated checkout page that collects user intent before handing off to the AI agent.

### 2️⃣ The Backend (Intelligence Layer)

The backend is built with **FastAPI** (Python), chosen for its speed and native support for asynchronous operations—critical for handling multiple AI agents simultaneously.

- **API Routes**: Organized via `APIRouter` to keep code modular (`/products`, `/agent`, `/cart`).
- **Data Models**: **Pydantic** ensures strict type validation for all data passing between frontend and backend.

### 3️⃣ The Core Logic: "Universal Intelligent Agent"

The `AutomationService` (`backend/app/services/automation_service.py`) is the most complex part of the system. It replaces traditional, brittle web scrapers with a **cognitive agent**.

- **Playwright Engine**: We use the synchronous Playwright API to drive a real Chromium browser instance.
- **Stealth Mode**: `playwright-stealth` injects scripts to mask the bot's fingerprint, making it look like a regular human user (plugins, navigator languages, etc.).
- **DOM Introspection**: Instead of hardcoding selectors like `#add-to-cart`, the agent scans the page's DOM for **semantic clues**:
  - Buttons containing words like "Add", "Bag", "Panier".
  - Dropdowns near labels like "Size" or "Taille".
  - Color swatches matching the user's selected variant.

### 4️⃣ The Integration: Zep MCP & Pinterest

- **Zep Memory**: We integrated **Zep's Memory Context Protocol (MCP)** to give the agent long-term memory. It stores a "Style DNA" based on user interactions.
- **Pinterest Scraper**: A background service scrapes the user's Pinterest boards to seed this Style DNA with visual preferences.

---

## ✨ Key Features

- **🤖 Universal Autonomous Agent**
  - **Retailer Agnostic**: Analyzes **any** e-commerce site structure on the fly.
  - **Smart Fallbacks**: If a link is broken, it automatically uses the retailer's search bar to find the item.

- **🧠 Style DNA & Hyper-Personalization**
  - **Contextual Ranking**: Search results are re-ranked based on your unique style profile stored in Zep.

- **🔎 Intelligent Product Search**
  - **Global Reach**: Aggregates products from across the web using Serper/Tavily APIs.

- **🛒 Smart Cart & Budgeting**
  - **Unified Cart**: Manage items from multiple retailers in one view.
  - **Budget Guard**: Real-time wallet monitoring.

- **👗 Virtual Try-On**
  - **AI Image Gen**: Upload a photo to preview how items look on you.

---

## 🤖 Detailed Checkout Automation Flow

The automation engine executes these steps when "Confirm & Pay" is clicked:

### 1. **Session & Stealth**
   - Launches browser with **persistent context** (cookies, login sessions preserved).
   - Applies stealth masking to evade bot detection.

### 2. **Navigation & Verification**
   - Navigates to the product URL.
   - **Smart Check**: Verifies if it's a product page. If not (e.g., category page), it triggers **Autopilot Search**:
     - Finds the search bar -> Types product name -> Clicks result -> Verified.

### 3. **Heuristic Variant Selection**
   - **Color**: Matches "Black", "Noir", "Tarte à la cerise" against DOM text/attributes.
   - **Size**: Identifies size selectors by proximity to "Size" labels.

### 4. **Cart & Handoff**
   - Clicks "Add to Cart" (multilingual support).
   - **Auto-Redirect**: Detects "Go to Checkout" modals or finds the cart icon to navigate to the final purchase screen.
   - **Human Handoff**: Pauses for the user to securely enter payment.

---


## 🔄 System Workflow

```mermaid
flowchart TD
  subgraph FE[Frontend · React / Vite]
    FE1[SmartCart Page]
    FE2[Virtual Try-On Modal]
    FE3[Pinterest Connect UI]
    FE4[Checkout Intent]
  end

  subgraph BE[Backend · FastAPI]
    C1["POST /api/cart"]
    R1[Ranking Service]
    S1[Retail Search Service]
    A1[Automation Service (Playwright Agent)]
    T1["POST /api/tryon/generate"]
    P1["POST /api/pinterest/connect"]
  end

  subgraph Z[Zep Cloud · MCP]
    ZU[User Memory]
    ZT[Conversation Thread]
    ZCTX[Style DNA Context]
  end

  subgraph EXT[External Services]
    PIN[Pinterest API]
    SERP[Serper / Tavily]
    RETAIL[E-commerce Sites]
    IMG[AI Image Gen]
  end

  FE1 --> C1
  C1 --> R1
  R1 --> ZCTX
  ZCTX --> R1
  R1 --> S1
  S1 --> SERP
  S1 --> FE1

  FE3 --> P1
  P1 --> PIN
  PIN --> ZU
  ZU --> ZCTX

  FE2 --> T1
  T1 --> IMG
  IMG --> FE2

  FE4 --> A1
  A1 --> RETAIL
  RETAIL --> A1
  A1 --> FE1
```

## 🚀 Installation & Setup

### Prerequisites
- **Node.js**: v18+
- **Python**: v3.10+
- **Browser**: Chrome/Chromium installed
- **API Keys**: Serper (Search), Zep (Memory)

### 1️⃣ Backend Setup

1. **Clone & CD**: `cd backend`
2. **Virtual Env**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate (Windows)
   ```
3. **Install**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
4. **Config**: Create `.env` with `SERPER_API_KEY`, `ZEP_API_KEY`.
5. **Run**: `uvicorn app.main:app --reload --port `

### 2️⃣ Frontend Setup

1. **CD**: `cd frontend`
2. **Install**: `npm install`
3. **Run**: `npm run dev`

---

## 📂 Project Structure

```
agentic-cart-assistant/
├── backend/
│   ├── app/
│   │   ├── services/
│   │   │   ├── RetailProduct/   # Search & Ranking logic
│   │   │   ├── automation_service.py # Core agent logic
│   │   │   └── pinterest.py     # Pinterest integration
│   │   ├── routers/             # API endpoints
│   │   ├── data/                # Zep MCP & Mock data
│   │   └── main.py              # App entry point
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── pages/               # React pages
│   │   ├── components/          # UI components
│   │   └── ...
│   └── ...
└── README.md
```

---

*Built for HackNation 2026*
