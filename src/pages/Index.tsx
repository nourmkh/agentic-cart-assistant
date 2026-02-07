import { useNavigate } from "react-router-dom";
import { FloatingBubble } from "@/components/FloatingBubble";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      {/* Landing content placeholder */}
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-3">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            Welcome to <span className="gradient-text">Agentic Commerce</span>
          </h1>
          <p className="text-muted-foreground text-lg max-w-md mx-auto">
            Click the floating bubble to start your AI-powered shopping experience.
          </p>
        </div>
      </div>

      <FloatingBubble onStartShopping={() => navigate("/cart")} />
    </div>
  );
};

export default Index;
