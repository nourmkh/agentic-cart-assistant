import { useState, useRef } from "react";
import { motion, AnimatePresence, useDragControls } from "framer-motion";
import { ShoppingBag, X } from "lucide-react";
import { SearchSidebar } from "@/components/SearchSidebar";

interface FloatingBubbleProps {
  onStartShopping: () => void;
}

export function FloatingBubble({ onStartShopping }: FloatingBubbleProps) {
  const [isOpen, setIsOpen] = useState(false);
  const constraintsRef = useRef<HTMLDivElement>(null);

  const handleStartShopping = () => {
    setIsOpen(false);
    onStartShopping();
  };

  return (
    <>
      {/* Full-screen drag constraint area */}
      <div ref={constraintsRef} className="fixed inset-0 pointer-events-none z-[9998]" />

      {/* Draggable Bubble */}
      <motion.div
        drag
        dragConstraints={constraintsRef}
        dragElastic={0.1}
        dragMomentum={false}
        initial={{ x: 0, y: 0, scale: 0 }}
        animate={{ scale: isOpen ? 0 : 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-[9999] w-14 h-14 rounded-full gradient-bg shadow-glow cursor-grab active:cursor-grabbing flex items-center justify-center pointer-events-auto"
        style={{ touchAction: "none" }}
      >
        <ShoppingBag className="w-6 h-6 text-primary-foreground" />
        {/* Pulse ring */}
        <span className="absolute inset-0 rounded-full gradient-bg animate-ping opacity-20" />
      </motion.div>

      {/* Popup Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[9999]"
            />

            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 40 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 40 }}
              transition={{ type: "spring", stiffness: 350, damping: 30 }}
              className="fixed bottom-6 right-6 z-[10000] w-[420px] max-w-[calc(100vw-2rem)] max-h-[calc(100vh-3rem)] rounded-3xl bg-background border border-border shadow-card-hover overflow-hidden"
            >
              {/* Close button */}
              <button
                onClick={() => setIsOpen(false)}
                className="absolute top-4 right-4 z-10 p-1.5 rounded-full bg-secondary hover:bg-secondary/80 text-muted-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Embedded SearchSidebar */}
              <div className="overflow-y-auto max-h-[calc(100vh-4rem)]">
                <SearchSidebar onStartShopping={handleStartShopping} />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
