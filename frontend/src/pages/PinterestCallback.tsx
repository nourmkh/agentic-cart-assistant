import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { completePinterestCallback } from "@/api/pinterest";

const PinterestCallback = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [message, setMessage] = useState("Connecting Pinterest...");

  const query = useMemo(() => new URLSearchParams(location.search), [location.search]);

  useEffect(() => {
    const code = query.get("code");
    const state = query.get("state") ?? undefined;

    if (!code) {
      setMessage("Missing authorization code.");
      return;
    }

    completePinterestCallback(code, state)
      .then(() => {
        setMessage("Pinterest connected. Redirecting...");
        setTimeout(() => navigate("/"), 800);
      })
      .catch(() => {
        setMessage("Failed to connect Pinterest.");
      });
  }, [navigate, query]);

  return (
    <div className="min-h-screen flex items-center justify-center text-sm text-muted-foreground">
      {message}
    </div>
  );
};

export default PinterestCallback;
