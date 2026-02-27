import { useState, useEffect } from 'react';
import {
    Bug, ShieldAlert, ShieldCheck, Shield, Zap, Code2, FileCode2,
    Copy, Layout, Terminal, Loader2, AlertTriangle, Cpu,
    ChevronDown, ChevronUp, Activity, BarChart3, Fingerprint,
    X, Check, Settings
} from 'lucide-react';

export default function DevSecOps() {
    const [code, setCode] = useState('');
    const [results, setResults] = useState(null);
    const [scanning, setScanning] = useState(false);
    const [showPatch, setShowPatch] = useState(false);
    const [copiedSource, setCopiedSource] = useState(false);
    const [copiedPatch, setCopiedPatch] = useState(false);

    const handleCopy = (text, type) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        if (type === 'source') {
            setCopiedSource(true);
            setTimeout(() => setCopiedSource(false), 2000);
        } else {
            setCopiedPatch(true);
            setTimeout(() => setCopiedPatch(false), 2000);
        }
    };

    const handleScan = async () => {
        setScanning(true);
        setResults(null);
        try {
            const res = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code }),
            });
            const data = await res.json();
            setResults(data);
        } catch (err) {
            console.error("Scan Error:", err);
        }
        setScanning(false);
    };

    const getSeverityStyle = (sev) => {
        switch (sev) {
            case 'CRITICAL': return 'text-red-500 border-red-500/30 bg-red-500/10';
            case 'HIGH': return 'text-amber-500 border-amber-500/30 bg-amber-500/10';
            case 'MEDIUM': return 'text-blue-400 border-blue-400/30 bg-blue-400/10';
            default: return 'text-gray-400 border-gray-400/30 bg-gray-400/10';
        }
    };

    return (
        <div className="max-w-[1600px] mx-auto px-6 py-10 animate-fade-in lg:px-12">
            {/* Header Section */}
            <div className="flex items-center justify-between mb-10">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-neon-blue/10 border border-neon-blue/20 rounded-xl">
                        <Code2 className="w-8 h-8 text-neon-blue" />
                    </div>
                    <div>
                        <h1 className="font-[Orbitron] text-3xl font-black text-white tracking-widest uppercase">
                            Vulnerability Detector
                        </h1>
                        <p className="text-xs text-gray-500 font-mono tracking-widest uppercase mt-1">
                            Deterministic Vulnerability Analysis & Remediation
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end mr-6">
                        <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest">Hardening Mode</span>
                        <span className="text-xs font-bold text-neon-green font-[Orbitron] tracking-widest flex items-center gap-2">
                            ACTIVE <Activity className="w-3 h-3" />
                        </span>
                    </div>
                    <button
                        onClick={handleScan}
                        disabled={scanning || !code.trim()}
                        className="btn-neon btn-neon-blue flex items-center gap-3"
                    >
                        {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Zap className="w-4 h-4 fill-current" /> Initialize Scan</>}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-8 h-[calc(100vh-250px)] min-h-[700px]">
                {/* Panel 1: Source Input */}
                <div className="col-span-12 lg:col-span-6 flex flex-col h-full">
                    <div className="flex items-center justify-between mb-3 px-1">
                        <div className="flex items-center gap-2">
                            <FileCode2 className="w-4 h-4 text-gray-500" />
                            <span className="text-[11px] font-[Orbitron] text-gray-500 tracking-widest uppercase font-bold">Source Auditor</span>
                        </div>
                        <button
                            onClick={() => handleCopy(code, 'source')}
                            className="flex items-center gap-2 text-[10px] font-mono text-gray-600 hover:text-neon-blue transition-colors uppercase tracking-widest font-black"
                        >
                            {copiedSource ? <><Check className="w-3 h-3" /> Copied</> : <><Copy className="w-3 h-3" /> Copy Source</>}
                        </button>
                    </div>
                    <div className="glass-card flex-1 bg-[#0d111b]/80 border-white/5 relative overflow-hidden flex flex-col shadow-2xl">
                        <div className="flex-1 flex overflow-hidden">
                            {/* Line Numbers column */}
                            <div className="w-14 bg-black/40 border-r border-white/5 flex flex-col pt-6 font-mono text-[11px] text-gray-700 items-center space-y-1 select-none">
                                {Array.from({ length: 40 }).map((_, i) => (
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

                {/* Panel 2: Results Display */}
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
                            <p className="text-[10px] text-gray-600 font-mono mt-4 animate-pulse uppercase">Traversing AST Sinks & Taint Flows...</p>
                        </div>
                    ) : (
                        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-6">
                            {/* Summary Metrics */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="glass-card bg-[#0d111b]/90 p-5 flex flex-col items-center border-white/5 shadow-xl">
                                    <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-1 font-bold">Risk Level</span>
                                    <span className={`text-2xl font-[Orbitron] font-black ${results.risk_score > 70 ? 'text-neon-pink' : 'text-neon-amber'}`}>
                                        {results.risk_score}%
                                    </span>
                                </div>
                                <div className="glass-card bg-[#0d111b]/90 p-5 flex flex-col items-center border-white/5 shadow-xl">
                                    <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-1 font-bold">Findings</span>
                                    <span className="text-2xl font-[Orbitron] font-black text-white">
                                        {results.findings_count}
                                    </span>
                                </div>
                                <div className="glass-card bg-[#0d111b]/90 p-5 flex flex-col items-center border-white/5 shadow-xl">
                                    <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest mb-1 font-bold">Hardened</span>
                                    <span className="text-2xl font-[Orbitron] font-black text-neon-green">
                                        {results.fixed_count}
                                    </span>
                                </div>
                            </div>

                            {/* Vulnerability Report Container */}
                            <div className="glass-card bg-[#0d111b]/60 border-white/5 shadow-2xl overflow-hidden">
                                <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className="w-4 h-4 text-neon-amber" />
                                        <span className="text-[11px] font-[Orbitron] text-gray-200 tracking-widest uppercase font-bold">Incident Log</span>
                                    </div>
                                    <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest text-neon-blue">AI Cognitive Audit</span>
                                </div>

                                <div className="divide-y divide-white/5">
                                    {results.findings.map((vuln, i) => (
                                        <div key={i} className="p-8 space-y-5 hover:bg-white/[0.02] transition-colors group">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-4">
                                                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${getSeverityStyle(vuln.severity)}`}>
                                                        {vuln.severity}
                                                    </span>
                                                    <h3 className="text-sm font-bold text-gray-200 tracking-tight font-[Orbitron] uppercase">
                                                        {vuln.id} — {vuln.type}
                                                    </h3>
                                                </div>
                                                <span className="text-[10px] font-mono text-gray-600 font-bold uppercase tracking-widest">Line {vuln.line}</span>
                                            </div>

                                            <p className="text-sm text-gray-400 leading-relaxed pl-4 border-l-2 border-white/5 font-medium">
                                                {vuln.description}
                                            </p>

                                            <div className="bg-[#060810] rounded-lg border border-white/5 p-5 font-mono text-xs overflow-x-auto shadow-inner relative group-hover:border-neon-blue/20 transition-colors">
                                                <div className="absolute top-2 right-4 text-[8px] text-gray-700 uppercase font-black">Vulnerable Code</div>
                                                <div className="flex gap-4">
                                                    <span className="text-gray-700 select-none">{vuln.line} |</span>
                                                    <code className="text-neon-pink font-bold">{vuln.snippet}</code>
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-4 pt-2">
                                                <button className="flex items-center gap-2 px-6 py-2 bg-neon-blue/10 border border-neon-blue/30 text-neon-blue rounded-lg text-[10px] font-bold font-[Orbitron] hover:bg-neon-blue hover:text-white transition-all tracking-widest shadow-lg">
                                                    <Zap className="w-3.5 h-3.5 fill-current" /> Simulate Exploit
                                                </button>
                                                <div className="flex items-center gap-2 text-neon-green text-[9px] font-bold tracking-widest uppercase ml-auto">
                                                    <Check className="w-3.5 h-3.5 stroke-[3px]" /> Patch Strategy Locked
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Secure Patch Section */}
                            <div className="glass-card bg-[#0d111b]/90 border-white/5 shadow-2xl overflow-hidden mb-8">
                                <div className="px-8 py-5 flex items-center justify-between border-b border-white/5 bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <ShieldCheck className="w-5 h-5 text-neon-green" />
                                        <span className="text-[11px] font-[Orbitron] text-gray-200 tracking-[0.3em] uppercase font-black">Autonomous Hardened Patch</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <button
                                            onClick={() => handleCopy(results.secure_code, 'patch')}
                                            className="flex items-center gap-2 text-[10px] font-mono text-gray-600 hover:text-neon-green transition-colors uppercase tracking-widest font-black"
                                        >
                                            {copiedPatch ? <><Check className="w-3 h-3 text-neon-green" /> Copied</> : <><Copy className="w-3 h-3" /> Copy Patch</>}
                                        </button>
                                        <button
                                            onClick={() => setShowPatch(!showPatch)}
                                            className="flex items-center gap-2 text-[10px] font-mono text-gray-600 hover:text-white transition-colors uppercase tracking-widest font-black"
                                        >
                                            {showPatch ? 'Compress' : 'Expand'}
                                            {showPatch ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                        </button>
                                    </div>
                                </div>

                                {showPatch && (
                                    <div className="p-8 animate-slide-up bg-black/40">
                                        <div className="bg-[#05080f] rounded-xl border border-white/5 p-8 overflow-x-auto shadow-inner custom-scrollbar relative">
                                            <div className="absolute top-4 right-8 text-[9px] text-gray-800 font-mono tracking-widest uppercase font-black">remediated_source.py</div>
                                            <pre className="text-gray-400 text-xs font-mono leading-relaxed">
                                                {results.secure_code}
                                            </pre>
                                        </div>
                                        <div className="mt-6 flex items-center justify-between">
                                            <div className="flex items-center gap-3 text-[10px] text-gray-600 font-mono uppercase tracking-widest font-bold">
                                                <Activity className="w-3.5 h-3.5 text-neon-green" /> Verification: Hash Validated
                                            </div>
                                            <button className="px-8 py-2.5 bg-neon-green/10 border border-neon-green/30 text-neon-green rounded-lg text-[10px] font-bold font-[Orbitron] hover:bg-neon-green hover:text-white transition-all tracking-widest shadow-xl">
                                                Apply to Environment
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
