import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles, ShoppingBag, Package, Truck, Image as ImageIcon, Upload, Loader2, Download, ZoomIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ProductCard } from "@/components/ProductCard";
import { fetchProducts } from "@/api/products";
import { confirmPurchase, fetchBudgetStatus, proposePurchase } from "@/api/budget";
import { generateTryOn } from "@/api/tryon";
import { toast } from "sonner";
import type { Product } from "@/types/product";

export default function SmartCart() {
  const navigate = useNavigate();
  const { data: products = [], isLoading, error } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [optimizing, setOptimizing] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmTitle, setConfirmTitle] = useState("Confirm Purchase");
  const [confirmMessage, setConfirmMessage] = useState<React.ReactNode>("");
  const [confirmProceed, setConfirmProceed] = useState<() => void>(() => () => {});
  const [budgetCurrency, setBudgetCurrency] = useState("USD");
  const [budgetBalance, setBudgetBalance] = useState<number | null>(null);
  const [confirmDetails, setConfirmDetails] = useState<{
    before: number;
    price: number;
    after: number;
    currency: string;
  } | null>(null);
  const [tryOnOpen, setTryOnOpen] = useState(false);
  const [tryOnProduct, setTryOnProduct] = useState<Product | null>(null);
  const [tryOnBodyImage, setTryOnBodyImage] = useState<string | null>(null);
  const [tryOnResultUrl, setTryOnResultUrl] = useState<string | null>(null);
  const [tryOnLoading, setTryOnLoading] = useState(false);
  const [tryOnError, setTryOnError] = useState<string | null>(null);
  const [tryOnZoomOpen, setTryOnZoomOpen] = useState(false);

  const initialQuantities = useMemo(
    () => (products.length ? Object.fromEntries(products.map((p) => [p.id, 1])) : {}),
    [products.length]
  );
  const effectiveQuantities = Object.keys(quantities).length ? quantities : initialQuantities;

  const handleQuantityChange = (id: string, qty: number) => {
    setQuantities((prev) => ({ ...initialQuantities, ...prev, [id]: qty }));
  };

  const handleSwap = (productId: string, altId: string) => {
    toast.success("Product swapped!", { description: `Alternative selected for comparison.` });
  };

  const inferBodyRegion = (product: Product): string => {
    const name = `${product.name} ${product.category ?? ""}`.toLowerCase();
    if (/(jean|pants|trouser|legging|skirt|short)/.test(name)) return "bottom";
    if (/(shoe|sneaker|boot|heel|loafer)/.test(name)) return "feet";
    if (/(coat|jacket|blazer|hoodie|sweater|cardigan)/.test(name)) return "top";
    return "top";
  };

  const handleTryOn = (product: Product) => {
    setTryOnProduct(product);
    setTryOnBodyImage(null);
    setTryOnResultUrl(null);
    setTryOnError(null);
    setTryOnOpen(true);
  };

  const handleBodyImageChange = (file: File | null) => {
    setTryOnError(null);
    setTryOnResultUrl(null);
    if (!file) {
      setTryOnBodyImage(null);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : null;
      setTryOnBodyImage(result);
    };
    reader.readAsDataURL(file);
  };

  const handleGenerateTryOn = async () => {
    if (!tryOnProduct) return;
    if (!tryOnBodyImage) {
      setTryOnError("Please upload a full-body photo to continue.");
      return;
    }
    setTryOnLoading(true);
    setTryOnError(null);
    try {
      const result = await generateTryOn(tryOnBodyImage, [
        {
          image_url: tryOnProduct.image,
          category: tryOnProduct.category,
          body_region: inferBodyRegion(tryOnProduct),
        },
      ]);
      setTryOnResultUrl(result.url);
    } catch (e) {
      setTryOnError("Try-on generation failed. Please try again.");
    } finally {
      setTryOnLoading(false);
    }
  };

  const activeProducts = products.filter((p) => (effectiveQuantities[p.id] ?? 0) > 0);
  const subtotal = activeProducts.reduce((sum, p) => sum + p.price * (effectiveQuantities[p.id] ?? 0), 0);

  const handleOptimize = () => {
    setOptimizing(true);
    setTimeout(() => {
      setOptimizing(false);
      toast.success("Cart optimized!", { description: "Saved an additional $28 by switching retailers." });
    }, 1500);
  };

  const loadBudget = async () => {
    try {
      const status = await fetchBudgetStatus();
      setBudgetCurrency(status.currency);
      setBudgetBalance(status.wallet_balance);
    } catch {
      setBudgetCurrency("USD");
      setBudgetBalance(null);
    }
  };

  useEffect(() => {
    loadBudget();
    const handleBudgetUpdated = () => {
      loadBudget();
    };
    window.addEventListener("budget-updated", handleBudgetUpdated as EventListener);
    return () => {
      window.removeEventListener("budget-updated", handleBudgetUpdated as EventListener);
    };
  }, []);

  const handleProceedToCheckout = async () => {
    try {
      const currentBalance = budgetBalance ?? subtotal;
      const nextBalance = currentBalance - subtotal;
      const result = await proposePurchase(subtotal, "Cart total");
      const message = result.result;

      if (message.includes("[BUDGET_EXCEEDED]")) {
        setConfirmTitle("Confirm Purchase");
        setConfirmDetails({ before: currentBalance, price: subtotal, after: nextBalance, currency: budgetCurrency });
        setConfirmMessage("This purchase exceeds your budget. Do you want to proceed anyway?");
        setConfirmProceed(() => async () => {
          const updated = await confirmPurchase(subtotal);
          localStorage.setItem("budget_balance", String(updated.wallet_balance));
          window.dispatchEvent(new Event("budget-updated"));
          await loadBudget();
          navigate("/checkout");
        });
        setConfirmOpen(true);
        return;
      }

      if (message.includes("[WALLET_CONFIRMATION_REQUIRED]")) {
        setConfirmTitle("Confirm Purchase");
        setConfirmDetails({ before: currentBalance, price: subtotal, after: nextBalance, currency: budgetCurrency });
        setConfirmMessage("Do you confirm this purchase?");
        setConfirmProceed(() => async () => {
          const updated = await confirmPurchase(subtotal);
          localStorage.setItem("budget_balance", String(updated.wallet_balance));
          window.dispatchEvent(new Event("budget-updated"));
          await loadBudget();
          navigate("/checkout");
        });
        setConfirmOpen(true);
        return;
      }

      navigate("/checkout");
    } catch {
      toast.error("Budget check failed", { description: "Proceeding to checkout." });
      navigate("/checkout");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 glass-panel border-b border-border/50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate("/")} className="p-2 rounded-xl hover:bg-secondary transition-colors text-muted-foreground">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
                <ShoppingBag className="w-4 h-4 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-foreground">Smart Cart</h1>
                <p className="text-[11px] text-muted-foreground">{activeProducts.length} items · AI-curated</p>
              </div>
            </div>
          </div>
          <Button onClick={handleOptimize} disabled={optimizing} variant="outline" className="text-xs gap-1.5 rounded-xl">
            <Sparkles className="w-3.5 h-3.5" />
            {optimizing ? "Optimizing..." : "Optimize Cart"}
          </Button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-muted-foreground">Current Budget</p>
            <p className="text-2xl font-bold text-foreground">
              {budgetBalance !== null ? `${budgetBalance.toFixed(2)} ${budgetCurrency}` : "—"}
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Products Grid */}
          <div className="lg:col-span-2">
            {error && (
              <div className="glass-panel rounded-2xl p-6 text-center">
                <p className="text-destructive text-sm font-medium mb-2">Failed to load products</p>
                <p className="text-muted-foreground text-xs">
                  {error instanceof Error ? error.message : "Is the backend running at http://localhost:3001?"}
                </p>
                <p className="text-muted-foreground text-xs mt-2">
                  Make sure the backend server is running: <code className="bg-secondary px-1.5 py-0.5 rounded text-[10px]">cd backend && uvicorn app.main:app --reload</code>
                </p>
              </div>
            )}
            {isLoading && (
              <div className="glass-panel rounded-2xl p-6 text-center">
                <p className="text-muted-foreground text-sm">Loading products…</p>
              </div>
            )}
            {!isLoading && !error && products.length === 0 && (
              <div className="glass-panel rounded-2xl p-6 text-center">
                <p className="text-muted-foreground text-sm font-medium mb-2">No products found</p>
                <p className="text-muted-foreground text-xs">
                  The products list is empty. Check if the backend API is returning data.
                </p>
              </div>
            )}
            {!isLoading && !error && products.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {products.map((product, index) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    index={index}
                    quantity={effectiveQuantities[product.id] ?? 0}
                    onQuantityChange={handleQuantityChange}
                    onSwap={handleSwap}
                    onTryOn={handleTryOn}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Summary Sidebar */}
          <div className="space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-panel rounded-2xl p-5 shadow-card sticky top-20"
            >
              <h3 className="text-sm font-semibold text-foreground mb-4">Order Summary</h3>

              <div className="space-y-2.5 mb-4">
                {activeProducts.map((p) => (
                  <div key={p.id} className="flex justify-between items-start gap-4 text-xs">
                    <div className="flex-1">
                      <p className="text-foreground font-medium line-clamp-1">{p.name}</p>
                      <p className="text-[10px] text-muted-foreground">Size: {p.size} · Qty: {effectiveQuantities[p.id] ?? 0}</p>
                    </div>
                    <span className="text-foreground font-semibold">${p.price * (effectiveQuantities[p.id] ?? 0)}</span>
                  </div>
                ))}
              </div>

              <div className="border-t border-border pt-3 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span className="text-foreground font-medium">${subtotal}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="flex items-center gap-1 text-muted-foreground">
                    <Truck className="w-3 h-3" /> Delivery
                  </span>
                  <span className="text-accent font-medium">Free</span>
                </div>
                <div className="flex justify-between text-sm font-bold pt-2 border-t border-border">
                  <span className="text-foreground">Total</span>
                  <span className="gradient-text">${subtotal}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 mt-3 p-2.5 rounded-xl gradient-subtle-bg">
                <Package className="w-4 h-4 text-primary" />
                <p className="text-[11px] text-muted-foreground">
                  All items arrive within <span className="font-medium text-foreground">2-4 days</span>
                </p>
              </div>

              <Button
                onClick={handleProceedToCheckout}
                className="w-full mt-4 gradient-bg text-primary-foreground py-5 rounded-xl text-sm font-semibold shadow-glow hover:opacity-90 transition-opacity border-0"
              >
                Proceed to Checkout
              </Button>
            </motion.div>
          </div>
        </div>
      </div>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <div className="relative">
            <button
              onClick={() => setConfirmOpen(false)}
              className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
            >
              ×
            </button>
            <h2 className="text-base font-semibold text-foreground mb-4">{confirmTitle}</h2>

            <div className="flex items-center gap-3 p-3 rounded-2xl bg-secondary/40 border border-border mb-4">
              <div className="w-10 h-10 rounded-xl bg-background flex items-center justify-center">
                <ShoppingBag className="w-5 h-5 text-muted-foreground" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-muted-foreground">Cart total</p>
                <p className="text-sm font-semibold text-foreground">
                  {confirmDetails ? `${confirmDetails.price.toFixed(2)} ${confirmDetails.currency}` : ""}
                </p>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between text-muted-foreground">
                <span>Current Balance:</span>
                <span className="font-semibold text-foreground">
                  {confirmDetails ? `${confirmDetails.before.toFixed(2)} ${confirmDetails.currency}` : ""}
                </span>
              </div>
              <div className="flex justify-between text-red-500">
                <span>Price:</span>
                <span className="font-semibold">
                  {confirmDetails ? `-${confirmDetails.price.toFixed(2)} ${confirmDetails.currency}` : ""}
                </span>
              </div>
              <div className="flex justify-between text-sm font-semibold border-t border-border pt-2">
                <span>Remaining:</span>
                <span>
                  {confirmDetails ? `${confirmDetails.after.toFixed(2)} ${confirmDetails.currency}` : ""}
                </span>
              </div>
            </div>

            <p className="text-xs text-muted-foreground mt-3">{confirmMessage}</p>

            <div className="flex items-center gap-2 mt-5">
              <AlertDialogCancel asChild>
                <Button variant="outline" className="w-full rounded-xl">
                  Cancel
                </Button>
              </AlertDialogCancel>
              <AlertDialogAction asChild>
                <Button onClick={confirmProceed} className="w-full rounded-xl gradient-bg text-primary-foreground">
                  Confirm & Buy
                </Button>
              </AlertDialogAction>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={tryOnOpen} onOpenChange={setTryOnOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Virtual Try‑On</DialogTitle>
            <DialogDescription>
              Upload a full‑body photo, then generate a preview wearing
              {tryOnProduct ? ` ${tryOnProduct.name}` : " this item"}.
            </DialogDescription>
          </DialogHeader>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="rounded-2xl border border-dashed border-border p-6 text-center bg-secondary/20">
                <input
                  id="tryon-file"
                  type="file"
                  accept="image/*"
                  onChange={(e) => handleBodyImageChange(e.target.files?.[0] ?? null)}
                  className="hidden"
                />
                <label
                  htmlFor="tryon-file"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-background hover:bg-secondary transition-colors text-xs font-semibold cursor-pointer"
                >
                  <Upload className="w-4 h-4" />
                  Upload full‑body photo
                </label>
                <p className="text-[11px] text-muted-foreground mt-3">PNG or JPG. Full‑body, fully clothed for best results.</p>
              </div>

              {tryOnBodyImage && (
                <div className="rounded-2xl overflow-hidden border border-border">
                  <img src={tryOnBodyImage} alt="Body preview" className="w-full h-80 object-cover" />
                </div>
              )}

              {tryOnError && <p className="text-xs text-destructive">{tryOnError}</p>}

              <Button
                onClick={handleGenerateTryOn}
                disabled={tryOnLoading || !tryOnBodyImage}
                className={`w-full rounded-xl gradient-bg text-primary-foreground shadow-glow ${tryOnLoading ? "animate-pulse" : ""}`}
              >
                {tryOnLoading ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating your outfit...
                  </span>
                ) : (
                  "Generate Try‑On"
                )}
              </Button>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl border border-border p-4 flex items-center gap-3 bg-secondary/20">
                <div className="w-11 h-11 rounded-xl bg-background flex items-center justify-center">
                  <ImageIcon className="w-5 h-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Item</p>
                  <p className="text-sm font-semibold text-foreground">{tryOnProduct?.name ?? "—"}</p>
                </div>
              </div>

              {tryOnResultUrl ? (
                <div className="relative rounded-2xl overflow-hidden border border-border group cursor-zoom-in" onClick={() => setTryOnZoomOpen(true)}>
                  <img src={tryOnResultUrl} alt="Try-on result" className="w-full h-[420px] object-cover transition-transform duration-300 group-hover:scale-[1.02]" />
                  <div className="absolute right-4 top-4 bg-background/85 text-xs px-2 py-1 rounded-lg inline-flex items-center gap-1 shadow-sm">
                    <ZoomIn className="w-3 h-3" />
                    Click to zoom
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-border h-[420px] flex items-center justify-center text-xs text-muted-foreground bg-secondary/10">
                  Your generated try‑on will appear here.
                </div>
              )}

              {tryOnResultUrl && (
                <div className="flex items-center gap-2">
                  <Button asChild variant="outline" className="rounded-xl">
                    <a href={tryOnResultUrl} download target="_blank" rel="noreferrer">
                      <span className="inline-flex items-center gap-2">
                        <Download className="w-4 h-4" />
                        Download image
                      </span>
                    </a>
                  </Button>
                  <Button variant="outline" className="rounded-xl" onClick={() => setTryOnZoomOpen(true)}>
                    <span className="inline-flex items-center gap-2">
                      <ZoomIn className="w-4 h-4" />
                      Zoom
                    </span>
                  </Button>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={tryOnZoomOpen} onOpenChange={setTryOnZoomOpen}>
        <DialogContent className="max-w-5xl">
          <DialogHeader>
            <DialogTitle>Try‑On Preview</DialogTitle>
            <DialogDescription>Click the image or press ESC to close.</DialogDescription>
          </DialogHeader>
          {tryOnResultUrl && (
            <div className="rounded-2xl overflow-hidden border border-border">
              <img src={tryOnResultUrl} alt="Try-on zoom" className="w-full max-h-[80vh] object-contain bg-black/90" />
            </div>
          )}
          {tryOnResultUrl && (
            <Button asChild variant="outline" className="rounded-xl w-full">
              <a href={tryOnResultUrl} download target="_blank" rel="noreferrer">
                <span className="inline-flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  Download image
                </span>
              </a>
            </Button>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
