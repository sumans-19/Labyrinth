import { useState, useEffect, useCallback } from 'react';
import {
  BrainCircuit, Activity, Target, Zap, Play, RefreshCw,
  TrendingUp, BarChart3, Gauge, ShieldAlert, CheckCircle2,
  AlertTriangle, Crosshair, Cpu, Database, ArrowLeft
} from 'lucide-react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, Legend, Cell
} from 'recharts';

const API = `http://${window.location.hostname}:8000`;

const NEON = {
  blue: '#3b82f6', purple: '#a855f7', green: '#22c55e',
  red: '#ef4444', amber: '#f59e0b', cyan: '#06b6d4'
};

function GlassCard({ children, className = '', glow }) {
  return (
    <div className={`relative bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl p-5 overflow-hidden ${className}`}
      style={glow ? { boxShadow: `0 0 30px ${glow}22` } : {}}>
      {children}
    </div>
  );
}

function SectionLabel({ icon: Icon, label, color = 'text-neon-blue' }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon className={`w-4 h-4 ${color}`} />
      <span className={`font-[Orbitron] text-xs tracking-[0.2em] font-bold ${color}`}>{label}</span>
    </div>
  );
}

function MetricPill({ label, value, color = 'text-neon-green' }) {
  return (
    <div className="flex flex-col items-center p-3 bg-black/40 border border-white/5 rounded-lg min-w-[100px]">
      <span className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">{label}</span>
      <span className={`text-lg font-[Orbitron] font-black ${color}`}>{value}</span>
    </div>
  );
}

