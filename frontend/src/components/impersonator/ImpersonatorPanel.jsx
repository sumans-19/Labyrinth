import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Activity, Cpu, Download } from 'lucide-react';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import { getBackendHttpBase } from '../../utils/runtime';


const ImpersonatorPanel = ({ sessionId, userId }) => {
    const [status, setStatus] = useState({ phase: 'LEARNING', progress: '0/15' });
    const [scoreData, setScoreData] = useState(null);
    const [profileData, setProfileData] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
    const [pdfData, setPdfData] = useState(null);
    const pdfRef = useRef(null);

    useEffect(() => {
        // Initial status check
        fetch(`${getBackendHttpBase()}/api/impersonator/status/${sessionId}/${userId}`)
            .then(res => res.json())
            .then(data => {
                setStatus(data);
                if (data.phase === 'MONITORING') {
                    fetch(`${getBackendHttpBase()}/api/impersonator/profile/${sessionId}/${userId}`)
                        .then(r => r.json())
                        .then(p => setProfileData(p))
                        .catch(() => {});
                }
            })
            .catch(e => console.error(e));

        // Listen for IRS updates dispatched globally
        const handleUpdate = (e) => {
            const data = e.detail;
            if (data.phase === 'LEARNING') {
                setStatus({ phase: 'LEARNING', progress: data.progress });
            } else {
                if (status.phase === 'LEARNING') {
                    // Just switched to monitoring, fetch profile
                    fetch(`${getBackendHttpBase()}/api/impersonator/profile/${sessionId}/${userId}`)
                        .then(r => r.json())
                        .then(p => setProfileData(p))
                        .catch(() => {});
                }
                setStatus({ phase: 'MONITORING', progress: '15/15' });
                setScoreData(data);
                
                // If the event included a command, add to timeline
                if (data.command) {
                    setTimeline(prev => [{
                        cmd: data.command,
                        time: new Date().toLocaleTimeString(),
                        severity: data.severity,
                        fileScore: data.file_score
                    }, ...prev].slice(0, 5));
                }
            }
        };

        window.addEventListener('irs-update', handleUpdate);
        return () => window.removeEventListener('irs-update', handleUpdate);
    }, [sessionId, userId]);

    // Handle PDF Generation
    const generatePdf = async () => {
        setIsGeneratingPdf(true);
        try {
            const res = await fetch(`${getBackendHttpBase()}/api/impersonator/report/${userId}`);
            const json = await res.json();
            if (json.status === 'success') {
                setPdfData(json.data);
                
                // Wait for the hidden div to render
                setTimeout(async () => {
                    if (pdfRef.current) {
                        const canvas = await html2canvas(pdfRef.current, {
                            scale: 2,
                            backgroundColor: '#0B0F19'
                        });
                        const imgData = canvas.toDataURL('image/png');
                        const pdf = new jsPDF({
                            orientation: 'portrait',
                            unit: 'px',
                            format: [canvas.width / 2, canvas.height / 2]
                        });
                        pdf.addImage(imgData, 'PNG', 0, 0, canvas.width / 2, canvas.height / 2);
                        pdf.save(`Labyrinth_Biometric_Profile_${userId}.pdf`);
                        setPdfData(null); // cleanup
                        setIsGeneratingPdf(false);
                    }
                }, 500);
            }
        } catch (e) {
            console.error(e);
            setIsGeneratingPdf(false);
        }
    };

    if (status.phase === 'LEARNING') {
        return (
            <div className="glass-card bg-black/50 p-6 border-neon-blue/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]">
                <div className="flex items-center space-x-3 mb-3">
                    <Cpu className="text-neon-blue animate-pulse w-6 h-6" />
                    <h3 className="text-white font-[Orbitron] font-black uppercase tracking-widest drop-shadow-[0_0_5px_rgba(59,130,246,0.5)]">The Impersonator</h3>
                </div>
                <p className="text-gray-400 text-xs font-mono mb-6 leading-relaxed">
                    Profiling behavioral biometrics. Please perform normal actions in the terminal to establish a baseline.
                </p>
                <div className="w-full bg-black/60 rounded-full h-3 border border-white/5 overflow-hidden">
                    <div 
                        className="bg-gradient-to-r from-neon-blue/50 to-neon-blue h-full rounded-full transition-all duration-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                        style={{ width: `${(parseInt(status.progress.split('/')[0]) / 15) * 100}%` }}
                    ></div>
                </div>
                <div className="text-right text-[10px] text-neon-blue font-mono mt-2 tracking-widest uppercase">{status.progress} Samples Collected</div>
            </div>
        );
    }

    const irs = scoreData?.irs || 0;
    
    let colorClass = "text-green-400";
    if (irs >= 40) colorClass = "text-yellow-400";
    if (irs >= 70) colorClass = "text-orange-400";
    if (irs >= 85) colorClass = "text-red-500";

    return (
        <div className={`glass-card bg-black/50 p-6 transition-all duration-500 ${irs >= 85 ? 'border-neon-red/50 shadow-[0_0_25px_rgba(239,68,68,0.4)] animate-pulse' : 'border-neon-blue/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]'}`}>
            <div className="flex justify-between items-start mb-6">
                <div>
                    <div className="flex items-center space-x-2 mb-1">
                        <Activity className={colorClass} />
                        <h3 className="text-white font-[Orbitron] font-black uppercase tracking-widest text-sm">Live Biometric Score</h3>
                    </div>
                    <span className={`text-3xl font-black font-[Orbitron] drop-shadow-[0_0_10px_currentColor] ${colorClass}`}>{irs}/100</span>
                </div>
                
                {/* PDF Download Button */}
                <button 
                    onClick={generatePdf}
                    disabled={isGeneratingPdf}
                    className="btn-neon btn-neon-blue text-[9px] py-1.5 px-3 flex items-center gap-1.5 whitespace-nowrap"
                >
                    <Download className="w-3 h-3" /> {isGeneratingPdf ? 'GENERATING...' : 'TRAINING PDF'}
                </button>
            </div>

            <div className="space-y-4">
                <div>
                    <div className="flex justify-between text-[10px] text-gray-400 mb-1.5 font-mono uppercase tracking-widest">
                        <span>Typing Rhythm (Isolation Forest)</span>
                        <span className="text-neon-purple">{scoreData?.if_score || 0}/100</span>
                    </div>
                    <div className="w-full bg-black/60 rounded-full h-1.5 border border-white/5">
                        <div className="bg-neon-purple h-1.5 rounded-full shadow-[0_0_10px_rgba(139,92,246,0.5)] transition-all duration-300" style={{ width: `${scoreData?.if_score || 0}%` }}></div>
                    </div>
                </div>
                
                <div>
                    <div className="flex justify-between text-[10px] text-gray-400 mb-1.5 font-mono uppercase tracking-widest">
                        <span>Sequence Match (MLP Regressor)</span>
                        <span className="text-neon-blue">{scoreData?.lstm_score || 0}/100</span>
                    </div>
                    <div className="w-full bg-black/60 rounded-full h-1.5 border border-white/5">
                        <div className="bg-neon-blue h-1.5 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-300" style={{ width: `${scoreData?.lstm_score || 0}%` }}></div>
                    </div>
                </div>

                <div>
                    <div className="flex justify-between text-[10px] text-gray-400 mb-1.5 font-mono uppercase tracking-widest">
                        <span>File Access Pattern</span>
                        <span className="text-neon-green">{scoreData?.file_score || 0}/100</span>
                    </div>
                    <div className="w-full bg-black/60 rounded-full h-1.5 border border-white/5">
                        <div className="bg-neon-green h-1.5 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)] transition-all duration-300" style={{ width: `${scoreData?.file_score || 0}%` }}></div>
                    </div>
                </div>
            </div>
            
            {scoreData?.severity === 'CRITICAL' && (
                <div className="mt-6 p-3 bg-neon-red/10 border border-neon-red/40 rounded-lg flex items-start space-x-3 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                    <ShieldAlert className="text-neon-red flex-shrink-0 mt-0.5" size={18}/>
                    <p className="text-xs text-red-200 font-mono leading-relaxed">
                        CRITICAL ANOMALY: The current session operator's behavior drastically deviates from the established owner profile.
                    </p>
                </div>
            )}

            {/* Typing Rhythm Waveform */}
            <div className="mt-8 pt-6 border-t border-white/10">
                <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4 font-[Orbitron]">Rhythm Waveform Comparison</h4>
                <div className="flex items-end space-x-1 h-12">
                    {/* Mocked visualization of dwell times. Blue = Baseline, Red = Live */}
                    {Array.from({ length: 15 }).map((_, i) => {
                        const baselineHeight = 20 + Math.random() * 40;
                        const liveHeight = scoreData?.if_score > 50 ? baselineHeight * (1 + Math.random()) : baselineHeight + (Math.random() * 5 - 2.5);
                        return (
                            <div key={i} className="flex-1 flex items-end justify-center space-x-[1px] h-full">
                                <div className="w-1/2 bg-neon-blue/50 rounded-t shadow-[0_0_5px_rgba(59,130,246,0.3)]" style={{ height: `${baselineHeight}%` }} title="Baseline Dwell"></div>
                                <div className={`w-1/2 rounded-t ${scoreData?.if_score > 50 ? 'bg-neon-red/80 shadow-[0_0_5px_rgba(239,68,68,0.5)]' : 'bg-neon-green/50 shadow-[0_0_5px_rgba(16,185,129,0.3)]'}`} style={{ height: `${Math.min(100, Math.max(0, liveHeight))}%` }} title="Live Dwell"></div>
                            </div>
                        );
                    })}
                </div>
                <div className="flex justify-between text-[9px] text-gray-500 mt-2 font-mono uppercase">
                    <div className="flex items-center space-x-1.5"><div className="w-2 h-2 bg-neon-blue/50 rounded shadow-[0_0_5px_rgba(59,130,246,0.5)]"></div><span>Baseline</span></div>
                    <div className="flex items-center space-x-1.5"><div className="w-2 h-2 bg-neon-red/80 rounded shadow-[0_0_5px_rgba(239,68,68,0.5)]"></div><span>Live Divergence</span></div>
                </div>
            </div>

            {/* File Sequence Tracker */}
            <div className="mt-8 pt-6 border-t border-white/10">
                <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-4 font-[Orbitron]">File Access Sequence Tracker</h4>
                <div className="space-y-2 h-32 overflow-hidden">
                    {timeline.length === 0 && <p className="text-xs text-slate-500 italic">Awaiting file access events...</p>}
                    {timeline.map((event, i) => (
                        <div key={i} className="flex items-center justify-between p-2 bg-black/30 border border-white/5 rounded text-xs font-mono">
                            <span className="text-slate-400">{event.time}</span>
                            <span className="text-white truncate mx-2 flex-1">{event.cmd}</span>
                            {event.fileScore === 100 ? (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-900/50 text-red-400 border border-red-500/30 uppercase">Decoy Trap</span>
                            ) : event.severity === 'NORMAL' ? (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-900/50 text-green-400 border border-green-500/30 uppercase">Normal</span>
                            ) : (
                                <span className="text-[9px] px-1.5 py-0.5 rounded bg-yellow-900/50 text-yellow-400 border border-yellow-500/30 uppercase">Anomalous</span>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Hidden PDF Template rendered off-screen */}
            {pdfData && (
                <div style={{ position: 'absolute', top: '-9999px', left: '-9999px', width: '800px', backgroundColor: '#0B0F19' }}>
                    <div ref={pdfRef} style={{ backgroundColor: '#0B0F19', color: '#FFFFFF', borderColor: '#8B5CF6', borderWidth: '4px', borderStyle: 'solid', minHeight: '1100px', width: '800px', padding: '48px', fontFamily: '"Orbitron", sans-serif', boxSizing: 'border-box' }}>
                        {/* Header */}
                        <div style={{ borderBottom: '2px solid #8B5CF6', paddingBottom: '24px', marginBottom: '32px' }}>
                            <h1 style={{ color: '#8B5CF6', fontSize: '36px', fontWeight: '900', letterSpacing: '0.1em', textTransform: 'uppercase', margin: '0 0 8px 0', textShadow: '0 0 15px rgba(139,92,246,0.8)' }}>Labyrinth Forge</h1>
                            <h2 style={{ color: '#D1D5DB', fontSize: '20px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.1em', margin: 0 }}>Behavioral Biometric Training Profile</h2>
                        </div>
                        
                        {/* Metadata */}
                        <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.4)', padding: '24px', borderRadius: '8px', marginBottom: '32px', fontFamily: 'monospace' }}>
                            <p style={{ color: '#3B82F6', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em', margin: '0 0 8px 0' }}><span style={{ color: '#9CA3AF' }}>Target Entity:</span> {userId}</p>
                            <p style={{ color: '#3B82F6', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em', margin: '0 0 8px 0' }}><span style={{ color: '#9CA3AF' }}>Samples Collected:</span> {pdfData.length}/15</p>
                            <p style={{ color: '#3B82F6', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '0.1em', margin: 0 }}><span style={{ color: '#9CA3AF' }}>Generated At:</span> {new Date().toUTCString()}</p>
                        </div>
                        
                        {/* Content */}
                        <div style={{ marginBottom: '24px' }}>
                            <h3 style={{ color: '#10B981', fontWeight: 'bold', fontSize: '18px', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '16px', borderLeft: '4px solid #10B981', paddingLeft: '12px', margin: '0 0 16px 0' }}>Baseline Command Sequence</h3>
                            <div style={{ backgroundColor: 'rgba(0, 0, 0, 0.6)', padding: '24px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)', fontFamily: 'monospace', fontSize: '14px' }}>
                                {pdfData.map((s, i) => (
                                    <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: i === pdfData.length - 1 ? 'none' : '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: i === pdfData.length - 1 ? 0 : '8px', marginBottom: i === pdfData.length - 1 ? 0 : '8px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                            <span style={{ color: '#6B7280' }}>[{String(i + 1).padStart(2, '0')}]</span>
                                            <span style={{ color: '#10B981', fontWeight: 'bold' }}>$ {s.command || 'UNKNOWN_CMD'}</span>
                                        </div>
                                        <span style={{ color: '#9CA3AF', fontSize: '12px', letterSpacing: '0.1em' }}>AVG DWELL: <span style={{ color: '#3B82F6', fontWeight: 'bold' }}>{s.avg_dwell.toFixed(1)}ms</span></span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        
                        {/* Footer */}
                        <div style={{ marginTop: '48px', paddingTop: '24px', borderTop: '1px solid rgba(139, 92, 246, 0.5)', textAlign: 'center' }}>
                            <p style={{ color: '#3B82F6', fontSize: '12px', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em', margin: 0 }}>End of Report // Labyrinth Forge Biometric Engine</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ImpersonatorPanel;
