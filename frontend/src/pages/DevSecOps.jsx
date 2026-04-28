import { useState } from 'react';
import {
    Bug, ShieldCheck, Shield, Zap, Code2, FileCode2,
    Copy, Terminal, Loader2, AlertTriangle, Activity,
    ChevronDown, ChevronUp, Check, User, Server, Skull,
    Target, Lock, Eye, Database
} from 'lucide-react';

// ── Phase config (dynamic — any phase name works) ─────────────────────────────
const PHASE_CFG = {
    Reconnaissance:       { ring: '#eab308', glow: '0 0 14px #eab30888', label: 'text-yellow-400' },
    Exploitation:         { ring: '#ef4444', glow: '0 0 14px #ef444488', label: 'text-red-400'    },
    'Privilege Escalation':{ ring: '#f97316', glow: '0 0 14px #f9731688', label: 'text-orange-400'},
    Exfiltration:         { ring: '#a855f7', glow: '0 0 14px #a855f788', label: 'text-purple-400'},
    Impact:               { ring: '#ec4899', glow: '0 0 14px #ec489988', label: 'text-pink-400'  },
};
const defaultPhase = { ring: '#6b7280', glow: '0 0 10px #6b728066', label: 'text-gray-400' };

const ACTOR_ICON = { ATTACKER: User, SYSTEM: Server, RESULT: Skull };
const ACTOR_COLOR = { ATTACKER: '#ef4444', SYSTEM: '#60a5fa', RESULT: '#ec4899' };

const STRATEGY_CFG = {
    PARAMETERIZE: { label: 'Parameterized Query', icon: Database, color: 'text-blue-400'   },
    SANITIZE:     { label: 'Input Sanitization',  icon: Shield,   color: 'text-green-400'  },
    VALIDATE:     { label: 'Input Validation',    icon: Check,    color: 'text-green-400'  },
    SANDBOX:      { label: 'Path Sandboxing',     icon: Lock,     color: 'text-purple-400' },
    AUTHENTICATE: { label: 'Auth Gate',           icon: Eye,      color: 'text-amber-400'  },
};