export default function NeuralAnalytics({ onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [trained, setTrained] = useState(false);
  const [predResult, setPredResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [animIdx, setAnimIdx] = useState(0);

  // Check status on mount
  useEffect(() => {
    fetch(`${API}/api/ensemble/status`).then(r => r.json()).then(d => {
      if (d.trained) { setTrained(true); fetchEval(); }
    }).catch(() => {});
  }, []);

  const fetchEval = useCallback(() => {
    fetch(`${API}/api/ensemble/evaluate`).then(r => r.json()).then(d => {
      if (!d.error) setData(d);
    }).catch(() => {});
  }, []);

  const handleTrain = async () => {
    setLoading(true); setAnimIdx(0);
    try {
      const r = await fetch(`${API}/api/ensemble/train`, { method: 'POST' });
      const d = await r.json();
      setData({ training_history: d.training_history, evaluation: d.evaluation });
      setTrained(true);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  // Animate training curves
  useEffect(() => {
    if (!data?.training_history) return;
    const max = data.training_history.filter(h => h.model === 'Isolation Forest').length;
    if (animIdx < max) {
      const t = setTimeout(() => setAnimIdx(i => i + 1), 150);
      return () => clearTimeout(t);
    }
  }, [data, animIdx]);

  const handlePredict = async () => {
    setPredicting(true);
    try {
      const r = await fetch(`${API}/api/ensemble/predict`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avg_keystroke_delay_ms: 60, typing_speed_wpm: 110, error_rate_pct: 22,
          command_diversity: 0.2, session_duration_s: 300, unique_commands: 35,
          dangerous_cmd_ratio: 0.55, time_between_commands_ms: 600,
          backspace_frequency: 0.3, paste_frequency: 0.45
        })
      });
      setPredResult(await r.json());
    } catch (e) { console.error(e); }
    setPredicting(false);
  };

  // Prepare chart data
  const getModelHistory = (model) => (data?.training_history || []).filter(h => h.model === model).slice(0, animIdx);
  const isoHistory = getModelHistory('Isolation Forest');
  const xgbHistory = getModelHistory('XGBoost');
  const frHistory = getModelHistory('Frustration Regressor');

  const ev = data?.evaluation || {};
  const rocData = ev.xgboost?.roc_curve ? ev.xgboost.roc_curve.fpr.map((f, i) => ({ fpr: f, tpr: ev.xgboost.roc_curve.tpr[i] })) : [];
  const featureImp = ev.xgboost?.feature_importance || [];
  const frustImp = ev.frustration_regressor?.feature_importance || [];

  const frustGauge = predResult ? [{ name: 'Frustration', value: predResult.frustration_index, fill: predResult.frustration_index > 70 ? NEON.red : predResult.frustration_index > 30 ? NEON.amber : NEON.green }] : [];

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-10 animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          {onNavigate && (
            <button onClick={() => onNavigate('internalthreat')} className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 transition-colors">
              <ArrowLeft className="w-5 h-5 text-gray-400" />
            </button>
          )}
          <div className="p-3 bg-neon-purple/10 border border-neon-purple/20 rounded-xl">
            <BrainCircuit className="w-8 h-8 text-neon-purple" />
          </div>
          <div>
            <h1 className="font-[Orbitron] text-2xl font-black text-white tracking-widest">NEURAL ANALYTICS</h1>
            <p className="text-[10px] text-gray-500 font-mono tracking-widest mt-1">MODEL EVALUATION &bull; ENSEMBLE TRAINING &bull; ATTACKER FRUSTRATION INDEX</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={handleTrain} disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-neon-purple/20 to-neon-blue/20 border border-neon-purple/40 rounded-lg text-neon-purple font-[Orbitron] text-xs tracking-wider hover:from-neon-purple/30 hover:to-neon-blue/30 transition-all disabled:opacity-50 cursor-pointer">
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? 'TRAINING...' : 'TRAIN ENSEMBLE'}
          </button>
          {trained && (
            <button onClick={handlePredict} disabled={predicting}
              className="flex items-center gap-2 px-5 py-2.5 bg-neon-red/10 border border-neon-red/30 rounded-lg text-neon-red font-[Orbitron] text-xs tracking-wider hover:bg-neon-red/20 transition-all cursor-pointer">
              {predicting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Crosshair className="w-4 h-4" />}
              TEST PREDICTION
            </button>
          )}
        </div>
      </div>

      {/* Not trained state */}
      {!trained && !loading && (
        <GlassCard className="text-center py-16">
          <Cpu className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 font-mono text-sm">No models trained yet. Click <span className="text-neon-purple font-bold">TRAIN ENSEMBLE</span> to begin.</p>
        </GlassCard>
      )}

      {/* Model Status Cards */}
      {trained && ev.isolation_forest && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Isolation Forest Card */}
          <GlassCard glow={NEON.cyan}>
            <SectionLabel icon={ShieldAlert} label="ISOLATION FOREST" color="text-neon-cyan" />
            <p className="text-[10px] text-gray-500 font-mono mb-3">Unsupervised Anomaly Detection</p>
            <div className="flex flex-wrap gap-2">
              <MetricPill label="Accuracy" value={`${ev.isolation_forest.accuracy}%`} />
              <MetricPill label="Precision" value={`${ev.isolation_forest.precision}%`} color="text-neon-cyan" />
              <MetricPill label="Recall" value={`${ev.isolation_forest.recall}%`} color="text-neon-amber" />
              <MetricPill label="F1" value={`${ev.isolation_forest.f1_score}%`} color="text-neon-purple" />
            </div>
            <p className="text-[9px] text-gray-600 font-mono mt-3 leading-relaxed">Detects unknown attacks by isolating anomalous behavioral patterns without labeled data. Contamination=0.3 flags top 30% most isolated points.</p>
          </GlassCard>

          {/* XGBoost Card */}
          <GlassCard glow={NEON.blue}>
            <SectionLabel icon={Zap} label="XGBOOST CLASSIFIER" color="text-neon-blue" />
            <p className="text-[10px] text-gray-500 font-mono mb-3">Supervised Classification</p>
            <div className="flex flex-wrap gap-2">
              <MetricPill label="Accuracy" value={`${ev.xgboost.accuracy}%`} />
              <MetricPill label="AUC" value={ev.xgboost.roc_auc} color="text-neon-blue" />
              <MetricPill label="Recall" value={`${ev.xgboost.recall}%`} color="text-neon-amber" />
              <MetricPill label="F1" value={`${ev.xgboost.f1_score}%`} color="text-neon-purple" />
            </div>
            <p className="text-[9px] text-gray-600 font-mono mt-3 leading-relaxed">High-speed classification distinguishing Benign Admin from Malicious Hacker with probability scores via gradient-boosted decision trees.</p>
          </GlassCard>

          {/* Frustration Card */}
          <GlassCard glow={NEON.amber}>
            <SectionLabel icon={Gauge} label="FRUSTRATION INDEX" color="text-neon-amber" />
            <p className="text-[10px] text-gray-500 font-mono mb-3">Novelty Regression Metric</p>
            <div className="flex flex-wrap gap-2">
              <MetricPill label="R² Score" value={`${ev.frustration_regressor.r2_score}%`} color="text-neon-amber" />
              <MetricPill label="MSE" value={ev.frustration_regressor.mse} color="text-neon-red" />
            </div>
            <p className="text-[9px] text-gray-600 font-mono mt-3 leading-relaxed">Predicts how close a hacker is to quitting. Low frustration → escalate tarpit. High frustration → leak fake credentials to keep them hooked.</p>
          </GlassCard>
        </div>
      )}

      {/* Training Curves */}
      {data?.training_history && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Accuracy Curves */}
          <GlassCard>
            <SectionLabel icon={TrendingUp} label="LIVE ACCURACY CURVES" color="text-neon-green" />
            <ResponsiveContainer width="100%" height={280}>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis dataKey="epoch" type="number" domain={[1, 10]} stroke="#555" tick={{ fontSize: 10, fill: '#666' }} label={{ value: 'Epoch', position: 'bottom', fill: '#555', fontSize: 10 }} />
                <YAxis stroke="#555" tick={{ fontSize: 10, fill: '#666' }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: '#0a0a0a', border: '1px solid #333', borderRadius: 8, fontSize: 11 }} />
                <Line data={isoHistory} dataKey="accuracy" name="Isolation Forest" stroke={NEON.cyan} strokeWidth={2} dot={{ r: 3 }} type="monotone" />
                <Line data={xgbHistory} dataKey="accuracy" name="XGBoost" stroke={NEON.blue} strokeWidth={2} dot={{ r: 3 }} type="monotone" />
                <Line data={frHistory} dataKey="accuracy" name="Frustration (R²)" stroke={NEON.amber} strokeWidth={2} dot={{ r: 3 }} type="monotone" />
                <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'monospace' }} />
              </LineChart>
            </ResponsiveContainer>
          </GlassCard>

          {/* Loss Curves */}
          <GlassCard>
            <SectionLabel icon={Activity} label="TRAINING LOSS CURVES" color="text-neon-red" />
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis dataKey="epoch" type="number" domain={[1, 10]} stroke="#555" tick={{ fontSize: 10, fill: '#666' }} />
                <YAxis stroke="#555" tick={{ fontSize: 10, fill: '#666' }} />
                <Tooltip contentStyle={{ background: '#0a0a0a', border: '1px solid #333', borderRadius: 8, fontSize: 11 }} />
                <Area data={isoHistory} dataKey="loss" name="IF Loss" stroke={NEON.cyan} fill={`${NEON.cyan}15`} strokeWidth={2} type="monotone" />
                <Area data={xgbHistory} dataKey="loss" name="XGB Loss" stroke={NEON.blue} fill={`${NEON.blue}15`} strokeWidth={2} type="monotone" />
                <Area data={frHistory} dataKey="loss" name="FR Loss" stroke={NEON.amber} fill={`${NEON.amber}15`} strokeWidth={2} type="monotone" />
                <Legend wrapperStyle={{ fontSize: 10, fontFamily: 'monospace' }} />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>
        </div>
      )}

      {/* ROC + Feature Importance */}
      {trained && ev.xgboost && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* ROC Curve */}
          <GlassCard>
            <SectionLabel icon={Target} label={`ROC / AUC CURVE — ${ev.xgboost.roc_auc}`} color="text-neon-purple" />
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={rocData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis dataKey="fpr" stroke="#555" tick={{ fontSize: 10, fill: '#666' }} label={{ value: 'False Positive Rate', position: 'bottom', fill: '#555', fontSize: 10 }} />
                <YAxis stroke="#555" tick={{ fontSize: 10, fill: '#666' }} label={{ value: 'True Positive Rate', angle: -90, position: 'insideLeft', fill: '#555', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#0a0a0a', border: '1px solid #333', borderRadius: 8, fontSize: 11 }} />
                <Area dataKey="tpr" stroke={NEON.purple} fill={`${NEON.purple}25`} strokeWidth={2.5} type="monotone" name="TPR" />
                <Line dataKey="fpr" stroke="#ffffff15" strokeDasharray="5 5" strokeWidth={1} type="linear" name="Random" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>

          {/* XGBoost Feature Importance */}
          <GlassCard>
            <SectionLabel icon={BarChart3} label="XGBOOST FEATURE IMPORTANCE" color="text-neon-blue" />
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={featureImp} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis type="number" stroke="#555" tick={{ fontSize: 10, fill: '#666' }} />
                <YAxis dataKey="feature" type="category" width={160} stroke="#555" tick={{ fontSize: 9, fill: '#999', fontFamily: 'monospace' }} />
                <Tooltip contentStyle={{ background: '#0a0a0a', border: '1px solid #333', borderRadius: 8, fontSize: 11 }} />
                <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                  {featureImp.map((_, i) => <Cell key={i} fill={[NEON.blue, NEON.purple, NEON.cyan, NEON.green, NEON.amber, NEON.red, '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'][i % 10]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </div>
      )}

      {/* Frustration Feature Importance */}
      {trained && frustImp.length > 0 && (
        <GlassCard>
          <SectionLabel icon={Gauge} label="FRUSTRATION INDEX — FEATURE WEIGHT MAP" color="text-neon-amber" />
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={frustImp} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
              <XAxis type="number" stroke="#555" tick={{ fontSize: 10, fill: '#666' }} />
              <YAxis dataKey="feature" type="category" width={160} stroke="#555" tick={{ fontSize: 9, fill: '#999', fontFamily: 'monospace' }} />
              <Tooltip contentStyle={{ background: '#0a0a0a', border: '1px solid #333', borderRadius: 8, fontSize: 11 }} />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {frustImp.map((_, i) => <Cell key={i} fill={[NEON.amber, NEON.red, '#f97316', '#eab308', '#d97706', '#b45309', '#92400e', '#78350f', '#fbbf24', '#fde68a'][i % 10]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>
      )}

      {/* Live Prediction Result */}
      {predResult && (
        <GlassCard glow={predResult.ensemble_threat_score > 60 ? NEON.red : NEON.green} className="animate-fade-in">
          <SectionLabel icon={Crosshair} label="LIVE ENSEMBLE PREDICTION" color="text-neon-red" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Anomaly + Classification */}
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-black/40 border border-white/5 rounded-lg">
                <div className={`w-3 h-3 rounded-full ${predResult.isolation_forest.is_anomaly ? 'bg-neon-red animate-pulse' : 'bg-neon-green'}`} />
                <div>
                  <div className="text-[10px] text-gray-500 font-mono">ISOLATION FOREST</div>
                  <div className={`text-sm font-[Orbitron] font-bold ${predResult.isolation_forest.is_anomaly ? 'text-neon-red' : 'text-neon-green'}`}>
                    {predResult.isolation_forest.is_anomaly ? 'ANOMALY DETECTED' : 'NORMAL'}
                  </div>
                </div>
              </div>
              <div className="p-3 bg-black/40 border border-white/5 rounded-lg">
                <div className="text-[10px] text-gray-500 font-mono mb-1">XGBOOST VERDICT</div>
                <div className="text-neon-blue font-[Orbitron] text-sm font-bold">{predResult.xgboost.malicious_prob}% MALICIOUS</div>
                <div className="text-[10px] text-gray-600 font-mono">Confidence: {predResult.xgboost.confidence}%</div>
              </div>
              <div className="p-3 bg-black/40 border border-white/5 rounded-lg">
                <div className="text-[10px] text-gray-500 font-mono mb-1">ENSEMBLE THREAT SCORE</div>
                <div className="h-2 bg-black/50 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-neon-green via-neon-amber to-neon-red transition-all duration-1000" style={{ width: `${predResult.ensemble_threat_score}%` }} />
                </div>
                <div className="text-right text-xs font-mono text-gray-400 mt-1">{predResult.ensemble_threat_score}/100</div>
              </div>
            </div>

            {/* Frustration Gauge */}
            <div className="flex flex-col items-center justify-center">
              <div className="text-[10px] text-gray-500 font-mono mb-2 tracking-widest">FRUSTRATION INDEX</div>
              <ResponsiveContainer width={200} height={200}>
                <RadialBarChart innerRadius="60%" outerRadius="90%" data={frustGauge} startAngle={180} endAngle={0}>
                  <RadialBar dataKey="value" cornerRadius={10} background={{ fill: '#ffffff08' }} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className={`text-3xl font-[Orbitron] font-black -mt-16 ${predResult.frustration_index > 70 ? 'text-neon-red' : predResult.frustration_index > 30 ? 'text-neon-amber' : 'text-neon-green'}`}>
                {predResult.frustration_index}
              </div>
              <div className="text-[10px] text-gray-600 font-mono mt-1">/100</div>
            </div>

            {/* Tarpit Strategy */}
            <div className="space-y-3">
              <div className="p-4 bg-black/40 border border-neon-red/20 rounded-lg">
                <div className="text-[10px] text-gray-500 font-mono mb-2">TARPIT STRATEGY</div>
                <div className="text-neon-red font-[Orbitron] text-sm font-bold mb-2">{predResult.tarpit_strategy}</div>
                <p className="text-xs text-gray-400 font-mono leading-relaxed">{predResult.tarpit_action}</p>
              </div>
              <div className="p-3 bg-black/40 border border-white/5 rounded-lg">
                <div className="text-[10px] text-gray-500 font-mono mb-1">AI LOGIC LAYER (GROQ)</div>
                <p className="text-[11px] text-neon-blue font-mono leading-relaxed italic">
                  "{predResult.ai_logic_layer}"
                </p>
              </div>
              <div className="p-3 bg-black/40 border border-white/5 rounded-lg">
                <div className="text-[10px] text-gray-500 font-mono mb-1">DEFENSE LOGIC (DETERMINISTIC)</div>
                <p className="text-[10px] text-gray-400 font-mono leading-relaxed">
                  {predResult.frustration_index < 30
                    ? '⬆ Frustration LOW → Increasing tarpit difficulty. Deploying complex fake systems.'
                    : predResult.frustration_index < 70
                    ? '⚖ Frustration MED → Maintaining engagement with periodic fake data leaks.'
                    : '⬇ Frustration HIGH → Leaking honeycreds to maximize intel before disconnect.'}
                </p>
              </div>
            </div>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
