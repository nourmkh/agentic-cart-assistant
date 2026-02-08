import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const CARD_WIDTH = 340;
const CARD_HEIGHT = 220;

function formatCardNumber(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

function formatExpiry(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 4);
  if (digits.length >= 2) {
    return `${digits.slice(0, 2)} / ${digits.slice(2)}`;
  }
  return digits;
}

type CardType = "visa" | "mastercard" | "amex" | "discover" | null;

function getCardType(cardNumber: string): CardType {
  const digits = cardNumber.replace(/\D/g, "");
  if (digits.length < 2) return null;
  const first = digits[0];
  const firstTwo = digits.slice(0, 2);
  const firstThree = digits.slice(0, 3);
  const firstFour = digits.slice(0, 4);
  const firstSix = digits.slice(0, 6);
  if (first === "4") return "visa";
  if (firstTwo === "34" || firstTwo === "37") return "amex";
  if (firstTwo >= "51" && firstTwo <= "55") return "mastercard";
  if (firstSix >= "2221" && firstSix <= "2720") return "mastercard";
  if (firstFour === "6011" || firstTwo === "65") return "discover";
  if (firstThree >= "644" && firstThree <= "649") return "discover";
  if (firstSix >= "622126" && firstSix <= "622925") return "discover";
  return null;
}

export interface RotatingCard3DProps {
  cardNumber: string;
  cardName: string;
  expiry: string;
  cvc: string;
  isFlipped: boolean;
  className?: string;
}