// ── Circular node with hover tooltip ─────────────────────────────────────────
function ChainNode({ step, index, total, hovered, onHover }) {
    const phase    = PHASE_CFG[step.phase] || defaultPhase;
    const ActorIcon = ACTOR_ICON[step.actor] || User;
    const actorColor = ACTOR_COLOR[step.actor] || '#9ca3af';
    const isHovered = hovered === index;

    // tooltip pops above on lower half of chain, below on upper half
    const tooltipSide = index >= total / 2 ? 'bottom-[calc(100%+12px)]' : 'top-[calc(100%+12px)]';

    return (
        <div className="relative flex flex-col items-center" style={{ flex: 1, minWidth: 0 }}>
            {/* Circle node */}
            <button
                onMouseEnter={() => onHover(index)}
                onMouseLeave={() => onHover(null)}
                onClick={() => onHover(isHovered ? null : index)}
                className="relative w-14 h-14 rounded-full border-2 flex items-center justify-center transition-transform duration-200 focus:outline-none"
                style={{
                    borderColor: phase.ring,
                    background: `${phase.ring}18`,
                    boxShadow: isHovered ? phase.glow : 'none',
                    transform: isHovered ? 'scale(1.15)' : 'scale(1)',
                }}
            >
                <ActorIcon className="w-5 h-5" style={{ color: actorColor }} />
                {/* Stage badge */}
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full text-[8px] font-black flex items-center justify-center"
                    style={{ background: phase.ring, color: '#000' }}>
                    {step.stage}
                </span>
            </button>

            {/* Phase label below node */}
            <span className={`mt-1.5 text-[8px] font-black uppercase tracking-wider text-center leading-tight ${phase.label}`}
                style={{ maxWidth: 68 }}>
                {step.phase}
            </span>

            {/* Hover tooltip */}
            {isHovered && (
                <div className={`absolute ${tooltipSide} left-1/2 -translate-x-1/2 z-50 w-64 rounded-xl border p-4 shadow-2xl animate-fade-in`}
                    style={{ borderColor: `${phase.ring}55`, background: '#0a0d16', boxShadow: phase.glow }}>
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[9px] font-black uppercase tracking-widest" style={{ color: phase.ring }}>
                            {step.phase} · Stage {step.stage}
                        </span>
                        <span className="text-[8px] font-bold uppercase" style={{ color: actorColor }}>
                            {step.actor}
                        </span>
                    </div>
                    {/* Action */}
                    <p className="text-xs font-bold text-white mb-1">{step.action}</p>
                    {/* Detail */}
                    <p className="text-[10px] text-gray-400 leading-relaxed mb-2">{step.detail}</p>
                    {/* Payload */}
                    {step.payload && (
                        <div className="bg-black/70 border border-white/[0.06] rounded-lg px-3 py-2 font-mono text-[10px] flex gap-2 items-start mb-2">
                            <Terminal className="w-3 h-3 text-gray-600 mt-0.5 flex-shrink-0" />
                            <code className="text-pink-400 break-all">{step.payload}</code>
                        </div>
                    )}
                    {/* Impact */}
                    {step.impact && (
                        <div className="flex items-start gap-1.5">
                            <Target className="w-3 h-3 text-gray-600 mt-0.5 flex-shrink-0" />
                            <span className="text-[10px] text-gray-500 italic">{step.impact}</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ── Animated connector line between nodes ─────────────────────────────────────
function Connector({ fromPhase }) {
    const phase = PHASE_CFG[fromPhase] || defaultPhase;
    return (
        <div className="flex-shrink-0 flex items-center" style={{ width: 28, marginTop: '-22px' }}>
            <div className="w-full h-px relative overflow-hidden" style={{ background: `${phase.ring}33` }}>
                <div className="absolute inset-0 animate-pulse" style={{ background: `linear-gradient(90deg, transparent, ${phase.ring}, transparent)`, animation: 'shimmer 1.8s infinite' }} />
            </div>
            <div style={{ width: 0, height: 0, borderTop: '4px solid transparent', borderBottom: '4px solid transparent', borderLeft: `6px solid ${phase.ring}` }} />
        </div>
    );
}

// ── Full attack chain visual ──────────────────────────────────────────────────
function AttackChainVisual({ chain, mitigation }) {
    const [hovered, setHovered] = useState(null);
    if (!chain || chain.length === 0) return null;

    const mitigationObj = typeof mitigation === 'object'
        ? mitigation
        : { summary: String(mitigation || ''), patched_snippet: '', strategy: 'VALIDATE' };
    const stratKey   = (mitigationObj.strategy || 'VALIDATE').split('|')[0].trim().toUpperCase();
    const strat      = STRATEGY_CFG[stratKey] || STRATEGY_CFG['VALIDATE'];
    const StratIcon  = strat.icon;

    return (
        <div className="mt-5 space-y-5 animate-fade-in">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="h-px flex-1" style={{ background: 'linear-gradient(90deg,transparent,#ef444444,transparent)' }} />
                <span className="text-[9px] font-black font-[Orbitron] text-red-400 tracking-[0.3em] uppercase">Attack Chain Simulation</span>
                <div className="h-px flex-1" style={{ background: 'linear-gradient(90deg,transparent,#ef444444,transparent)' }} />
            </div>

            {/* Circular nodes row */}
            <div className="relative flex items-start justify-between px-2 py-4" style={{ minHeight: 110 }}>
                {chain.map((step, idx) => (
                    <>
                        <ChainNode key={idx} step={step} index={idx} total={chain.length} hovered={hovered} onHover={setHovered} />
                        {idx < chain.length - 1 && <Connector key={`c${idx}`} fromPhase={step.phase} />}
                    </>
                ))}
            </div>
            <p className="text-center text-[9px] text-gray-600 font-mono uppercase tracking-widest -mt-2">Hover or tap a node to reveal attack details</p>

            {/* Mitigation */}
            <div className="rounded-xl border border-green-500/25 bg-green-500/5 p-4 space-y-2.5">
                <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-green-400" />
                    <span className="text-[10px] font-black font-[Orbitron] text-green-400 tracking-widest uppercase">Shield Response — Mitigation Applied</span>
                </div>
                <div className={`flex items-center gap-2 ${strat.color}`}>
                    <StratIcon className="w-3.5 h-3.5" />
                    <span className="text-[9px] font-bold uppercase tracking-widest">{strat.label}</span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">{mitigationObj.summary}</p>
                {mitigationObj.patched_snippet && (
                    <div className="bg-black/60 border border-green-500/20 rounded-lg px-4 py-2.5 font-mono text-[11px] flex items-start gap-3">
                        <Check className="w-3 h-3 text-green-400 mt-0.5 flex-shrink-0" />
                        <code className="text-green-400 break-all">{mitigationObj.patched_snippet}</code>
                    </div>
                )}
            </div>
        </div>
    );
}


// ─── Main Component ───────────────────────────────────────────────────────────
export default function DevSecOps() {
    const [code, setCode] = useState('');
    const [results, setResults] = useState(null);
    const [scanning, setScanning] = useState(false);
    const [showPatch, setShowPatch] = useState(false);
    const [expandedFinding, setExpandedFinding] = useState(null);
    const [copiedSource, setCopiedSource] = useState(false);
    const [copiedPatch, setCopiedPatch] = useState(false);
    const [appliedPatch, setAppliedPatch] = useState(false);

    const handleCopy = (text, type) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        if (type === 'source') { setCopiedSource(true); setTimeout(() => setCopiedSource(false), 2000); }
        else                   { setCopiedPatch(true);  setTimeout(() => setCopiedPatch(false),  2000); }
    };

    const handleScan = async () => {
        setScanning(true);
        setResults(null);
        setAppliedPatch(false);
        setExpandedFinding(null);
        try {
            const res  = await fetch('/api/scan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code }) });
            const data = await res.json();
            setResults(data);
        } catch (err) { console.error('Scan Error:', err); }
        setScanning(false);
    };

    const getSeverityStyle = (sev) => {
        switch (sev) {
            case 'CRITICAL': return 'text-red-500 border-red-500/30 bg-red-500/10';
            case 'HIGH':     return 'text-amber-500 border-amber-500/30 bg-amber-500/10';
            case 'MEDIUM':   return 'text-blue-400 border-blue-400/30 bg-blue-400/10';
            default:         return 'text-gray-400 border-gray-400/30 bg-gray-400/10';
        }
    };

    const getRiskColor = (score) => {
        if (score >= 80) return 'text-red-500';
        if (score >= 50) return 'text-amber-400';
        return 'text-neon-green';
    };

    return (
        <div className="max-w-[1600px] mx-auto px-6 py-10 animate-fade-in lg:px-12">
            {/* ── Header ──────────────────────────────── */}
            <div className="flex items-center justify-between mb-10">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-neon-blue/10 border border-neon-blue/20 rounded-xl">
                        <Code2 className="w-8 h-8 text-neon-blue" />
                    </div>
                    <div>
                        <h1 className="font-[Orbitron] text-3xl font-black text-white tracking-widest uppercase">Vulnerability Detector</h1>
                        <p className="text-xs text-gray-500 font-mono tracking-widest uppercase mt-1">Deterministic Vulnerability Analysis &amp; Remediation</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end mr-6">
                        <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest">Hardening Mode</span>
                        <span className="text-xs font-bold text-neon-green font-[Orbitron] tracking-widest flex items-center gap-2">ACTIVE <Activity className="w-3 h-3" /></span>
                    </div>
                    <button onClick={handleScan} disabled={scanning || !code.trim()} className="btn-neon btn-neon-blue flex items-center gap-3">
                        {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Zap className="w-4 h-4 fill-current" /> Initialize Scan</>}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-8 h-[calc(100vh-250px)] min-h-[700px]">
                {/* ── Panel 1: Source Editor ──────────── */}
                <div className="col-span-12 lg:col-span-6 flex flex-col h-full">
                    <div className="flex items-center justify-between mb-3 px-1">
                        <div className="flex items-center gap-2">
                            <FileCode2 className="w-4 h-4 text-gray-500" />
                            <span className="text-[11px] font-[Orbitron] text-gray-500 tracking-widest uppercase font-bold">Source Auditor</span>
                        </div>
                        <button onClick={() => handleCopy(code, 'source')} className="flex items-center gap-2 text-[10px] font-mono text-gray-600 hover:text-neon-blue transition-colors uppercase tracking-widest font-black">
                            {copiedSource ? <><Check className="w-3 h-3" /> Copied</> : <><Copy className="w-3 h-3" /> Copy Source</>}
                        </button>
                    </div>
                    <div className="glass-card flex-1 bg-[#0d111b]/80 border-white/5 relative overflow-hidden flex flex-col shadow-2xl">
                        <div className="flex-1 flex overflow-hidden">
                            <div className="w-14 bg-black/40 border-r border-white/5 flex flex-col pt-6 font-mono text-[11px] text-gray-700 items-center space-y-1 select-none">
                                {Array.from({ length: Math.max(40, code.split('\n').length + 5) }).map((_, i) => (
                                    <span key={i}>{i + 1}</span>
                                ))} 
                            </div>
                            <textarea
                                value={code}
                                onChange={e => setCode(e.target.value)}
                                className="flex-1 bg-transparent text-gray-300 text-[14px] p-6 font-mono outline-none resize-none leading-relaxed h-full custom-scrollbar"
                                placeholder="# Paste source code for forensic analysis..."
                                spellCheck={false}
                            />
                        </div>
                        <div className="px-6 py-2 border-t border-white/5 bg-black/40 flex justify-between text-[10px] text-gray-600 font-mono uppercase tracking-widest font-bold">
                            <span>{code.split('\n').length} Lines</span>
                            <span>{code.length} Characters</span>
                        </div>
                    </div>
                </div>

                {/* ── Panel 2: Results ────────────────── */}
                <div className="col-span-12 lg:col-span-6 flex flex-col h-full">
                    {!results && !scanning ? (
                        <div className="flex-1 flex flex-col items-center justify-center glass-card border-dashed border-white/10 opacity-50 text-center p-12">
                            <Shield className="w-20 h-20 mb-6 text-gray-700 animate-pulse" />
                            <p className="font-[Orbitron] text-xs text-gray-500 uppercase tracking-[0.4em]">Awaiting Analysis Stream</p>
                        </div>
                    ) : scanning ? (
                        <div className="flex-1 flex flex-col items-center justify-center glass-card border-white/5 bg-black/20 shadow-xl p-12">
                            <div className="w-20 h-20 mb-8 relative flex items-center justify-center">
                                <Shield className="w-full h-full text-neon-blue animate-pulse" />
                                <div className="absolute inset-0 border-2 border-transparent border-t-neon-blue rounded-full animate-spin" />
                            </div>
                            <p className="font-[Orbitron] text-neon-blue text-xs tracking-[0.4em] uppercase font-bold">Generating Autonomous Report</p>
                            <p className="text-[10px] text-gray-600 font-mono mt-4 animate-pulse uppercase">Traversing AST Sinks &amp; Taint Flows...</p>
                        </div>
                    ) : results.findings_count === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center glass-card border-green-500/20 bg-green-500/5 text-center p-12 space-y-4">
                            <div className="w-20 h-20 rounded-full border-2 border-green-400/40 bg-green-500/10 flex items-center justify-center shadow-[0_0_24px_#22c55e44]">
                                <ShieldCheck className="w-10 h-10 text-green-400" />
                            </div>
                            <p className="font-[Orbitron] text-green-400 text-sm font-black uppercase tracking-[0.3em]">Code Is Secure</p>
                            <p className="text-xs text-gray-500 font-mono max-w-xs leading-relaxed">The AI Cognitive Audit found no exploitable vulnerabilities in the provided source. No attack chain can be constructed.</p>
                            <div className="grid grid-cols-3 gap-4 w-full max-w-xs pt-2">
                                {['Risk Level','Findings','Hardened'].map((label, i) => (
                                    <div key={i} className="glass-card p-3 flex flex-col items-center border-white/5">
                                        <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest mb-1">{label}</span>
                                        <span className={`text-lg font-[Orbitron] font-black ${i===0?'text-green-400':i===1?'text-white':'text-green-400'}`}>
                                            {i===0 ? `${results.risk_score}%` : i===1 ? '0' : '✓'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-6">
                            {/* ── Summary Metrics ── */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="glass-card bg-[#0d111b]/90 p-5 flex flex-col items-center border-white/5 shadow-xl">
                                    <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-1 font-bold">Risk Level</span>
                                    <span className={`text-2xl font-[Orbitron] font-black ${getRiskColor(results.risk_score)}`}>{results.risk_score}%</span>
                                </div>
                                <div className="glass-card bg-[#0d111b]/90 p-5 flex flex-col items-center border-white/5 shadow-xl">
                                    <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-1 font-bold">Findings</span>
                                    <span className="text-2xl font-[Orbitron] font-black text-white">{results.findings_count}</span>
                                </div>
                                <div className="glass-card bg-[#0d111b]/90 p-5 flex flex-col items-center border-white/5 shadow-xl">
                                    <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-1 font-bold">Hardened</span>
                                    <span className="text-2xl font-[Orbitron] font-black text-neon-green">{results.fixed_count}</span>
                                </div>
                            </div>

                            {/* ── Incident Log ── */}
                            <div className="glass-card bg-[#0d111b]/60 border-white/5 shadow-2xl overflow-hidden">
                                <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className="w-4 h-4 text-neon-amber" />
                                        <span className="text-[11px] font-[Orbitron] text-gray-200 tracking-widest uppercase font-bold">Incident Log</span>
                                    </div>
                                    <span className="text-[9px] font-mono text-neon-blue uppercase tracking-widest">AI Cognitive Audit</span>
                                </div>

                                <div className="divide-y divide-white/5">
                                    {results.findings.map((vuln, i) => {
                                        const isOpen = expandedFinding === vuln.id;
                                        return (
                                            <div key={i} className="p-6 space-y-4 hover:bg-white/[0.02] transition-colors group">
                                                {/* Finding header */}
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-3">
                                                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${getSeverityStyle(vuln.severity)}`}>
                                                            {vuln.severity}
                                                        </span>
                                                        <h3 className="text-sm font-bold text-gray-200 font-[Orbitron] uppercase tracking-tight">
                                                            {vuln.id} — {vuln.type}
                                                        </h3>
                                                    </div>
                                                    <span className="text-[10px] font-mono text-gray-600 font-bold uppercase tracking-widest">Line {vuln.line}</span>
                                                </div>

                                                <p className="text-sm text-gray-400 leading-relaxed pl-4 border-l-2 border-white/5 font-medium">{vuln.description}</p>

                                                {/* Vulnerable snippet */}
                                                <div className="bg-[#060810] rounded-lg border border-white/5 px-5 py-3 font-mono text-xs overflow-x-auto shadow-inner relative group-hover:border-red-500/20 transition-colors">
                                                    <div className="absolute top-2 right-4 text-[8px] text-gray-700 uppercase font-black">Vulnerable Code</div>
                                                    <div className="flex gap-4">
                                                        <span className="text-gray-700 select-none">{vuln.line} |</span>
                                                        <code className="text-neon-pink font-bold">{vuln.snippet}</code>
                                                    </div>
                                                </div>

                                                {/* ── Attack Chain Visual (expanded) ── */}
                                                {isOpen && (
                                                    <AttackChainVisual chain={vuln.attack_chain} mitigation={vuln.mitigation} />
                                                )}

                                                {/* Toggle button */}
                                                <div className="flex items-center gap-4 pt-1">
                                                    <button
                                                        onClick={() => setExpandedFinding(isOpen ? null : vuln.id)}
                                                        className={`flex items-center gap-2 px-5 py-2 rounded-lg text-[10px] font-bold font-[Orbitron] transition-all tracking-widest shadow-lg border ${isOpen ? 'bg-red-500/20 border-red-500/40 text-red-400 hover:bg-red-500/30' : 'bg-neon-blue/10 border-neon-blue/30 text-neon-blue hover:bg-neon-blue hover:text-white'}`}
                                                    >
                                                        <Bug className="w-3.5 h-3.5" />
                                                        {isOpen ? 'Hide Attack Chain' : 'Show Attack Chain'}
                                                        {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                                    </button>
                                                    <div className="flex items-center gap-2 text-neon-green text-[9px] font-bold tracking-widest uppercase ml-auto">
                                                        <Check className="w-3.5 h-3.5 stroke-[3px]" /> Patch Strategy Locked
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* ── Autonomous Hardened Patch ── */}
                            <div className="glass-card bg-[#0d111b]/90 border-white/5 shadow-2xl overflow-hidden mb-8">
                                <div className="px-8 py-5 flex items-center justify-between border-b border-white/5 bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <ShieldCheck className="w-5 h-5 text-neon-green" />
                                        <span className="text-[11px] font-[Orbitron] text-gray-200 tracking-[0.3em] uppercase font-black">Autonomous Hardened Patch</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <button onClick={() => handleCopy(results.secure_code, 'patch')} className="flex items-center gap-2 text-[10px] font-mono text-gray-600 hover:text-neon-green transition-colors uppercase tracking-widest font-black">
                                            {copiedPatch ? <><Check className="w-3 h-3 text-neon-green" /> Copied</> : <><Copy className="w-3 h-3" /> Copy Patch</>}
                                        </button>
                                        <button onClick={() => setShowPatch(!showPatch)} className="flex items-center gap-2 text-[10px] font-mono text-gray-600 hover:text-white transition-colors uppercase tracking-widest font-black">
                                            {showPatch ? 'Compress' : 'Expand'}
                                            {showPatch ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>

                                {showPatch && (
                                    <div className="p-8 animate-slide-up bg-black/40">
                                        <div className="bg-[#05080f] rounded-xl border border-white/5 p-8 overflow-x-auto shadow-inner custom-scrollbar relative">
                                            <div className="absolute top-4 right-8 text-[9px] text-gray-800 font-mono tracking-widest uppercase font-black">remediated_source.py</div>
                                            <pre className="text-gray-400 text-xs font-mono leading-relaxed">{results.secure_code}</pre>
                                        </div>
                                        <div className="mt-6 flex items-center justify-between">
                                            <div className="flex items-center gap-3 text-[10px] text-gray-600 font-mono uppercase tracking-widest font-bold">
                                                <Activity className="w-3.5 h-3.5 text-neon-green" /> Verification: Hash Validated
                                            </div>
                                            <button
                                                onClick={() => { setAppliedPatch(true); setCode(results.secure_code); setShowPatch(false); }}
                                                className={`px-8 py-2.5 border rounded-lg text-[10px] font-bold font-[Orbitron] transition-all tracking-widest shadow-xl flex items-center gap-2 ${appliedPatch ? 'bg-neon-green text-white border-neon-green' : 'bg-neon-green/10 border-neon-green/30 text-neon-green hover:bg-neon-green hover:text-white'}`}
                                            >
                                                {appliedPatch ? <><Check className="w-4 h-4" /> Environment Secured</> : 'Apply to Environment'}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
