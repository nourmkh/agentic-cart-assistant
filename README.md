# 🛍️ Agentic Cart Assistant  
**Your personal AI shopper — anywhere on the internet**

The **Agentic Cart Assistant** is an AI-powered shopping companion that acts like a **real human personal shopper**, but works across **any online store**.

Instead of just showing links, it can:
- 🔍 Find the best products for you  
- 🌐 Visit real retailer websites  
- 🎨 Select the right size & color  
- 🛒 Add items to your cart  
- 💳 Take you directly to checkout  

All from **one simple interface**.

> Think: *ChatGPT + Pinterest taste + a human who actually clicks “Add to Cart” for you.*

---

## 🚦 Project Status

![Status](https://img.shields.io/badge/status-active-success.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-blue.svg)
![Frontend](https://img.shields.io/badge/frontend-React_Vite-61dafb.svg)
![Agent](https://img.shields.io/badge/agent-Playwright-orange.svg)
![Memory](https://img.shields.io/badge/memory-Zep_MCP-purple.svg)

---

## 🧠 What Makes This Different?

Most shopping assistants stop at **recommendations**.  
Agentic Cart Assistant goes further — it **takes action**.

### ✅ Not just search — execution
- Doesn’t just suggest products  
- Opens the website and **adds items to your cart**

### ✅ Works on *any* store
- No plugins
- No retailer APIs
- If a human can buy it, the agent can too

### ✅ Learns your personal style
- Learns visually
- Improves over time
- Results feel increasingly *you*

---

## ✨ Core Features

### 🤖 Universal Shopping Agent
- Works on **any e-commerce site**
- Uses DOM understanding instead of fragile selectors
- Mimics real human behavior
- Recovers from broken links and layout changes

---

### 🧬 Style DNA (Long-Term Memory)
Your shopping taste is **remembered**, not reset.

- Connects to your **Pinterest boards**
- Learns:
  - Colors you love
  - Brands you prefer
  - Fits and silhouettes you gravitate toward
- Stored as a long-term **Style DNA** using **Zep MCP**
- Search results are re-ranked based on *you*

---

### 🔎 Intelligent Product Search
- Searches across the web
- Fixes broken or redirected product links
- Searches *inside* retailer sites when needed
- Prioritizes products that match your style profile

---

### 🛒 Unified Cart & Budget Guard
- One cart across multiple retailers
- Real-time budget tracking
- Prevents overspending
- Checkout handoff keeps payments secure

---

## 🤖 Checkout Automation Flow

### 1️⃣ Persistent Browser Session
- Launches a real browser with saved cookies and logins

### 2️⃣ Smart Navigation
- Tries direct product links
- Falls back to on-site search when links break

### 3️⃣ Variant Selection
- Selects size, color, and options automatically
- Uses heuristics + Style DNA preferences

### 4️⃣ Add to Cart
- Language-agnostic button detection:
  - “Add to Cart”
  - “Add to Bag”
  - “Ajouter au panier”
- Confirms success via UI feedback

### 5️⃣ Human Checkout Handoff
- Navigates to checkout
- Pauses
- User completes payment manually

---

## 🏗️ Architecture

```mermaid
graph TD
    User[User] --> Frontend[React Frontend]
    Frontend --> Backend[FastAPI Backend]
    
    subgraph "Intelligent Backend"
        Backend --> SearchService[Search Service]
        Backend --> AutomationService[Universal Agent]
        Backend --> ZepMCP["Zep Memory (Style DNA)"]
        Backend --> Pinterest[Pinterest Scraper]
    end
    
    subgraph "Autonomous Agent"
        AutomationService --> Playwright[Playwright Browser]
        Playwright --> Retailer[Any Retailer Website]
    end
    
    Pinterest --> ZepMCP
    ZepMCP --> SearchService
