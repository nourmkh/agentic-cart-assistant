import { motion } from "framer-motion";
import { Check, Info } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAgentLogs } from "@/api/agent";

export function AgentLog() {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);
  const { data: agentLogs = [] } = useQuery({ queryKey: ["agentLogs"], queryFn: fetchAgentLogs });

  return (
    <div className="glass-panel rounded-2xl p-5 shadow-card">
      <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
        <div className="w-5 h-5 rounded-md gradient-bg flex items-center justify-center">
          <Info className="w-3 h-3 text-primary-foreground" />
        </div>
        Agent Activity Log
      </h3>
      <div className="space-y-2.5">
        {agentLogs.map((log, i) => (
          <motion.div
            key={log.step}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            onMouseEnter={() => setHoveredStep(log.step)}
            onMouseLeave={() => setHoveredStep(null)}
            className="flex items-start gap-3 p-2 rounded-lg hover:bg-secondary/50 transition-colors cursor-default relative"
          >
            <div className="w-5 h-5 rounded-full bg-accent/10 flex items-center justify-center shrink-0 mt-0.5">
              <Check className="w-3 h-3 text-accent" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-foreground">{log.action}</p>
                <span className="text-[10px] font-mono text-muted-foreground">{log.time}</span>
              </div>
              {hoveredStep === log.step && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="text-[11px] text-muted-foreground mt-0.5"
                >
                  {log.detail}
                </motion.p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
