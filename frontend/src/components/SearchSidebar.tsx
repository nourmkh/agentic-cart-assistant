import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Search, Sparkles, Image, Zap, DollarSign, Truck, Palette, Heart, ShoppingBag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchPinterestLoginUrl, fetchPinterestStatus } from "@/api/pinterest";
import { extractRequirements } from "@/api/llm";

const preferences = [
  { label: "Budget", icon: DollarSign, active: false },
  { label: "Fast Delivery", icon: Truck, active: false },
  { label: "Trending", icon: Zap, active: false },
  { label: "My Style", icon: Palette, active: false },
  { label: "Eco-Friendly", icon: Heart, active: false },
];

interface SearchSidebarProps {
  onStartShopping: () => void;
}

export function SearchSidebar({ onStartShopping }: SearchSidebarProps) {
  const [query, setQuery] = useState("");
  const [activePrefs, setActivePrefs] = useState<Set<string>>(new Set());
  const [isListening, setIsListening] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isPinterestConnected, setIsPinterestConnected] = useState(false);
  const [isPinterestLoading, setIsPinterestLoading] = useState(false);
  const [pinterestError, setPinterestError] = useState<string | null>(null);

  const togglePref = (label: string) => {
    setActivePrefs((prev) => {
      const next = new Set(prev);
      next.has(label) ? next.delete(label) : next.add(label);
      return next;
    });
  };

  const handleStartShopping = () => {
    setIsSearching(true);
    extractRequirements(query, Array.from(activePrefs)).catch(() => null);
    setTimeout(() => {
      setIsSearching(false);
      onStartShopping();
    }, 2000);
  };

  useEffect(() => {
    let isMounted = true;
    fetchPinterestStatus()
      .then((status) => {
        if (isMounted) setIsPinterestConnected(status.connected);
      })
      .catch(() => {
        if (isMounted) setIsPinterestConnected(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handlePinterestConnect = async () => {
    setIsPinterestLoading(true);
    setPinterestError(null);
    try {
      const { oauth_url } = await fetchPinterestLoginUrl();
      window.location.href = oauth_url;
    } catch {
      setIsPinterestLoading(false);
      setPinterestError("Failed to start Pinterest connection. Is the backend running?");
      // eslint-disable-next-line no-console
      console.error("Pinterest login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-lg"
      >
        {/* Logo */}
        <div className="text-center mb-10">
          <motion.div
            className="inline-flex items-center gap-2.5 mb-3"
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="w-10 h-10 rounded-xl gradient-bg flex items-center justify-center shadow-glow">
              <ShoppingBag className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Agentic Commerce
            </h1>
          </motion.div>
          <p className="text-muted-foreground text-sm">
            Tell me what you need. I'll find the best deals across the web.
          </p>
        </div>

        {/* Search Input */}
        <motion.div
          className="glass-panel rounded-2xl p-1.5 shadow-card mb-5 focus-within:shadow-card-hover transition-shadow duration-300"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-2 px-3">
            <Search className="w-4 h-4 text-muted-foreground shrink-0" />
            <input
              type="text"
              placeholder="I need headphones, running shoes, a smart watch..."
              className="flex-1 py-3 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              onClick={() => setIsListening(!isListening)}
              className={`p-2 rounded-xl transition-all duration-200 ${
                isListening
                  ? "gradient-bg text-primary-foreground animate-pulse-glow"
                  : "hover:bg-secondary text-muted-foreground"
              }`}
            >
              <Mic className="w-4 h-4" />
            </button>
          </div>
        </motion.div>

        {/* Preferences */}
        <motion.div
          className="mb-5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <p className="text-xs font-medium text-muted-foreground mb-2.5 uppercase tracking-wider">
            Preferences
          </p>
          <div className="flex flex-wrap gap-2">
            {preferences.map((pref) => {
              const isActive = activePrefs.has(pref.label);
              return (
                <button
                  key={pref.label}
                  onClick={() => togglePref(pref.label)}
                  className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? "gradient-bg text-primary-foreground shadow-glow"
                      : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                  }`}
                >
                  <pref.icon className="w-3.5 h-3.5" />
                  {pref.label}
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Pinterest Import */}
        <motion.div
          className="mb-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {isPinterestConnected ? (
            <div className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-border bg-secondary/40 text-xs font-medium text-secondary-foreground">
              <Image className="w-3.5 h-3.5" />
              Pinterest is connected
            </div>
          ) : (
            <button
              onClick={handlePinterestConnect}
              disabled={isPinterestLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-border text-muted-foreground text-xs font-medium hover:border-primary/40 hover:text-primary transition-all duration-200 disabled:opacity-60"
            >
              <Image className="w-3.5 h-3.5" />
              {isPinterestLoading ? "Connecting..." : "Import from Pinterest board"}
            </button>
          )}
          {pinterestError ? (
            <p className="mt-2 text-[11px] text-destructive text-center">{pinterestError}</p>
          ) : null}
        </motion.div>

        {/* Start Shopping Button */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Button
            onClick={handleStartShopping}
            disabled={isSearching}
            className="w-full gradient-bg text-primary-foreground py-6 rounded-2xl text-sm font-semibold shadow-glow hover:opacity-90 transition-opacity border-0"
          >
            <AnimatePresence mode="wait">
              {isSearching ? (
                <motion.div
                  key="searching"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2"
                >
                  <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Finding the best deals...
                </motion.div>
              ) : (
                <motion.div
                  key="start"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  Start Shopping
                </motion.div>
              )}
            </AnimatePresence>
          </Button>
        </motion.div>

        <p className="text-center text-[11px] text-muted-foreground/60 mt-4">
          AI-powered · Searches 50+ retailers · Prices verified in real-time
        </p>
      </motion.div>
    </div>
  );
}