export function RotatingCard3D({
  cardNumber,
  cardName,
  expiry,
  cvc,
  isFlipped,
  className,
}: RotatingCard3DProps) {
  const displayNumber = formatCardNumber(cardNumber) || "•••• •••• •••• ••••";
  const displayName = cardName || "CARDHOLDER NAME";
  const displayExpiry = formatExpiry(expiry) || "MM / YY";
  const displayCvc = cvc || "•••";
  const cardType = getCardType(cardNumber);
  const cardTypeLabel = cardType
    ? cardType.charAt(0).toUpperCase() + cardType.slice(1)
    : null;

  return (
    <div
      className={cn("flex justify-center items-center py-2", className)}
      style={{
        perspective: "1000px",
        minHeight: CARD_HEIGHT,
      }}
    >
      <motion.div
        className="relative"
        style={{
          width: CARD_WIDTH,
          height: CARD_HEIGHT,
          transformStyle: "preserve-3d",
        }}
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        {/* Front face */}
        <div
          className="absolute inset-0 rounded-[0.6rem] overflow-hidden"
          style={{
            backfaceVisibility: "hidden",
            WebkitBackfaceVisibility: "hidden",
            background: "linear-gradient(145deg, hsl(220 30% 18%) 0%, hsl(220 25% 12%) 50%, hsl(220 30% 16%) 100%)",
            boxShadow:
              "0 4px 20px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.05) inset, 0 1px 0 rgba(255,255,255,0.1)",
          }}
        >
          {/* Subtle holographic strip */}
          <div
            className="absolute top-0 right-0 w-24 h-full opacity-30"
            style={{
              background: "linear-gradient(105deg, transparent 0%, rgba(255,255,255,0.15) 30%, rgba(180,220,255,0.2) 50%, rgba(255,255,255,0.1) 70%, transparent 100%)",
            }}
          />
          <div className="absolute inset-0 p-5 flex flex-col justify-between text-white">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2">
                {/* EMV Chip (puce) - gold chip with chamfered corner */}
                <div
                className="relative w-12 h-9 flex-shrink-0"
                style={{
                  background: "linear-gradient(135deg, #e8d48b 0%, #d4af37 20%, #c9a227 50%, #b8860b 80%, #daa520 100%)",
                  boxShadow:
                    "0 1px 3px rgba(0,0,0,0.5) inset, 0 1px 0 rgba(255,255,255,0.4), 0 2px 4px rgba(0,0,0,0.3)",
                  clipPath: "polygon(0 0, 100% 0, 100% 100%, 8px 100%, 0 calc(100% - 8px))",
                }}
              >
                {/* Circuit lines inside chip */}
                <div className="absolute inset-1 overflow-hidden rounded-[1px]">
                  <svg width="100%" height="100%" viewBox="0 0 40 28" className="opacity-30">
                    <path d="M8 4h4M8 8h8M8 12h6M8 16h10" stroke="rgba(0,0,0,0.4)" strokeWidth="0.8" strokeLinecap="round" />
                    <path d="M20 4v6M24 4v8M28 4v4" stroke="rgba(0,0,0,0.4)" strokeWidth="0.8" strokeLinecap="round" />
                    <rect x="16" y="14" width="4" height="4" rx="0.5" fill="rgba(0,0,0,0.2)" />
                    <path d="M4 20h12M4 24h8" stroke="rgba(0,0,0,0.3)" strokeWidth="0.6" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
                {/* Contactless waves */}
                <svg width="22" height="16" viewBox="0 0 24 16" fill="none" className="opacity-60 flex-shrink-0">
                  <path
                    d="M6 8a3 3 0 0 0 0 6M10 8a7 7 0 0 0 0 6M14 8a7 7 0 0 1 0 6M18 8a3 3 0 0 1 0 6"
                    stroke="currentColor"
                    strokeWidth="1"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <span className="text-[10px] uppercase tracking-[0.15em] font-semibold text-white/90 drop-shadow-sm">
                {cardTypeLabel ?? "Card"}
              </span>
            </div>
            <div>
              <p className="font-mono text-[1.05rem] tracking-[0.25em] mb-4 text-white/95" style={{ textShadow: "0 1px 2px rgba(0,0,0,0.3)" }}>
                {displayNumber}
              </p>
              <div className="flex justify-between items-end">
                <div>
                  <p className="text-[8px] uppercase tracking-[0.2em] text-white/60 mb-0.5">Cardholder</p>
                  <p className="text-xs uppercase tracking-widest truncate max-w-[180px] text-white/95" style={{ textShadow: "0 1px 1px rgba(0,0,0,0.2)" }}>
                    {displayName}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[8px] uppercase tracking-[0.2em] text-white/60 mb-0.5">Expires</p>
                  <p className="font-mono text-xs tracking-[0.15em] text-white/95" style={{ textShadow: "0 1px 1px rgba(0,0,0,0.2)" }}>
                    {displayExpiry}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Back face */}
        <div
          className="absolute inset-0 rounded-[0.6rem] overflow-hidden"
          style={{
            backfaceVisibility: "hidden",
            WebkitBackfaceVisibility: "hidden",
            transform: "rotateY(180deg)",
            background: "linear-gradient(145deg, hsl(220 30% 18%) 0%, hsl(220 25% 12%) 50%, hsl(220 30% 16%) 100%)",
            boxShadow:
              "0 4px 20px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.05) inset, 0 1px 0 rgba(255,255,255,0.1)",
          }}
        >
          <div className="absolute inset-0 p-5 flex flex-col text-white">
            {/* Magnetic stripe */}
            <div
              className="h-9 -mx-5 mt-4"
              style={{ background: "linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 50%, #1a1a1a 100%)" }}
            />
            {/* Signature / CVC strip */}
            <div className="flex-1 flex items-center mt-4 gap-4">
              <div className="flex-1 h-8 rounded-sm bg-white/90 flex items-center px-3">
                <span className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">Authorized signature</span>
              </div>
              <div className="w-14 shrink-0">
                <p className="text-[8px] uppercase tracking-[0.15em] text-white/60 mb-1">CVV</p>
                <div
                  className="h-8 rounded-sm flex items-center justify-end px-2 font-mono text-sm tracking-wider text-gray-900"
                  style={{ background: "linear-gradient(180deg, #f5f5f5 0%, #e8e8e8 100%)" }}
                >
                  {displayCvc}
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
