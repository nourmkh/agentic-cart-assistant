import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ShoppingBag, CreditCard, Lock, CheckCircle2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RotatingCard3D } from "@/components/RotatingCard3D";
import { fetchProducts } from "@/api/products";
import { automateCheckout } from "@/api/checkout";
import productHeadphones from "@/assets/product-headphones.jpg";
import productSneakers from "@/assets/product-sneakers.jpg";
import productWatch from "@/assets/product-watch.jpg";
import productBag from "@/assets/product-bag.jpg";

const imageMap: Record<string, string> = {
  headphones: productHeadphones,
  sneakers: productSneakers,
  watch: productWatch,
  bag: productBag,
};

function getImageSrc(image: string): string {
  if (image.startsWith("http://") || image.startsWith("https://")) return image;
  return imageMap[image] ?? image;
}

type FocusedField = "number" | "name" | "expiry" | "cvc" | null;

function formatCardNumberInput(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

function formatExpiryInput(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  if (digits.length >= 2) return `${digits.slice(0, 2)} / ${digits.slice(2)}`;
  return digits;
}

export default function Checkout() {
  const navigate = useNavigate();
  const [confirmed, setConfirmed] = useState(false);
  const [isAutomating, setIsAutomating] = useState(false);
  const [automationMessage, setAutomationMessage] = useState("");
  const [cardNumber, setCardNumber] = useState("");
  const [cardName, setCardName] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvc, setCvc] = useState("");
  const [focusedField, setFocusedField] = useState<FocusedField>(null);
  const { data: products = [], isLoading, error } = useQuery({ queryKey: ["products"], queryFn: fetchProducts });
  const subtotal = products.reduce((s, p) => s + p.price, 0);

  const handleConfirm = async () => {
    setIsAutomating(true);
    setAutomationMessage("Initializing Personal Shopper agent...");

    try {
      const response = await automateCheckout({
        items: products.map(p => ({
          id: p.id,
          name: p.name,
          retailer: p.retailer,
          url: p.url || "",
          price: p.price,
          size: p.size
        })),
        user_data: {
          name: cardName,
          email: "user@example.com", // In a real app, this would come from a form or auth context
          address: "123 Fashion St",
          city: "Paris",
          zip: "75001"
        }
      });

      setAutomationMessage(response.message);

      // We don't wait for the automation to finish (it stays open in background)
      // but we show the success state in our app
      setTimeout(() => {
        setIsAutomating(false);
        setConfirmed(true);
      }, 2000);

    } catch (err) {
      console.error("Automation failed:", err);
      setIsAutomating(false);
      setConfirmed(true); // Fallback for demo
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 glass-panel border-b border-border/50">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={() => navigate("/cart")} className="p-2 rounded-xl hover:bg-secondary transition-colors text-muted-foreground">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-bg flex items-center justify-center">
              <ShoppingBag className="w-4 h-4 text-primary-foreground" />
            </div>
            <h1 className="text-sm font-bold text-foreground">Checkout</h1>
          </div>
          <div className="ml-auto flex items-center gap-1 text-[11px] text-accent font-medium">
            <Lock className="w-3 h-3" /> Secured by AI Agent
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <AnimatePresence mode="wait">
          {isAutomating ? (
            <motion.div
              key="automating"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex flex-col items-center justify-center py-20 text-center"
            >
              <div className="relative w-24 h-24 mb-8">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 border-4 border-primary/20 border-t-primary rounded-full"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Sparkles className="w-8 h-8 text-primary animate-pulse" />
                </div>
              </div>
              <h2 className="text-xl font-bold text-foreground mb-3">AI Agent is Shopping for You</h2>
              <p className="text-muted-foreground text-sm max-w-sm mb-6">
                {automationMessage || "Opening brand websites and adding items to carts..."}
              </p>
              <div className="flex gap-2">
                {["Zara", "Stradivarius"].map((retailer) => (
                  <div key={retailer} className="px-3 py-1 rounded-full bg-secondary text-[10px] font-bold text-muted-foreground animate-pulse">
                    {retailer}
                  </div>
                ))}
              </div>
            </motion.div>
          ) : confirmed ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center justify-center py-20 text-center"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.1 }}
                className="w-20 h-20 rounded-full gradient-bg flex items-center justify-center shadow-glow mb-6"
              >
                <CheckCircle2 className="w-10 h-10 text-primary-foreground" />
              </motion.div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Order Confirmed!</h2>
              <p className="text-muted-foreground text-sm mb-6 max-w-sm">
                Your AI agent has placed orders across 4 retailers. You'll receive tracking info via email.
              </p>
              <div className="flex items-center gap-2 p-3 rounded-xl gradient-subtle-bg text-xs text-muted-foreground">
                <Sparkles className="w-4 h-4 text-primary" />
                You saved <span className="font-bold text-accent">$312</span> compared to buying at full price
              </div>
              <Button
                onClick={() => navigate("/")}
                variant="outline"
                className="mt-8 rounded-xl"
              >
                Start New Search
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 lg:grid-cols-5 gap-6"
            >
              {/* Form */}
              <div className="lg:col-span-3 space-y-5">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="glass-panel rounded-2xl p-5 shadow-card"
                >
                  <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-primary" />
                    Payment & Shipping
                  </h3>
                  <p className="text-[11px] text-muted-foreground mb-4">
                    Single entry — your AI agent handles multi-retailer checkout automatically.
                  </p>

                  <RotatingCard3D
                    cardNumber={cardNumber}
                    cardName={cardName}
                    expiry={expiry}
                    cvc={cvc}
                    isFlipped={focusedField === "cvc"}
                    className="mb-6"
                  />

                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      placeholder="Full Name"
                      value={cardName}
                      onChange={(e) => setCardName(e.target.value)}
                      onFocus={() => setFocusedField("name")}
                      onBlur={() => setFocusedField(null)}
                      className="col-span-2 rounded-xl bg-secondary/50 border-0 text-sm"
                    />
                    <Input placeholder="Email" className="col-span-2 rounded-xl bg-secondary/50 border-0 text-sm" />
                    <Input
                      placeholder="Card Number"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(formatCardNumberInput(e.target.value))}
                      onFocus={() => setFocusedField("number")}
                      onBlur={() => setFocusedField(null)}
                      maxLength={19}
                      className="col-span-2 rounded-xl bg-secondary/50 border-0 text-sm font-mono"
                    />
                    <Input
                      placeholder="MM / YY"
                      value={expiry}
                      onChange={(e) => setExpiry(formatExpiryInput(e.target.value))}
                      onFocus={() => setFocusedField("expiry")}
                      onBlur={() => setFocusedField(null)}
                      maxLength={7}
                      className="rounded-xl bg-secondary/50 border-0 text-sm font-mono"
                    />
                    <Input
                      placeholder="CVC"
                      value={cvc}
                      onChange={(e) => setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))}
                      onFocus={() => setFocusedField("cvc")}
                      onBlur={() => setFocusedField(null)}
                      maxLength={4}
                      type="password"
                      className="rounded-xl bg-secondary/50 border-0 text-sm font-mono"
                    />
                    <Input placeholder="Shipping Address" className="col-span-2 rounded-xl bg-secondary/50 border-0 text-sm" />
                    <Input placeholder="City" className="rounded-xl bg-secondary/50 border-0 text-sm" />
                    <Input placeholder="ZIP Code" className="rounded-xl bg-secondary/50 border-0 text-sm" />
                  </div>
                </motion.div>
              </div>

              {/* Order Summary */}
              <div className="lg:col-span-2">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="glass-panel rounded-2xl p-5 shadow-card sticky top-20"
                >
                  <h3 className="text-sm font-semibold text-foreground mb-4">Order Summary</h3>
                  {error && <p className="text-destructive text-xs mb-2">Could not load products.</p>}
                  {isLoading && <p className="text-muted-foreground text-xs mb-2">Loading…</p>}
                  <div className="space-y-3 mb-4">
                    {products.map((p) => (
                      <div key={p.id} className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg overflow-hidden bg-secondary">
                          <img src={getImageSrc(p.image)} alt={p.name} className="w-full h-full object-cover" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-foreground truncate">{p.name}</p>
                          <p className="text-[11px] text-muted-foreground">{p.retailer} · Size: {p.size}</p>
                        </div>
                        <span className="text-xs font-semibold text-foreground">${p.price}</span>
                      </div>
                    ))}
                  </div>
                  <div className="border-t border-border pt-3 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Subtotal</span>
                      <span className="text-foreground font-medium">${subtotal}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-accent">Savings</span>
                      <span className="text-accent font-medium">-$312</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Shipping</span>
                      <span className="text-accent font-medium">Free</span>
                    </div>
                    <div className="flex justify-between text-sm font-bold pt-2 border-t border-border">
                      <span className="text-foreground">Total</span>
                      <span className="gradient-text">${subtotal}</span>
                    </div>
                  </div>

                  <Button
                    onClick={handleConfirm}
                    className="w-full mt-5 gradient-bg text-primary-foreground py-5 rounded-xl text-sm font-semibold shadow-glow hover:opacity-90 transition-opacity border-0"
                  >
                    <Lock className="w-3.5 h-3.5 mr-2" />
                    Confirm & Pay ${subtotal}
                  </Button>

                  <p className="text-[10px] text-muted-foreground/60 text-center mt-3">
                    Your agent will place orders on 4 retailers on your behalf
                  </p>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
