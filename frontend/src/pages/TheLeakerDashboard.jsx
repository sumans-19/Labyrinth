import { useState, useEffect, useRef } from 'react';
import { Download, Target, ChevronLeft, ShieldAlert, FileText, Server, HardDrive, Key, Copy, Check, Database, MapPin, ArrowRight, Globe, AlertTriangle } from 'lucide-react';

export default function TheLeakerDashboard({ onNavigate }) {
    const [internalThreats, setInternalThreats] = useState([]);
    const [decoys, setDecoys] = useState([]);
    const [copiedUrl, setCopiedUrl] = useState(null);
    const [movementHistory, setMovementHistory] = useState({});
    const [isGenerating, setIsGenerating] = useState(false);
    const [customFilename, setCustomFilename] = useState("Confidential_Alpha.html");
    const [customBaseUrl, setCustomBaseUrl] = useState("https://jene-plinthless-darius.ngrok-free.dev");
    const wsRef = useRef(null);

    // Fetch Decoys list from the backend
    useEffect(() => {
        const fetchDecoys = async () => {
            try {
                const response = await fetch(`http://${window.location.hostname}:8000/api/decoys`);
                const data = await response.json();
                setDecoys(data.files || []);
            } catch (error) {
                console.error("Failed to fetch decoys:", error);
            }
        };
        fetchDecoys();
    }, []);

    // Establish WebSocket Connection for Alert listener
    useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const host = window.location.hostname + ':8000';
        const ws = new WebSocket(`${protocol}://${host}/ws/monitor`);
        wsRef.current = ws;

        ws.onopen = () => console.log("Leaker Dashboard WS connected");

        ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === 'INTERNAL_THREAT_ALERT') {
                    setInternalThreats(prev => [msg, ...prev]);
                } else if (msg.type === 'FILE_MOVEMENT_DETECTED') {
                    setMovementHistory(prev => ({ ...prev, [msg.file_id]: msg }));
                }
            } catch (e) {
                console.error("Failed to parse WS message", e);
            }
        };

        ws.onclose = () => console.log("Leaker Dashboard WS closed");

        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, []);

    const copyToClipboard = (docName) => {
        const tripwireUrl = `http://${window.location.hostname}:8000/api/honeytoken/${encodeURIComponent(docName)}`;
        navigator.clipboard.writeText(tripwireUrl);
        setCopiedUrl(docName);
        setTimeout(() => setCopiedUrl(null), 2000);
    };

    const copyGhostPixel = (docName) => {
        const pixelUrl = `http://${window.location.hostname}:8000/api/v1/ghost-pixel/${encodeURIComponent(docName)}`;
        const imgTag = `<img src="${pixelUrl}" style="display:none;" />`;
        navigator.clipboard.writeText(imgTag);
        setCopiedUrl(docName + "_pixel");
        setTimeout(() => setCopiedUrl(null), 2000);
    };

    const handleDownload = (fileName) => {
        const downloadUrl = `http://${window.location.hostname}:8000/api/download/${encodeURIComponent(fileName)}`;
        window.open(downloadUrl, '_blank');
    };

    const handleGenerateAndDownload = async () => {
        setIsGenerating(true);
        try {
            const response = await fetch(`http://${window.location.hostname}:8000/api/v1/generate-decoy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: customFilename,
                    base_url: customBaseUrl
                })
            });
            const data = await response.json();
            if (data.download_url) {
                window.open(`http://${window.location.hostname}:8000${data.download_url}`, '_blank');
            }
        } catch (error) {
            console.error("Generation failed:", error);
        } finally {
            setIsGenerating(false);
        }
    };

    const getIcon = (type) => {
        switch (type) {
            case 'pdf': return <FileText className="w-5 h-5 text-neon-blue" />;
            case 'database': return <Database className="w-5 h-5 text-neon-purple" />;
            case 'config': return <Key className="w-5 h-5 text-neon-amber" />;
            default: return <Server className="w-5 h-5 text-gray-400" />;
        }
    };

    return (
        <div className="max-w-[1600px] mx-auto px-6 py-10 animate-fade-in lg:px-12 space-y-8">
            {/* Header & Navigation */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/10 pb-6">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => onNavigate('internalthreat')}
                        className="p-2 border border-white/10 hover:border-white/30 rounded bg-white/5 hover:bg-white/10 transition-colors mr-2"
                    >
                        <ChevronLeft className="w-5 h-5 text-gray-400" />
                    </button>
                    <div className="p-3 bg-neon-red/10 border border-neon-red/20 rounded-xl relative overflow-hidden group">
                        <div className="absolute inset-0 bg-neon-red/20 opacity-0 group-hover:opacity-100 animate-pulse transition-opacity" />
                        <Download className="w-8 h-8 text-neon-red relative z-10" />
                    </div>
                    <div>
                        <h1 className="font-[Orbitron] text-3xl font-black text-white tracking-widest uppercase text-glow-red">
                            The Leaker Dashboard
                        </h1>
                        <div className="flex items-center gap-2 mt-1">
                            <ShieldAlert className="w-3.5 h-3.5 text-neon-red" />
                            <p className="text-xs text-neon-red font-mono tracking-widest uppercase">
                                Active Honey-Token Monitoring
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Column: Live Alerts Queue */}
                <div className="lg:col-span-8 flex flex-col gap-6">
                    <h2 className="font-[Orbitron] text-lg font-bold text-white tracking-wider py-2 border-b border-white/5 flex items-center gap-3">
                        <span className="text-neon-red animate-pulse">●</span>
                        LIVE THREAT FEED & TRACE MAP
                    </h2>

                    {/* Exfiltration Trace Map */}
                    {Object.keys(movementHistory).length > 0 && (
                        <div className="space-y-4 animate-fade-in">
                            {Object.values(movementHistory).map((move, i) => (
                                <div key={i} className="glass-card border border-neon-red/30 bg-[#1a0808]/60 p-6 relative overflow-hidden">
                                    <div className="absolute top-0 right-0 p-2 opacity-20">
                                        <Globe className="w-20 h-20 text-neon-red animate-spin-slow" />
                                    </div>
                                    <div className="flex flex-col gap-6 relative z-10">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <AlertTriangle className="w-5 h-5 text-neon-red" />
                                                <span className="font-[Orbitron] text-xs font-bold text-white tracking-widest uppercase">
                                                    Exfiltration Trace: {move.file_id}
                                                </span>
                                            </div>
                                            <span className="text-[10px] font-mono text-neon-red animate-pulse">MOVE DETECTED</span>
                                        </div>

                                        <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16 py-4">
                                            <div className="flex flex-col items-center gap-2">
                                                <div className={`p-4 rounded-full ${move.is_authorized ? 'bg-neon-green/10 border-neon-green ring-4 ring-neon-green/20' : 'bg-white/5 border-white/10'}`}>
                                                    <MapPin className={`w-8 h-8 ${move.is_authorized ? 'text-neon-green' : 'text-neon-blue'}`} />
                                                </div>
                                                <div className="text-center">
                                                    <div className="text-[10px] text-gray-500 font-mono uppercase">Authorized Origin</div>
                                                    <div className={`text-sm font-bold font-mono ${move.is_authorized ? 'text-neon-green' : 'text-white'}`}>{move.origin_ip}</div>
                                                </div>
                                            </div>

                                            {!move.is_authorized && (
                                                <>
                                                    <div className="flex-1 max-w-[200px] h-[2px] bg-gradient-to-r from-neon-blue via-neon-red to-neon-red relative">
                                                        <div className="absolute top-1/2 left-0 right-0 h-1 bg-neon-red/50 blur-sm animate-pulse -translate-y-1/2" />
                                                        <div className="absolute top-1/2 -translate-y-1/2 left-0 w-4 h-4 rounded-full bg-neon-red animate-ping-fast shadow-[0_0_15px_#ef4444]" />
                                                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 flex items-center gap-1 text-[10px] font-mono text-neon-red font-bold animate-bounce uppercase">
                                                            <ArrowRight className="w-3 h-3" /> Exfiltrating
                                                        </div>
                                                    </div>

                                                    <div className="flex flex-col items-center gap-2">
                                                        <div className="p-4 rounded-full bg-neon-red/10 border border-neon-red shadow-[0_0_15px_#ef4444]">
                                                            <AlertTriangle className="w-8 h-8 text-neon-red animate-pulse" />
                                                        </div>
                                                        <div className="text-center">
                                                            <div className="text-[10px] text-neon-red font-mono uppercase font-bold">Unauthorized Probe</div>
                                                            <div className="text-sm font-bold text-neon-red font-mono text-glow-red">{move.current_ip}</div>
                                                        </div>
                                                    </div>
                                                </>
                                            )}

                                            {move.is_authorized && (
                                                <div className="flex flex-col items-center gap-2 opacity-50">
                                                    <div className="p-4 rounded-full bg-white/5 border border-white/10 border-dashed">
                                                        <ShieldAlert className="w-8 h-8 text-gray-500" />
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-[10px] text-gray-600 font-mono uppercase">No Movement Detected</div>
                                                        <div className="text-sm font-bold text-gray-600 font-mono italic">Origin Secured</div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="max-h-[800px] overflow-y-auto pr-2 custom-scrollbar space-y-6">
                        {internalThreats.length === 0 ? (
                            <div className="glass-card border border-white/5 bg-black/40 p-12 flex flex-col items-center justify-center text-center opacity-70">
                                <Target className="w-12 h-12 text-gray-600 mb-4 opacity-50" />
                                <h3 className="text-gray-400 font-mono tracking-widest text-sm mb-2 uppercase">No Breaches Detected</h3>
                                <p className="text-gray-500 text-xs max-w-sm">
                                    All honeypots and tracking pixel payloads are deployed and silent. Listening for unauthorized physical or remote network extraction...
                                </p>
                            </div>
                        ) : (
                            <>
                                {internalThreats.map((threat, idx) => {
                                    const isAuthorized = threat.is_authorized;
                                    const themeColor = isAuthorized ? 'neon-green' : 'neon-red';
                                    const secondaryColor = isAuthorized ? 'neon-blue' : 'neon-amber';
                                    const shadowColor = isAuthorized ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)';
                                    const accentShadow = isAuthorized ? '#22c55e' : '#ef4444';

                                    return (
                                        <div key={idx} className={`relative glass-card border border-${themeColor}/50 ${isAuthorized ? 'bg-[#05140b]/80' : 'bg-[#140505]/80'} overflow-hidden shadow-[0_0_25px_${shadowColor}] group animate-slide-up`}>
                                            <div className={`absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-${themeColor} to-${secondaryColor} shadow-[0_0_15px_${accentShadow}]`} />

                                            <div className="p-6 md:p-8 flex flex-col gap-6 relative z-10">
                                                <div className={`flex items-start justify-between border-b border-${themeColor}/20 pb-4`}>
                                                    <div className="flex items-center gap-3">
                                                        <div className={`p-2.5 bg-${themeColor}/10 rounded border border-${themeColor}/30 ${!isAuthorized ? 'animate-pulse' : ''}`}>
                                                            {isAuthorized ? <ShieldAlert className={`w-6 h-6 text-${themeColor}`} /> : <Target className={`w-6 h-6 text-${themeColor}`} />}
                                                        </div>
                                                        <div>
                                                            <h3 className={`font-[Orbitron] font-black text-xl text-white tracking-widest uppercase ${isAuthorized ? 'text-glow-green' : 'text-glow-red'}`}>
                                                                {isAuthorized ? 'AUTHORIZED ACCESS VERIFIED' : 'CRITICAL DATA EXFILTRATION'}
                                                            </h3>
                                                            <span className="text-xs font-mono text-gray-400">Time: {new Date(threat.timestamp).toLocaleString()}</span>
                                                        </div>
                                                    </div>
                                                    <div className={`px-3 py-1 bg-${themeColor}/20 border border-${themeColor} text-${themeColor} text-[10px] font-bold tracking-widest uppercase ${!isAuthorized ? 'animate-pulse' : ''}`}>
                                                        {isAuthorized ? 'SECURE ENVIRONMENT' : (threat.type === 'FILE_MOVEMENT_DETECTED' ? 'GEOGRAPHIC ANOMALY' : 'ISOLATION REQUIRED')}
                                                    </div>
                                                </div>

                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div className="bg-black/40 border border-white/5 rounded-lg p-4">
                                                        <div className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-1.5 font-bold">Leaked Asset</div>
                                                        <div className={`text-${secondaryColor} font-bold font-mono text-base break-all`}>{threat.document_name}</div>
                                                    </div>
                                                    <div className="bg-black/40 border border-white/5 rounded-lg p-4">
                                                        <div className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-1.5 font-bold">Threat Source</div>
                                                        <div className="text-white font-[Orbitron] font-black">{threat.ip_address}</div>
                                                        <div className="text-[10px] text-gray-400 mt-1 truncate" title={threat.user_agent}>{threat.user_agent}</div>
                                                    </div>
                                                </div>

                                                <div className={`bg-[#0a0f12]/90 rounded-xl p-4 md:p-5 border border-${isAuthorized ? 'neon-green/20' : 'neon-blue/20'}`}>
                                                    <div className="flex items-center gap-2 mb-3">
                                                        <div className={`w-2 h-2 rounded-full bg-${isAuthorized ? 'neon-green' : 'neon-blue'} ${!isAuthorized ? 'animate-ping' : ''}`} />
                                                        <span className={`font-[Orbitron] text-xs font-bold text-${isAuthorized ? 'neon-green' : 'neon-blue'} uppercase tracking-widest`}>Google Gemini Forensic Analysis</span>
                                                    </div>
                                                    <p className={`text-sm text-gray-300 leading-relaxed font-sans border-l-2 border-${isAuthorized ? 'neon-green/40' : 'neon-blue/40'} pl-4 py-1`}>
                                                        {threat.gemini_analysis}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </>
                        )}
                    </div>
                </div>

                {/* Right Column: Remote Tracking Generator & Pre-Deployed Decoys */}
                <div className="lg:col-span-4 space-y-8">
                    {/* Remote Tracking Generator */}
                    <div className="space-y-4">
                        <h2 className="font-[Orbitron] text-lg font-bold text-white tracking-wider flex justify-between items-center border-b border-neon-purple/30 pb-2">
                            <span className="text-neon-purple">Remote Tracking Gen</span>
                            <Globe className="w-5 h-5 text-neon-purple" />
                        </h2>

                        <div className="glass-card p-5 border border-neon-purple/20 bg-[#0f0514]/60 space-y-4">
                            <div className="space-y-1.5">
                                <label className="text-[10px] uppercase font-mono text-gray-400 font-bold tracking-widest">Decoy Filename</label>
                                <input
                                    type="text"
                                    value={customFilename}
                                    onChange={(e) => setCustomFilename(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-xs text-white font-mono focus:border-neon-purple/50 outline-none transition-colors"
                                    placeholder="e.g. Q4_Payroll.html"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[10px] uppercase font-mono text-gray-400 font-bold tracking-widest">Tracking Base URL (Local or Ngrok)</label>
                                <input
                                    type="text"
                                    value={customBaseUrl}
                                    onChange={(e) => setCustomBaseUrl(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-xs text-neon-blue font-mono focus:border-neon-blue/50 outline-none transition-colors"
                                    placeholder="http://..."
                                />
                            </div>

                            <button
                                onClick={handleGenerateAndDownload}
                                disabled={isGenerating}
                                className="w-full py-3 bg-neon-purple/10 hover:bg-neon-purple/20 border border-neon-purple/30 hover:border-neon-purple text-neon-purple text-[10px] font-black uppercase tracking-widest transition-all hover:shadow-[0_0_15px_rgba(168,85,247,0.3)] flex items-center justify-center gap-2 group"
                            >
                                {isGenerating ? (
                                    <>
                                        <div className="w-3 h-3 border-2 border-neon-purple/30 border-t-neon-purple rounded-full animate-spin" />
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <FileText className="w-3.5 h-3.5 group-hover:animate-bounce" />
                                        Generate & Download Instrumented File
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h2 className="font-[Orbitron] text-lg font-bold text-white tracking-wider flex justify-between items-center border-b border-white/5 pb-2">
                            <span className="text-neon-amber">Pre-Deployed Decoys</span>
                            <HardDrive className="w-5 h-5 text-gray-500" />
                        </h2>

                        <div className="glass-card p-6 border border-white/10 bg-black/60">
                            <p className="text-xs text-gray-400 mb-6 font-sans leading-relaxed">
                                These fake files contain tracking pixels or trap links. Use the copy button to get the tripwire link to embed in your PDFs or documents.
                            </p>

                            <div className="space-y-3">
                                {decoys.length > 0 ? decoys.map((file, idx) => (
                                    <div key={idx} className="group relative bg-[#111] border border-white/5 rounded p-3 flex items-center justify-between hover:border-white/20 transition-colors">
                                        <div className="flex items-center gap-3 overflow-hidden">
                                            <div className="p-2 bg-black/50 rounded border border-white/5 flex-shrink-0">
                                                {getIcon(file.type)}
                                            </div>
                                            <div className="min-w-0">
                                                <div className="text-sm font-semibold text-gray-200 truncate">{file.name}</div>
                                                <div className="text-[10px] font-mono text-gray-500 tracking-widest">{file.size} • {file.type.toUpperCase()}</div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleDownload(file.name)}
                                                className="p-2 bg-black/40 hover:bg-neon-green/20 border border-white/10 hover:border-neon-green/50 rounded flex-shrink-0 transition-colors"
                                                title="Download Decoy & Track Internal IP"
                                            >
                                                <Download className="w-4 h-4 text-gray-400 hover:text-neon-green transition-colors" />
                                            </button>
                                            <button
                                                onClick={() => copyGhostPixel(file.name)}
                                                className="p-2 bg-black/40 hover:bg-neon-purple/20 border border-white/10 hover:border-neon-purple/50 rounded flex-shrink-0 transition-colors"
                                                title="Copy Invisible Ghost Pixel Tag (HTML)"
                                            >
                                                {copiedUrl === file.name + "_pixel" ? (
                                                    <Check className="w-4 h-4 text-neon-green" />
                                                ) : (
                                                    <Globe className="w-4 h-4 text-gray-400 group-hover:text-neon-purple" />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => copyToClipboard(file.name)}
                                                className="p-2 bg-black/40 hover:bg-neon-blue/20 border border-white/10 hover:border-neon-blue/50 rounded flex-shrink-0 transition-colors tooltip-trigger"
                                                title="Copy HTTP Tripwire Link"
                                            >
                                                {copiedUrl === file.name ? (
                                                    <Check className="w-4 h-4 text-neon-green" />
                                                ) : (
                                                    <Copy className="w-4 h-4 text-gray-400 group-hover:text-neon-blue" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                )) : (
                                    <div className="text-center py-6 text-xs text-gray-500 font-mono">Loading decoys...</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
