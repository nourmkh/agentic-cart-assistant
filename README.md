# 🛍️ Agentic Cart Assistant

The **Agentic Cart Assistant** is a next-generation AI shopping companion that revolutionizes the e-commerce experience. It acts as a universal personal shopper that not only finds and ranks products from **any online store** but also **autonomously navigates retailer websites** to add items to the cart and initiate checkout—all from a single, unified interface.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/backend-FastAPI-blue.svg)
![React](https://img.shields.io/badge/frontend-React_Vite-61dafb.svg)
![Agent](https://img.shields.io/badge/agent-Playwright-orange.svg)
![Memory](https://img.shields.io/badge/memory-Zep_MCP-purple.svg)

---

## ✨ Key Features

- **🤖 Universal Autonomous Agent**
  - **Retailer Agnostic**: The agent is designed to understand the structure of **any e-commerce website**.
  - **DOM Introspection**: Instead of relying on fragile selectors, the agent "reads" the page code to dynamically identify options (size, color) and buttons.
  - **Stealth Navigation**: Mimics human behavior to ensure smooth interaction with complex sites.

- **🧠 Style DNA & Hyper-Personalization**
  - **Pinterest Integration**: Connects to your Pinterest boards to analyze your visual preferences.
  - **Zep MCP Memory**: Uses **Zep's Memory Context Protocol** to build a long-term "Style DNA" profile. This memory evolves with every interaction, learning your favorite brands, colors, and fits.
  - **Contextual Ranking**: Search results aren't just relevant to keywords—they are re-ranked based on your unique style profile stored in Zep.

- **🔎 Intelligent Product Search**
  - **Global Reach**: Aggregates products from across the web.
  - **Smart Fallbacks**: Automatically detects broken links and searches the retailer's site to find the exact item.

- **🛒 Smart Cart & Budgeting**
  - **Unified Cart**: Manage items from multiple retailers in one view.
  - **Budget Guard**: Real-time wallet monitoring prevents overspending.
  - **Virtual Try-On**: AI-powered preview of how items look on you.

---

## 🤖 Detailed Checkout Automation Flow

The automation engine is designed to be **retailer-agnostic** and highly resilient. Here is the step-by-step process the agent executes when you click "Confirm & Pay":

### 1. **Session Initialization (Persistent Context)**
   - The agent launches a browser instance with a **persistent user data directory**.
   - This means cookies, local storage, and previous logins are preserved, mimicking a real user's browser history.

### 2. **Smart Navigation & Fallback**
   - **Direct Link**: It first attempts to navigate to the product URL provided by the search results.
   - **Page Analysis**: It instantly analyzes the page to verify if it's a product page (checking for "Add to Cart" buttons, price, etc.).
   - **Intelligent Fallback**: If the link leads to a homepage or category page (common with dynamic inventory), the agent automatically:
     - Locates the site's search bar.
     - Types the exact product name.
     - Submits the search and identifies the correct item from results.
     - Navigates to the correct product page.

### 3. **Heuristic Variant Selection**
     - **Color Matching**
     - **Size Selection**

### 4. **Dynamic Cart Interaction**
   - **Button Detection**: It scans for buttons with text like "Add to Cart", "Add to Bag", "Ajouter au panier", making it language-agnostic.
   - **Action Execution**: It clicks the button and waits for confirmation (e.g., cart counter update, slide-out modal).

### 5. **Checkout Transition & Handoff**
   - Notifies the backend that the item is secured in the cart.
   - Navigates to the retailer's checkout page.
   - **Human Handoff**: The agent pauses and keeps the browser open, allowing the user to securely enter payment details and finalize the purchase manually. This ensures sensitive financial data is never handled by the AI.

---

## 🏗️ Architecture

The system consists of a modern React frontend and a powerful FastAPI backend that orchestrates the AI agents and memory layers.

```mermaid
graph TD
    User[User] -->|Interacts| Frontend[React Frontend]
    Frontend -->|API Calls| Backend[FastAPI Backend]
    
    subgraph "Intelligent Backend"
        Backend -->|Search| SearchService[Search Service]
        Backend -->|Orchestrates| AutomationService[Universal Agent]
        Backend -->|Recall| ZepMCP[Zep Memory (Style DNA)]
        Backend -->|Analyze| Pinterest[Pinterest Scraper]
    end
    
    subgraph "Autonomous Agent"
        AutomationService -->|Controls| Playwright[Playwright Browser]
        Playwright -->|Navigates| anyRetailer[Any Retailer Website]
    end
    
    Pinterest -->|Feeds| ZepMCP
    ZepMCP -->|Refines| SearchService
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS, shadcn/ui
- **State/Data**: React Query (TanStack Query)
- **Animation**: Framer Motion
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Server**: Uvicorn
- **Automation**: Playwright (Sync API) + `playwright-stealth`
- **Memory/Context**: **Zep MCP** (Memory Context Protocol)
- **Networking**: HTTPX
- **Data Handling**: Pydantic models

---

## 🚀 Installation & Setup

### Prerequisites
- **Node.js**: v18+
- **Python**: v3.10+
- **Browser**: Chrome/Chromium installed
- **API Keys**: Serper (Search), Zep (Memory - optional but recommended)

### 1️⃣ Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. Create a `.env` file in `backend/`:
   ```env
   SERPER_API_KEY=your_key
   ZEP_API_KEY=your_key
   PORT=3001
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 3001
   ```

### 2️⃣ Frontend Setup

1. Navigate to the frontend directory (`cd frontend`).
2. Install dependencies (`npm install`).
3. Start dev server (`npm run dev`).

---

## 📖 Usage Guide

1. **Build Your Style DNA**: 
   - Connect your Pinterest account in settings. The agent feeds visual data into **Zep Memory**.
   
2. **Browse & Search**:
   - Search for products. The results are personalized based on your Zep profile.

3. **Add to Cart & Checkout**:
   - Add items to the Smart Cart.
   - Click **"Confirm & Pay"** to launch the **Universal Shopper Agent**.

4. **Watch the Magic**:
   - The agent autonomously navigates retailer sites, finds items, selects variants, and reaches checkout.

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
