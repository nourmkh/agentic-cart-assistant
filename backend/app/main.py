import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import agent, budget, cart, checkout, llm, pinterest, products, tryon

load_dotenv()  # load .env so SERPER_API_KEY and PORT are available

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("groq").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai._base_client").setLevel(logging.WARNING)
logging.getLogger("app.data.pinterest").setLevel(logging.WARNING)
logging.getLogger("app.data.pinterest.filter").setLevel(logging.WARNING)
logging.getLogger("app.data.pinterest.sync").setLevel(logging.WARNING)
logging.getLogger("app.data.ZEP_mcp.pinterest_sync").setLevel(logging.WARNING)

app = FastAPI(title="Agentic Cart API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(agent.router)
app.include_router(checkout.router)
app.include_router(pinterest.router)
app.include_router(llm.router)
app.include_router(budget.router)
app.include_router(cart.router)
app.include_router(tryon.router)

# Serve generated uploads (try-on fallback files) at /uploads
uploads_dir = os.path.join(os.getcwd(), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/health")
def health():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
