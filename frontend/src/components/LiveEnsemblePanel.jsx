import { useState, useEffect, useRef } from 'react';
import { BrainCircuit, Activity, Shield, Flame, Cpu, Zap, Target, AlertTriangle, Bot } from 'lucide-react';

const STRATEGY_COLORS = {
  ESCALATE_TARPIT: { border: 'border-neon-red/40', bg: 'bg-neon-red/10', text: 'text-neon-red', label: 'AGGRESSIVE TARPIT' },
  MAINTAIN_ENGAGEMENT: { border: 'border-neon-amber/40', bg: 'bg-neon-amber/10', text: 'text-neon-amber', label: 'SUSTAIN ENGAGEMENT' },
  DEPLOY_HONEYCRED: { border: 'border-neon-purple/40', bg: 'bg-neon-purple/10', text: 'text-neon-purple', label: 'DEPLOY HONEYCREDS' },
};

function AnimatedNumber({ value, decimals = 1, duration = 600 }) {
  const [display, setDisplay] = useState(value);
  const frameRef = useRef(null);

  useEffect(() => {
    const start = display;
    const end = value;
    const startTime = performance.now();

    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(start + (end - start) * eased);
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value]);

  return <>{display.toFixed(decimals)}</>;
}

export default function LiveEnsemblePanel({ ensembleData, aiNarration, active }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (ensembleData && ensembleData.ensemble_threat_score !== undefined) {
      setHistory(prev => [...prev.slice(-19), {
        score: ensembleData.ensemble_threat_score,
        time: Date.now(),
      }]);
    }
  }, [ensembleData]);

  if (!ensembleData || ensembleData.error) {
    return (
      <div className="glass-card p-4 relative overflow-hidden animate-fade-in">
        <div className="flex items-center gap-2 mb-3">
          <BrainCircuit className="w-4 h-4 text-neon-cyan" />
          <span className="font-[Orbitron] text-xs font-semibold text-neon-cyan tracking-wider">
            NEURAL ENSEMBLE ENGINE
          </span>
        </div>
        <div className="text-center py-6 text-gray-500 text-sm font-mono">
          {ensembleData?.error === 'Models not trained yet'
            ? <div className="space-y-2">
                <AlertTriangle className="w-6 h-6 mx-auto text-neon-amber animate-pulse" />
                <div className="text-neon-amber">ENSEMBLE NOT TRAINED</div>
                <div className="text-xs text-gray-400">Go to Neural Analytics → Train Models first</div>
              </div>
            : <div className="space-y-2">
                <Cpu className="w-6 h-6 mx-auto text-gray-600 animate-pulse" />
                <div>Awaiting live session data...</div>
              </div>
          }
        </div>
      </div>
    );
  }

  const { isolation_forest, xgboost, frustration_index, ensemble_threat_score, tarpit_strategy, tarpit_action } = ensembleData;
  const stratStyle = STRATEGY_COLORS[tarpit_strategy] || STRATEGY_COLORS.MAINTAIN_ENGAGEMENT;

  const threatColor = ensemble_threat_score > 75 ? 'text-neon-red'
    : ensemble_threat_score > 40 ? 'text-neon-amber'
    : 'text-neon-green';

  const threatBg = ensemble_threat_score > 75 ? 'bg-neon-red'
    : ensemble_threat_score > 40 ? 'bg-neon-amber'
    : 'bg-neon-green';

  const frustColor = frustration_index > 70 ? 'text-neon-red'
    : frustration_index > 30 ? 'text-neon-amber'
    : 'text-neon-cyan';

  // Mini sparkline
  const maxScore = Math.max(...history.map(h => h.score), 1);
  const sparkPoints = history.map((h, i) => {
    const x = (i / Math.max(history.length - 1, 1)) * 100;
    const y = 100 - (h.score / Math.max(maxScore, 100)) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="glass-card p-4 relative overflow-hidden animate-fade-in border border-white/5">
      {/* Pulse overlay on high threat */}
      {ensemble_threat_score > 75 && (
        <div className="absolute inset-0 bg-neon-red/5 animate-pulse pointer-events-none" />
      )}

      <div className="flex items-center justify-between mb-4 relative z-10">
        <h3 className="font-[Orbitron] text-sm text-neon-cyan font-bold flex items-center gap-2">
          <BrainCircuit className={`w-4 h-4 ${active ? 'animate-pulse' : ''}`} />
          NEURAL ENSEMBLE ENGINE
        </h3>
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded border ${stratStyle.border} ${stratStyle.bg}`}>
          <Zap className={`w-3 h-3 ${stratStyle.text}`} />
          <span className={`text-[10px] font-[Orbitron] tracking-wider ${stratStyle.text}`}>
            {stratStyle.label}
          </span>
        </div>
      </div>

      <div className="space-y-3 relative z-10">
        {/* ── Threat Score Hero ── */}
        <div className="flex items-center gap-4 p-3 bg-black/40 rounded border border-white/10">
          <div className="text-center min-w-[80px]">
            <div className={`font-[Orbitron] text-3xl font-bold ${threatColor}`}>
              <AnimatedNumber value={ensemble_threat_score} />
            </div>
            <div className="text-[9px] text-gray-500 font-mono tracking-wider mt-0.5">THREAT / 100</div>
          </div>
          <div className="flex-1 space-y-2">
            <div className="h-2 bg-black/60 rounded-full overflow-hidden">
              <div
                className={`h-full ${threatBg} transition-all duration-700 rounded-full`}
                style={{
                  width: `${Math.min(100, ensemble_threat_score)}%`,
                  boxShadow: ensemble_threat_score > 50 ? `0 0 12px currentColor` : 'none'
                }}
              />
            </div>
            {/* Sparkline */}
            {history.length > 1 && (
              <svg viewBox="0 0 100 100" className="w-full h-6" preserveAspectRatio="none">
                <polyline
                  points={sparkPoints}
                  fill="none"
                  stroke={ensemble_threat_score > 75 ? '#FF3131' : ensemble_threat_score > 40 ? '#F59E0B' : '#00FF41'}
                  strokeWidth="2"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            )}
          </div>
        </div>

        {/* ── Model Results Grid ── */}
        <div className="grid grid-cols-3 gap-2">
          {/* Isolation Forest */}
          <div className={`p-2.5 rounded border ${isolation_forest?.is_anomaly ? 'border-neon-red/30 bg-neon-red/5' : 'border-neon-green/20 bg-neon-green/5'}`}>
            <div className="flex items-center gap-1 mb-1.5">
              <Shield className={`w-3 h-3 ${isolation_forest?.is_anomaly ? 'text-neon-red' : 'text-neon-green'}`} />
              <span className="text-[9px] font-mono text-gray-400 tracking-wider">ISO FOREST</span>
            </div>
            <div className={`text-xs font-[Orbitron] font-bold ${isolation_forest?.is_anomaly ? 'text-neon-red animate-pulse' : 'text-neon-green'}`}>
              {isolation_forest?.is_anomaly ? 'ANOMALY' : 'NORMAL'}
            </div>
          </div>

          {/* XGBoost */}
          <div className={`p-2.5 rounded border ${xgboost?.prediction === 1 ? 'border-neon-red/30 bg-neon-red/5' : 'border-neon-green/20 bg-neon-green/5'}`}>
            <div className="flex items-center gap-1 mb-1.5">
              <Target className={`w-3 h-3 ${xgboost?.prediction === 1 ? 'text-neon-red' : 'text-neon-green'}`} />
              <span className="text-[9px] font-mono text-gray-400 tracking-wider">XGBOOST</span>
            </div>
            <div className={`text-xs font-[Orbitron] font-bold ${xgboost?.prediction === 1 ? 'text-neon-red' : 'text-neon-green'}`}>
              {xgboost?.malicious_prob ?? 0}%
            </div>
            <div className="text-[8px] text-gray-500 font-mono mt-0.5">
              {xgboost?.prediction === 1 ? 'MALICIOUS' : 'BENIGN'}
            </div>
          </div>

          {/* Frustration */}
          <div className="p-2.5 rounded border border-white/10 bg-black/30">
            <div className="flex items-center gap-1 mb-1.5">
              <Flame className={`w-3 h-3 ${frustColor}`} />
              <span className="text-[9px] font-mono text-gray-400 tracking-wider">FRUSTRATION</span>
            </div>
            <div className={`text-xs font-[Orbitron] font-bold ${frustColor}`}>
              <AnimatedNumber value={frustration_index} />
            </div>
            <div className="text-[8px] text-gray-500 font-mono mt-0.5">
              {frustration_index > 70 ? 'BREAKING' : frustration_index > 30 ? 'RISING' : 'STABLE'}
            </div>
          </div>
        </div>

        {/* ── Tarpit Action ── */}
        <div className={`p-3 rounded border ${stratStyle.border} ${stratStyle.bg}`}>
          <div className="flex items-center gap-2 mb-1">
            <Bot className={`w-3.5 h-3.5 ${stratStyle.text}`} />
            <span className="text-[10px] font-mono text-gray-400 tracking-wider">ADAPTIVE DEFENSE ACTION</span>
          </div>
          <div className="text-xs text-gray-200 font-mono">
            {tarpit_action}
          </div>
        </div>

        {/* ── AI Logic Layer Narration ── */}
        {aiNarration && (
          <div className="p-3 rounded border border-neon-blue/20 bg-neon-blue/5 relative">
            <div className="absolute -top-2.5 left-3 bg-[#0a0e1a] px-2">
              <span className="text-[9px] font-[Orbitron] text-neon-blue tracking-wider">AI LOGIC LAYER</span>
            </div>
            <div className="text-xs text-gray-300 leading-relaxed mt-1 font-mono">
              {aiNarration}
            </div>
          </div>
        )}

        {/* ── XGBoost Confidence Bar ── */}
        <div className="p-2 rounded border border-white/5 bg-black/20">
          <div className="flex items-center justify-between text-[9px] font-mono text-gray-500 mb-1">
            <span>XGBOOST CONFIDENCE</span>
            <span className="text-neon-blue">{xgboost?.confidence ?? 0}%</span>
          </div>
          <div className="h-1 bg-black/60 rounded-full overflow-hidden">
            <div
              className="h-full bg-neon-blue transition-all duration-500 rounded-full"
              style={{ width: `${xgboost?.confidence ?? 0}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
