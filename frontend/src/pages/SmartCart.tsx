import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Sparkles, ShoppingBag, Package, Truck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductCard } from "@/components/ProductCard";
import { fetchProducts } from "@/api/products";
import { toast } from "sonner";

export default function SmartCart() {
  const navigate = useNavigate();
  const { data: products = [], isLoading, error } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [optimizing, setOptimizing] = useState(false);

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

  const activeProducts = products.filter((p) => (effectiveQuantities[p.id] ?? 0) > 0);
  const subtotal = activeProducts.reduce((sum, p) => sum + p.price * (effectiveQuantities[p.id] ?? 0), 0);
  const savings = activeProducts.reduce(
    (sum, p) => sum + ((p.originalPrice || p.price) - p.price) * (effectiveQuantities[p.id] ?? 0),
    0
  );

  const handleOptimize = () => {
    setOptimizing(true);
    setTimeout(() => {
      setOptimizing(false);
      toast.success("Cart optimized!", { description: "Saved an additional $28 by switching retailers." });
    }, 1500);
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
                  <div key={p.id} className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{p.name} × {effectiveQuantities[p.id] ?? 0}</span>
                    <span className="text-foreground font-medium">${p.price * (effectiveQuantities[p.id] ?? 0)}</span>
                  </div>
                ))}
              </div>

              <div className="border-t border-border pt-3 space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span className="text-foreground font-medium">${subtotal}</span>
                </div>
                {savings > 0 && (
                  <div className="flex justify-between text-xs">
                    <span className="text-accent font-medium">You save</span>
                    <span className="text-accent font-medium">-${savings}</span>
                  </div>
                )}
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
                onClick={() => navigate("/checkout")}
                className="w-full mt-4 gradient-bg text-primary-foreground py-5 rounded-xl text-sm font-semibold shadow-glow hover:opacity-90 transition-opacity border-0"
              >
                Proceed to Checkout
              </Button>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
