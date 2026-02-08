import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Star, Info, ChevronDown, Minus, Plus, ArrowRightLeft, ExternalLink, Trash2 } from "lucide-react";
import type { Product } from "@/types/product";
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

interface ProductCardProps {
  product: Product;
  index: number;
  quantity: number;
  onQuantityChange: (id: string, qty: number) => void;
  onSwap: (productId: string, altId: string) => void;
}

export function ProductCard({ product, index, quantity, onQuantityChange, onSwap }: ProductCardProps) {
  const [showAlts, setShowAlts] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="glass-panel rounded-2xl overflow-hidden shadow-card hover:shadow-card-hover transition-all duration-300 group"
    >
      {/* Image */}
      <div className="relative aspect-square bg-secondary/50 overflow-hidden">
        <img
          src={getImageSrc(product.image)}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        {/* Match Score Badge */}
        <div className="absolute top-3 left-3 gradient-bg text-primary-foreground text-[11px] font-bold px-2.5 py-1 rounded-lg shadow-glow">
          {product.matchScore}% match
        </div>
        {/* Remove item */}
        <button
          type="button"
          onClick={() => onQuantityChange(product.id, 0)}
          className="absolute bottom-3 right-3 p-2 rounded-lg bg-background/90 hover:bg-destructive/90 text-muted-foreground hover:text-destructive-foreground transition-colors shadow-sm"
          title="Remove from cart"
          aria-label="Remove from cart"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div>
            <p className="text-[11px] font-medium text-muted-foreground">{product.brand}</p>
            <h3 className="text-sm font-semibold text-foreground leading-tight">{product.name}</h3>
          </div>
          {/* Why Suggested Tooltip */}
          <div className="relative">
            <button
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              className="p-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-primary"
            >
              <Info className="w-3.5 h-3.5" />
            </button>
            <AnimatePresence>
              {showTooltip && (
                <motion.div
                  initial={{ opacity: 0, y: 4, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 4, scale: 0.95 }}
                  className="absolute right-0 top-full mt-1 w-56 p-3 rounded-xl glass-panel shadow-card-hover z-20 text-xs text-foreground leading-relaxed"
                >
                  <p className="font-semibold gradient-text mb-1">Why Suggested?</p>
                  {product.whySuggested}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Rating & Retailer */}
        <div className="flex items-center gap-2 mb-2">
          <div className="flex items-center gap-0.5">
            <Star className="w-3 h-3 fill-accent text-accent" />
            <span className="text-xs font-medium text-foreground">{product.rating}</span>
          </div>
          <span className="text-[11px] text-muted-foreground">· {product.retailer}</span>
          <span className="text-[11px] font-semibold bg-secondary/80 px-1.5 py-0.5 rounded ml-auto">{product.size}</span>
        </div>

        {/* Price */}
        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-lg font-bold text-foreground">${product.price}</span>
        </div>

        <p className="text-[11px] text-accent font-medium mb-3">{product.delivery}</p>

        {/* View on retailer site (Zara, Stradivarius, etc.) */}
        {product.url && (
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[11px] text-accent hover:underline mb-3"
          >
            <ExternalLink className="w-3 h-3" />
            View on {product.retailer}
          </a>
        )}

        {/* Quantity Selector */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-muted-foreground">Qty</span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onQuantityChange(product.id, Math.max(0, quantity - 1))}
              className="p-1 rounded-lg hover:bg-secondary transition-colors text-muted-foreground"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <span className="w-8 text-center text-sm font-medium text-foreground">{quantity}</span>
            <button
              onClick={() => onQuantityChange(product.id, quantity + 1)}
              className="p-1 rounded-lg hover:bg-secondary transition-colors text-muted-foreground"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Alternatives Toggle */}
        <button
          onClick={() => setShowAlts(!showAlts)}
          className="w-full flex items-center justify-between py-2 text-xs text-muted-foreground hover:text-primary transition-colors"
        >
          <span className="flex items-center gap-1">
            <ArrowRightLeft className="w-3 h-3" />
            3 alternatives
          </span>
          <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${showAlts ? "rotate-180" : ""}`} />
        </button>

        <AnimatePresence>
          {showAlts && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="space-y-1.5 pt-1">
                {product.alternatives.map((alt) => (
                  <button
                    key={alt.id}
                    onClick={() => onSwap(product.id, alt.id)}
                    className="w-full flex items-center justify-between p-2 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors text-xs"
                  >
                    <span className="text-foreground font-medium">{alt.brand} {alt.name}</span>
                    <span className="text-muted-foreground font-medium">${alt.price}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
