import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import {
    Bug, ShieldAlert, ShieldCheck, Shield, Zap, Code2,
    Copy, Layout, Terminal, Loader2, AlertTriangle, Cpu,
    ChevronDown, ChevronUp, Activity, BarChart3, Fingerprint,
    X, Check, Settings, Upload, Play, Download, Trash2, FileCode2,
    Lock, AlertCircle
} from 'lucide-react';

export default function DevSecOps() {
    const [code, setCode] = useState('def vulnerable_function():\n    password = "hardcoded_secret"\n    cmd = input("Enter command: ")\n    import os\n    os.system(cmd)\n');
    const [language, setLanguage] = useState('python');
    const [activeTab, setActiveTab] = useState('output'); // 'output', 'vulnerabilities', 'exploit', 'fixed'
    
    const [execOutput, setExecOutput] = useState(null);
    const [isExecuting, setIsExecuting] = useState(false);
    
    const [scanResults, setScanResults] = useState(null);
    const [isScanning, setIsScanning] = useState(false);
    
    const [exploitSims, setExploitSims] = useState({});
    const [isSimulating, setIsSimulating] = useState(false);
    
    // Live Attack States
    const [liveAttackScript, setLiveAttackScript] = useState("");
    const [liveAttackOutput, setLiveAttackOutput] = useState(null);
    const [isAttacking, setIsAttacking] = useState(false);

    const [fixedCode, setFixedCode] = useState('');
    const [isFixing, setIsFixing] = useState(false);
    
    const [fixedExecOutput, setFixedExecOutput] = useState(null);
    const [copied, setCopied] = useState(false);
    
    const fileInputRef = useRef(null);

    const handleCopy = (text) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const autoDetectLanguage = (sourceCode) => {
        if (sourceCode.includes('#include <stdio.h>') || sourceCode.includes('#include <stdlib.h>')) {
            return 'c';
        } else if (sourceCode.includes('#include <iostream>')) {
            return 'cpp';
        } else if (sourceCode.includes('public class ') || sourceCode.includes('import java.')) {
            return 'java';
        } else if (sourceCode.includes('def ') && sourceCode.includes(':')) {
            return 'python';
        }
        return language; // default to whatever is selected
    };

    const handleRunCode = async (codeToRun = code, isFixed = false) => {
        let currentLang = language;
        if (!isFixed) {
            currentLang = autoDetectLanguage(codeToRun);
            if (currentLang !== language) setLanguage(currentLang);
            setActiveTab('output');
            setIsExecuting(true);
            setExecOutput(null);
        }
        
        try {
            const res = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: codeToRun, language: currentLang }),
            });
            const data = await res.json();
            if (isFixed) {
                setFixedExecOutput(data);
            } else {
                setExecOutput(data);
            }
        } catch (err) {
            const errData = { output: "Connection to Sandbox Failed.", status: "error", execution_time: "0.000s" };
            if (isFixed) setFixedExecOutput(errData);
            else setExecOutput(errData);
        }
        
        if (!isFixed) setIsExecuting(false);
    };

    const handleScan = async () => {
        const detectedLang = autoDetectLanguage(code);
        if (detectedLang !== language) setLanguage(detectedLang);
        
        setIsScanning(true);
        setActiveTab('vulnerabilities');
        setScanResults(null);
        try {
            const res = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language: detectedLang }),
            });
            const data = await res.json();
            setScanResults(data);
            if (data.secure_code) {
                setFixedCode(data.secure_code);
            }
        } catch (err) {
            console.error("Scan Error:", err);
        }
        setIsScanning(false);
    };

    const handleSimulateExploit = async (vuln) => {
        setIsSimulating(true);
        setActiveTab('exploit');
        try {
            const res = await fetch('/api/exploit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    vulnerability_id: vuln.id, 
                    vulnerability_type: vuln.type, 
                    code_snippet: vuln.snippet, 
                    line: vuln.line || 1 
                }),
            });
            const data = await res.json();
            setExploitSims(prev => ({ ...prev, [vuln.id]: data.simulation }));
        } catch (err) {
            setExploitSims(prev => ({ ...prev, [vuln.id]: "Exploit simulation failed to generate." }));
        }
        setIsSimulating(false);
    };

    const handleLiveAttack = async () => {
        if (!liveAttackScript.trim()) return;
        setIsAttacking(true);
        setLiveAttackOutput(null);
        try {
            const res = await fetch('/api/live_attack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vulnerable_code: code,
                    exploit_script: liveAttackScript
                }),
            });
            const data = await res.json();
            setLiveAttackOutput(data.output);
        } catch (err) {
            setLiveAttackOutput("[!] Connection Error. Attack failed to simulate.");
        }
        setIsAttacking(false);
    };

    const handleFixCode = async () => {
        setIsFixing(true);
        let currentFixedCode = fixedCode;
        
        if (!scanResults) {
            // Need to scan first if not done
            try {
                const res = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code, language }),
                });
                const data = await res.json();
                setScanResults(data);
                currentFixedCode = data.secure_code;
                setFixedCode(data.secure_code);
            } catch (err) {
                console.error("Scan Error:", err);
            }
        }
        
        setActiveTab('fixed');
        setIsFixing(false);
        
        // Automatically run the fixed code
        if (currentFixedCode) {
            setFixedExecOutput({ output: "Executing secure code in sandbox...", status: "running" });
            handleRunCode(currentFixedCode, true);
        }
    };

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            setCode(e.target.result);
            // auto-detect basic extensions
            if(file.name.endsWith('.py')) setLanguage('python');
            if(file.name.endsWith('.js')) setLanguage('javascript');
            if(file.name.endsWith('.c')) setLanguage('c');
            if(file.name.endsWith('.cpp')) setLanguage('cpp');
            if(file.name.endsWith('.java')) setLanguage('java');
        };
        reader.readAsText(file);
    };

    const downloadFixedCode = () => {
        if (!fixedCode) return;
        const blob = new Blob([fixedCode], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ext = language === 'python' ? 'py' : language === 'javascript' ? 'js' : language === 'java' ? 'java' : language === 'cpp' ? 'cpp' : 'c';
        a.download = `secure_code.${ext}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const getSeverityColor = (sev) => {
        switch (sev?.toUpperCase()) {
            case 'CRITICAL': return 'text-red-500 border-red-500 bg-red-500/10';
            case 'HIGH': return 'text-amber-500 border-amber-500 bg-amber-500/10';
            case 'MEDIUM': return 'text-yellow-400 border-yellow-400 bg-yellow-400/10';
            default: return 'text-blue-400 border-blue-400 bg-blue-400/10';
        }
    };

    const getIndicatorInfo = () => {
        if (scanResults) {
            if (scanResults.risk_score > 70) return { color: 'text-red-500', text: 'CRITICAL RISK', icon: AlertTriangle };
            if (scanResults.risk_score > 30) return { color: 'text-amber-500', text: 'WARNING', icon: AlertCircle };
            return { color: 'text-green-500', text: 'SAFE', icon: ShieldCheck };
        }
        return { color: 'text-gray-400', text: 'UNTESTED', icon: Shield };
    };
    const IndicatorInfo = getIndicatorInfo();
    const IndicatorIcon = IndicatorInfo.icon;

    return (
        <div className="max-w-[1600px] mx-auto px-6 py-6 animate-fade-in lg:px-8 h-[calc(100vh-64px)] flex flex-col">
            {/* Header Section */}
            <div className="flex items-center justify-between mb-6 shrink-0">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-neon-blue/10 border border-neon-blue/20 rounded-xl">
                        <Lock className="w-8 h-8 text-neon-blue" />
                    </div>
                    <div>
                        <h1 className="font-[Orbitron] text-2xl font-black text-white tracking-widest uppercase">
                            AI Secure Debugger & Analyzer
                        </h1>
                        <p className="text-xs text-gray-500 font-mono tracking-widest uppercase mt-1">
                            Sandboxed Execution • Vulnerability Scanning • Auto-Remediation
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-6">
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] font-mono text-gray-600 uppercase tracking-widest">Status Indicator</span>
                        <span className={`text-sm font-bold font-[Orbitron] tracking-widest flex items-center gap-2 ${IndicatorInfo.color}`}>
                            {IndicatorInfo.text} <IndicatorIcon className="w-4 h-4" />
                        </span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">
                {/* ── LEFT PANEL: CODE INPUT ── */}
                <div className="col-span-12 lg:col-span-6 flex flex-col h-full glass-card bg-[#0d111b]/80 border-white/5 relative overflow-hidden shadow-2xl">
                    <div className="px-4 py-3 border-b border-white/5 bg-black/40 flex justify-between items-center shrink-0">
                        <div className="flex items-center gap-3">
                            <FileCode2 className="w-4 h-4 text-neon-blue" />
                            <span className="text-[11px] font-[Orbitron] text-gray-300 tracking-widest uppercase font-bold">Source Sandbox</span>
                            <select 
                                value={language} 
                                onChange={(e) => setLanguage(e.target.value)}
                                className="bg-black/50 border border-white/10 text-xs text-gray-300 font-mono px-2 py-1 rounded outline-none cursor-pointer hover:border-neon-blue/50 transition-colors"
                            >
                                <option value="python">Python</option>
                                <option value="javascript">JavaScript</option>
                                <option value="java">Java</option>
                                <option value="c">C</option>
                                <option value="cpp">C++</option>
                            </select>
                        </div>
                        <div className="flex items-center gap-2">
                            <button onClick={() => setCode('')} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded hover:bg-white/5" title="Clear Code">
                                <Trash2 className="w-4 h-4" />
                            </button>
                            <input type="file" ref={fileInputRef} className="hidden" onChange={handleFileUpload} />
                            <button onClick={() => fileInputRef.current?.click()} className="p-1.5 text-gray-500 hover:text-neon-blue transition-colors rounded hover:bg-white/5" title="Upload File">
                                <Upload className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 min-h-0 relative">
                        <Editor
                            height="100%"
                            language={language}
                            theme="vs-dark"
                            value={code}
                            onChange={(value) => setCode(value)}
                            options={{
                                minimap: { enabled: false },
                                fontSize: 14,
                                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                padding: { top: 16 },
                                scrollBeyondLastLine: false,
                                smoothScrolling: true,
                            }}
                        />
                    </div>
                    
                    {/* Action Bar */}
                    <div className="p-4 border-t border-white/5 bg-black/60 shrink-0 grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <button 
                            onClick={() => handleRunCode(code, false)} 
                            disabled={isExecuting || !code.trim()}
                            className="flex items-center justify-center gap-2 py-2 px-3 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 rounded text-xs font-bold font-[Orbitron] tracking-wider transition-all disabled:opacity-50"
                        >
                            {isExecuting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />} RUN
                        </button>
                        <button 
                            onClick={handleScan}
                            disabled={isScanning || !code.trim()}
                            className="flex items-center justify-center gap-2 py-2 px-3 bg-neon-blue/10 hover:bg-neon-blue/20 border border-neon-blue/30 text-neon-blue rounded text-xs font-bold font-[Orbitron] tracking-wider transition-all shadow-[0_0_15px_rgba(59,130,246,0.1)] disabled:opacity-50"
                        >
                            {isScanning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldAlert className="w-3.5 h-3.5" />} SCAN
                        </button>
                        <button 
                            onClick={handleFixCode}
                            disabled={isFixing || !code.trim() || (!scanResults && isScanning)}
                            className="flex items-center justify-center gap-2 py-2 px-3 bg-neon-green/10 hover:bg-neon-green/20 border border-neon-green/30 text-neon-green rounded text-xs font-bold font-[Orbitron] tracking-wider transition-all shadow-[0_0_15px_rgba(34,197,94,0.1)] disabled:opacity-50"
                        >
                            {isFixing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 fill-current" />} FIX
                        </button>
                        <button 
                            onClick={() => handleCopy(code)}
                            className="flex items-center justify-center gap-2 py-2 px-3 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 rounded text-xs font-bold font-[Orbitron] tracking-wider transition-all"
                        >
                            {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />} COPY
                        </button>
                    </div>
                </div>

                {/* ── RIGHT PANEL: OUTPUT & ANALYSIS ── */}
                <div className="col-span-12 lg:col-span-6 flex flex-col h-full glass-card bg-[#0d111b]/80 border-white/5 shadow-2xl relative overflow-hidden">
                    {/* Tabs */}
                    <div className="flex items-center border-b border-white/5 bg-black/40 overflow-x-auto custom-scrollbar shrink-0">
                        {[
                            { id: 'output', label: 'Runtime Output', icon: Terminal },
                            { id: 'vulnerabilities', label: 'Vuln Report', icon: ShieldAlert },
                            { id: 'exploit', label: 'Exploit Sim', icon: Bug },
                            { id: 'fixed', label: 'Secure Code', icon: ShieldCheck }
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-3 text-[11px] font-[Orbitron] font-bold tracking-widest uppercase transition-colors whitespace-nowrap border-b-2
                                    ${activeTab === tab.id 
                                        ? 'border-neon-blue text-neon-blue bg-neon-blue/5' 
                                        : 'border-transparent text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
                            >
                                <tab.icon className="w-3.5 h-3.5" /> {tab.label}
                            </button>
                        ))}
                    </div>

                    <div className="flex-1 overflow-y-auto p-0 custom-scrollbar relative">
                        {/* 1. Runtime Output */}
                        {activeTab === 'output' && (
                            <div className="p-6 h-full flex flex-col">
                                {isExecuting ? (
                                    <div className="flex-1 flex flex-col items-center justify-center opacity-70">
                                        <div className="w-16 h-16 border-2 border-t-neon-blue border-r-transparent border-b-neon-blue border-l-transparent rounded-full animate-spin mb-4" />
                                        <p className="font-mono text-xs text-neon-blue uppercase tracking-widest">Executing in Sandbox...</p>
                                    </div>
                                ) : execOutput ? (
                                    <div className="flex-1 bg-[#05080f] rounded-lg border border-white/5 p-4 flex flex-col shadow-inner">
                                        <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-2">
                                            <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest flex items-center gap-2">
                                                <Terminal className="w-3 h-3" /> Console Output
                                            </span>
                                            <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded border ${execOutput.status === 'success' ? 'text-neon-green border-neon-green/30 bg-neon-green/10' : 'text-red-500 border-red-500/30 bg-red-500/10'}`}>
                                                Status: {execOutput.status} | {execOutput.execution_time}
                                            </span>
                                        </div>
                                        <pre className={`flex-1 font-mono text-sm overflow-auto whitespace-pre-wrap custom-scrollbar ${execOutput.status === 'success' ? 'text-gray-300' : 'text-red-400'}`}>
                                            {execOutput.output || "No output."}
                                        </pre>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex items-center justify-center text-gray-600 font-mono text-xs uppercase tracking-widest">
                                        Run code to see execution output
                                    </div>
                                )}
                            </div>
                        )}

                        {/* 2. Vulnerability Report */}
                        {activeTab === 'vulnerabilities' && (
                            <div className="p-6 h-full flex flex-col">
                                {isScanning ? (
                                    <div className="flex-1 flex flex-col items-center justify-center opacity-70">
                                        <Shield className="w-16 h-16 text-neon-amber animate-pulse mb-4" />
                                        <p className="font-mono text-xs text-neon-amber uppercase tracking-widest">Running Security Audit...</p>
                                    </div>
                                ) : scanResults ? (
                                    <div className="space-y-6">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-[#05080f] p-4 rounded border border-white/5 flex flex-col">
                                                <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-1">Risk Score</span>
                                                <span className={`text-3xl font-[Orbitron] font-black ${scanResults.risk_score > 70 ? 'text-red-500' : 'text-neon-amber'}`}>{scanResults.risk_score}%</span>
                                            </div>
                                            <div className="bg-[#05080f] p-4 rounded border border-white/5 flex flex-col">
                                                <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-1">Issues Found</span>
                                                <span className="text-3xl font-[Orbitron] font-black text-white">{scanResults.findings_count}</span>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            {scanResults.findings.map((vuln, i) => (
                                                <div key={i} className="bg-black/30 border border-white/5 rounded-lg p-5 group hover:border-white/10 transition-colors">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div className="flex items-center gap-3">
                                                            <span className={`px-2 py-0.5 rounded text-[9px] font-bold border uppercase tracking-wider ${getSeverityColor(vuln.severity)}`}>
                                                                {vuln.severity}
                                                            </span>
                                                            <h3 className="text-sm font-bold text-gray-200 font-[Orbitron] tracking-wide">{vuln.type}</h3>
                                                        </div>
                                                        <span className="text-[10px] font-mono text-gray-500">Line {vuln.line}</span>
                                                    </div>
                                                    <p className="text-xs text-gray-400 mb-4 font-mono leading-relaxed pl-3 border-l-2 border-white/10">
                                                        {vuln.description}
                                                    </p>
                                                    <button 
                                                        onClick={() => handleSimulateExploit(vuln)}
                                                        className="flex items-center gap-2 text-[10px] font-[Orbitron] uppercase tracking-widest text-neon-blue hover:text-white transition-colors bg-neon-blue/10 px-3 py-1.5 rounded border border-neon-blue/30"
                                                    >
                                                        <Bug className="w-3 h-3" /> Simulate Exploit
                                                    </button>
                                                </div>
                                            ))}
                                            {scanResults.findings.length === 0 && (
                                                <div className="p-8 text-center text-neon-green font-mono text-xs border border-neon-green/20 bg-neon-green/5 rounded-lg">
                                                    No vulnerabilities detected. Code appears secure.
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex items-center justify-center text-gray-600 font-mono text-xs uppercase tracking-widest">
                                        Scan code to view vulnerability report
                                    </div>
                                )}
                            </div>
                        )}

                        {/* 3. Safe Exploit Simulation */}
                        {activeTab === 'exploit' && (
                            <div className="p-6 h-full flex flex-col">
                                {isSimulating ? (
                                    <div className="flex-1 flex flex-col items-center justify-center opacity-70">
                                        <Bug className="w-16 h-16 text-red-500 animate-bounce mb-4" />
                                        <p className="font-mono text-xs text-red-500 uppercase tracking-widest">Generating POC Exploit...</p>
                                    </div>
                                ) : Object.keys(exploitSims).length > 0 ? (
                                    <div className="space-y-6">
                                        {Object.entries(exploitSims).map(([id, sim]) => {
                                            const parts = sim.split("[SIMULATION OUTPUT]");
                                            const exploitScript = parts[0]?.replace("[EXPLOIT SCRIPT]", "").trim() || "";
                                            const simulationOut = parts[1]?.trim() || sim;

                                            return (
                                                <div key={id} className="bg-[#0a0000] border border-red-500/30 rounded-lg p-5 shadow-[0_0_20px_rgba(239,68,68,0.1)]">
                                                    <div className="flex items-center gap-2 mb-3 text-red-500">
                                                        <AlertTriangle className="w-4 h-4" />
                                                        <span className="text-[11px] font-[Orbitron] font-bold uppercase tracking-widest">Target Vulnerability: {id}</span>
                                                    </div>
                                                    
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="flex flex-col">
                                                            <span className="text-[10px] text-red-400 font-mono mb-2 uppercase tracking-widest border-b border-red-500/20 pb-1">AI Generated Exploit Script</span>
                                                            <pre className="text-gray-300 font-mono text-[10px] whitespace-pre-wrap bg-black/80 p-3 rounded border border-white/5 h-full overflow-auto custom-scrollbar">
                                                                {exploitScript}
                                                            </pre>
                                                        </div>
                                                        <div className="flex flex-col">
                                                            <span className="text-[10px] text-red-400 font-mono mb-2 uppercase tracking-widest border-b border-red-500/20 pb-1">Simulated Breach Output</span>
                                                            <pre className="text-red-400 font-mono text-[10px] whitespace-pre-wrap bg-black/80 p-3 rounded border border-red-500/20 h-full overflow-auto custom-scrollbar shadow-inner">
                                                                {simulationOut}
                                                            </pre>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                        
                                        {/* LIVE ATTACK SANDBOX */}
                                        <div className="mt-8 pt-6 border-t border-red-500/20">
                                            <h3 className="text-red-500 font-[Orbitron] font-bold text-sm tracking-widest uppercase mb-4 flex items-center gap-2">
                                                <Terminal className="w-4 h-4" /> Custom Live Attack Terminal
                                            </h3>
                                            <p className="text-xs text-gray-400 font-mono mb-4">
                                                Paste a custom payload or script below and launch a simulated live attack against the sandboxed application.
                                            </p>
                                            
                                            <textarea 
                                                value={liveAttackScript}
                                                onChange={(e) => setLiveAttackScript(e.target.value)}
                                                placeholder="Enter raw python pwntools script, bash payload, or raw malicious input..."
                                                className="w-full h-32 bg-black/60 border border-red-500/30 rounded p-3 text-red-400 font-mono text-xs focus:outline-none focus:border-red-500 mb-3 custom-scrollbar"
                                            />
                                            
                                            <button 
                                                onClick={handleLiveAttack}
                                                disabled={isAttacking || !liveAttackScript.trim()}
                                                className="w-full py-4 bg-red-900/40 hover:bg-red-600/60 text-red-400 hover:text-white border-2 border-red-500/50 hover:border-red-500 rounded font-[Orbitron] font-black tracking-[0.2em] uppercase text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 group relative overflow-hidden shadow-[0_0_15px_rgba(220,38,38,0.3)] hover:shadow-[0_0_30px_rgba(220,38,38,0.6)]"
                                            >
                                                {isAttacking ? (
                                                    <span className="animate-pulse text-white">ATTACKING TARGET...</span>
                                                ) : (
                                                    <>
                                                        <Activity className="w-5 h-5 group-hover:animate-ping text-red-500 group-hover:text-white" /> LAUNCH DESTRUCTIVE EXPLOIT
                                                    </>
                                                )}
                                                <div className="absolute inset-0 bg-red-500/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                                                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent)] -translate-x-[100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                                            </button>

                                            {liveAttackOutput && (
                                                <div className="mt-8 relative animate-in fade-in zoom-in-95 slide-in-from-bottom-8 duration-700 ease-out">
                                                    {/* Glitch Overlay Effect */}
                                                    <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] pointer-events-none z-10 opacity-30"></div>
                                                    
                                                    <div className="bg-[#1a0000] border border-red-500/80 rounded-lg p-5 shadow-[0_0_50px_rgba(220,38,38,0.4)] relative overflow-hidden z-0">
                                                        <div className="flex justify-between items-center mb-3 pb-3 border-b border-red-600/50">
                                                            <span className="text-[12px] text-white font-mono uppercase tracking-widest flex items-center gap-2 font-bold">
                                                                <Bug className="w-4 h-4 text-red-500" /> SYSTEM BREACH DETECTED
                                                            </span>
                                                            <span className="text-[10px] text-red-400 font-[Orbitron] font-black uppercase bg-red-900/50 px-2 py-1 rounded animate-pulse shadow-[0_0_10px_rgba(220,38,38,0.8)]">CRITICAL COMPROMISE</span>
                                                        </div>
                                                        <pre className="text-red-500 font-mono text-sm whitespace-pre-wrap leading-relaxed">
                                                            {liveAttackOutput}
                                                        </pre>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex items-center justify-center text-gray-600 font-mono text-xs uppercase tracking-widest text-center px-8">
                                        Select a vulnerability from the Vuln Report and click 'Simulate Exploit'
                                    </div>
                                )}
                            </div>
                        )}

                        {/* 4. Secure Code & Final Output */}
                        {activeTab === 'fixed' && (
                            <div className="p-0 h-full flex flex-col">
                                {fixedCode ? (
                                    <div className="flex flex-col h-full">
                                        <div className="flex items-center justify-between p-3 border-b border-white/5 bg-[#05080f]">
                                            <span className="text-[11px] font-[Orbitron] text-neon-green tracking-widest uppercase font-bold flex items-center gap-2">
                                                <ShieldCheck className="w-4 h-4" /> Remediated Code
                                            </span>
                                            <button 
                                                onClick={downloadFixedCode}
                                                className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-gray-300 rounded text-[10px] font-mono tracking-widest uppercase transition-colors"
                                            >
                                                <Download className="w-3 h-3" /> Download
                                            </button>
                                        </div>
                                        <div className="flex-1 border-b border-white/5">
                                            <Editor
                                                height="100%"
                                                language={language}
                                                theme="vs-dark"
                                                value={fixedCode}
                                                options={{
                                                    readOnly: true,
                                                    minimap: { enabled: false },
                                                    fontSize: 13,
                                                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                                    scrollBeyondLastLine: false,
                                                }}
                                            />
                                        </div>
                                        {/* Final Execution Output portion */}
                                        <div className="h-48 bg-[#05080f] p-4 flex flex-col shrink-0">
                                            <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-2 flex items-center gap-2">
                                                <Activity className="w-3 h-3 text-neon-green" /> Post-Remediation Execution
                                            </span>
                                            <div className="flex-1 bg-black/50 border border-white/5 rounded p-3 overflow-auto custom-scrollbar">
                                                {fixedExecOutput ? (
                                                    <pre className={`font-mono text-xs whitespace-pre-wrap ${fixedExecOutput.status === 'success' ? 'text-gray-300' : 'text-red-400'}`}>
                                                        {fixedExecOutput.output || "No output."}
                                                    </pre>
                                                ) : (
                                                    <span className="text-gray-600 font-mono text-[10px] uppercase">Awaiting execution...</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex items-center justify-center text-gray-600 font-mono text-xs uppercase tracking-widest">
                                        Run FIX to generate secure code
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
