import { FileText, Download, Clock, Shield, Crosshair, AlertTriangle, CheckCircle2, Activity, BarChart3, Fingerprint, Database } from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer, YAxis, Tooltip } from 'recharts';
import { getBackendHttpBase } from '../utils/runtime';


function formatTimestamp(ts) {
    if (!ts) return '--';
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString();
}

export default function IncidentReport({ report }) {
    if (!report) return null;

    const {
        report_id,
        session_duration,
        attacker_ip,
        threat_assessment,
        mitre_attack,
        session_stats,
        timeline,
        recommendations,
    } = report;

    const riskColor = threat_assessment.overall_risk > 70 ? '#ef4444'
        : threat_assessment.overall_risk > 40 ? '#f59e0b' : '#10b981';

    const classificationColors = {
        APT: '#dc2626',
        Advanced: '#f59e0b',
        Opportunistic: '#10b981',
    };

    const downloadReport = async () => {
        try {
            console.log('Generating PDF from report data statelessly...');
            const response = await fetch(`${getBackendHttpBase()}/api/report/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(report),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Server failed to generate PDF');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Labyrinth_Incident_${report_id}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading PDF report:', error);
            alert('Failed to download PDF report. Using backup text fallback.');

            // Fallback to text download if PDF fails
            const textContent = `LABYRINTH FORGE — INCIDENT REPORT\nID: ${report_id}\n... (Rest of text content)`;
            const blob = new Blob([textContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${report_id}_report.txt`;
            a.click();
            URL.revokeObjectURL(url);
        }
    };

    return (
        <div className="glass-card overflow-hidden border-neon-amber/30 shadow-[0_0_30px_rgba(245,158,11,0.15)] animate-slide-up">
            <div className="px-4 py-3 border-b border-white/5 bg-black/30 flex items-center gap-2">
                <FileText className="w-4 h-4 text-neon-amber" />
                <span className="font-[Orbitron] text-xs font-semibold text-neon-amber tracking-wider">
                    INCIDENT REPORT
                </span>
                <span className="ml-auto font-mono text-[10px] text-gray-500">{report_id}</span>
            </div>

            <div className="p-4 space-y-4">
                {/* Risk Classification Header */}
                <div className="flex items-center gap-4 p-3 rounded-xl border"
                    style={{
                        background: `linear-gradient(135deg, ${riskColor}10, transparent)`,
                        borderColor: `${riskColor}30`,
                    }}>
                    <div className="text-center">
                        <div className="font-[Orbitron] text-3xl font-black" style={{ color: riskColor }}>
                            {threat_assessment.overall_risk}
                        </div>
                        <div className="text-[9px] font-mono text-gray-500 mt-0.5">RISK SCORE</div>
                    </div>
                    <div className="h-12 w-px bg-white/10" />
                    <div className="flex-1 grid grid-cols-3 gap-3 text-xs">
                        <div>
                            <div className="text-gray-500 text-[10px]">Classification</div>
                            <div className="font-bold" style={{ color: classificationColors[threat_assessment.classification] || '#f59e0b' }}>
                                {threat_assessment.classification}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-500 text-[10px]">Skill</div>
                            <div className="text-white font-semibold">{threat_assessment.skill_level}</div>
                        </div>
                        <div>
                            <div className="text-gray-500 text-[10px]">Duration</div>
                            <div className="text-white font-semibold">{session_duration}s</div>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-4 gap-2">
                    {[
                        { icon: Activity, label: 'Commands', value: session_stats.total_commands, color: '#3b82f6' },
                        { icon: AlertTriangle, label: 'Suspicious', value: session_stats.suspicious_commands, color: '#f59e0b' },
                        { icon: Crosshair, label: 'TTPs', value: mitre_attack.techniques_observed, color: '#ef4444' },
                        { icon: Shield, label: 'Tokens Hit', value: session_stats.honey_tokens_accessed, color: '#ec4899' },
                    ].map(({ icon: Icon, label, value, color }, i) => (
                        <div key={i} className="p-2 rounded-lg bg-white/[0.03] text-center">
                            <Icon className="w-4 h-4 mx-auto mb-1" style={{ color }} />
                            <div className="text-white font-bold text-sm">{value}</div>
                            <div className="text-[9px] text-gray-500 font-mono">{label}</div>
                        </div>
                    ))}
                </div>

                {/* MITRE Techniques */}
                {mitre_attack.techniques?.length > 0 && (
                    <div>
                        <div className="text-[10px] font-[Orbitron] font-bold text-neon-red tracking-wider mb-2">
                            MITRE ATT&CK TECHNIQUES
                        </div>
                        <div className="space-y-1 max-h-[120px] overflow-y-auto">
                            {mitre_attack.techniques.map((t, i) => (
                                <div key={i} className="flex items-center gap-2 text-[11px] font-mono p-1.5 rounded bg-white/[0.03]">
                                    <span className="text-neon-red font-bold shrink-0">{t.technique_id}</span>
                                    <span className="text-gray-400 flex-1 truncate">{t.technique_name}</span>
                                    <span className="text-gray-600 text-[9px]">{t.phase}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Mini Visualization */}
                <div className="h-[80px] w-full bg-black/40 rounded-lg border border-white/5 p-1 relative overflow-hidden">
                    <div className="absolute top-1 left-2 z-10 flex items-center gap-1 opacity-50">
                        <BarChart3 className="w-2.5 h-2.5 text-neon-cyan" />
                        <span className="text-[8px] font-mono text-neon-cyan uppercase">Threat Waveform</span>
                    </div>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={timeline.slice(-10).map((t, i) => ({ val: t.risk_score, i }))}>
                            <Area
                                type="monotone"
                                dataKey="val"
                                stroke="#00FFFF"
                                fill="url(#colorVal)"
                                strokeWidth={1}
                                isAnimationActive={false}
                            />
                            <defs>
                                <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#00FFFF" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#00FFFF" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Recommendations */}
                <div>
                    <div className="text-[10px] font-[Orbitron] font-bold text-neon-cyan tracking-wider mb-2">
                        RECOMMENDATIONS
                    </div>
                    <div className="space-y-1">
                        {recommendations?.map((r, i) => (
                            <div key={i} className="flex items-start gap-2 text-[11px] p-1.5 rounded bg-white/[0.03]">
                                <CheckCircle2 className="w-3 h-3 text-neon-cyan shrink-0 mt-0.5" />
                                <span className="text-gray-300">{r}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Behavioral Fingerprinting Data */}
                {report.fingerprint && (
                    <div className={`p-4 rounded-xl border ${report.fingerprint.is_returning ? 'border-neon-blue/30 bg-neon-blue/5' : 'border-neon-purple/30 bg-neon-purple/5'} relative overflow-hidden group`}>
                        {/* Background Decoration */}
                        <div className={`absolute top-0 right-0 w-32 h-32 -mr-16 -mt-16 rounded-full blur-[60px] opacity-20 ${report.fingerprint.is_returning ? 'bg-neon-blue' : 'bg-neon-purple'}`} />
                        
                        <div className="flex items-center justify-between mb-4 relative z-10">
                            <div className="flex items-center gap-2">
                                <Fingerprint className={`w-4 h-4 ${report.fingerprint.is_returning ? 'text-neon-blue' : 'text-neon-purple'}`} />
                                <span className={`font-[Orbitron] text-[10px] font-bold uppercase tracking-widest ${report.fingerprint.is_returning ? 'text-neon-blue' : 'text-neon-purple'}`}>
                                    Behavioral Forensic Intelligence
                                </span>
                            </div>
                            <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${report.fingerprint.is_returning ? 'text-neon-blue border-neon-blue/30 bg-neon-blue/10' : 'text-neon-purple border-neon-purple/30 bg-neon-purple/10'} uppercase font-bold`}>
                                {report.fingerprint.is_returning ? "Returning Attacker" : "Novel Attack Pattern"}
                            </span>
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6 relative z-10">
                            <div className="space-y-1">
                                <div className="text-[9px] text-gray-500 font-mono uppercase tracking-tighter">Profile Attribution</div>
                                <div className="text-sm font-bold text-white font-[Orbitron] tracking-wider truncate">
                                    {report.fingerprint.matched_profile}
                                </div>
                                <div className={`text-[10px] font-bold ${report.fingerprint.is_returning ? 'text-neon-blue' : 'text-neon-purple'}`}>
                                    Confidence: {report.fingerprint.match_confidence}%
                                </div>
                            </div>
                            <div className="space-y-1">
                                <div className="text-[9px] text-gray-500 font-mono uppercase tracking-tighter">Predicted Objective</div>
                                <div className="text-sm font-bold text-neon-amber font-mono truncate leading-none">
                                    {report.fingerprint.detected_objective}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 py-4 border-y border-white/5 relative z-10">
                            <div className="text-center p-2 rounded bg-white/[0.02] sm:bg-transparent">
                                <div className="text-xs font-bold text-white mb-0.5">{report.fingerprint.avg_time_delay_ms} ms</div>
                                <div className="text-[8px] text-gray-500 uppercase font-mono">Avg Delay</div>
                            </div>
                            <div className="text-center p-2 rounded bg-white/[0.02] sm:bg-transparent">
                                <div className="text-xs font-bold text-neon-red mb-0.5">{report.fingerprint.error_rate_percentage}%</div>
                                <div className="text-[8px] text-gray-500 uppercase font-mono">Typo Rate</div>
                            </div>
                            <div className="text-center p-2 rounded bg-white/[0.02] sm:bg-transparent">
                                <div className="text-xs font-bold text-neon-green mb-0.5">{report.fingerprint.total_commands}</div>
                                <div className="text-[8px] text-gray-500 uppercase font-mono">Sequence Len</div>
                            </div>
                        </div>

                        <div className="relative mt-4 group">
                            <button
                                onClick={async (e) => {
                                    const btn = e.currentTarget;
                                    btn.disabled = true;
                                    const originalText = btn.innerHTML;
                                    btn.innerHTML = '<span class="animate-pulse">SYNCHRONIZING WITH DB...</span>';
                                    
                                    try {
                                        const resp = await fetch(`${getBackendHttpBase()}/api/v1/fingerprint/save`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                                fingerprint: report.fingerprint,
                                                attacker_ip: report.attacker_ip
                                            })
                                        });
                                        const data = await resp.json();
                                        if (data.status === 'success') {
                                            btn.innerHTML = '<span class="text-neon-green flex items-center gap-2"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-circle-2"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg> PROFILE PERSISTED SUCCESSFULLY</span>';
                                            setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 3000);
                                        } else {
                                            throw new Error("Save failed");
                                        }
                                    } catch (e) { 
                                        btn.innerHTML = '<span class="text-neon-red">SYNC FAILED</span>';
                                        setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 3000);
                                    }
                                }}
                                className={`w-full py-3 ${report.fingerprint.is_returning ? 'bg-neon-blue/10 hover:bg-neon-blue/20 border-neon-blue/30' : 'bg-neon-purple/10 hover:bg-neon-purple/20 border-neon-purple/30'} border hover:border-white/40 text-white text-[10px] font-black uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 group relative overflow-hidden`}
                            >
                                <Database className={`w-4 h-4 ${report.fingerprint.is_returning ? 'text-neon-blue' : 'text-neon-purple'}`} />
                                PERSIST FINGERPRINT TO INTELLIGENCE DB
                                
                                {/* Hover Effect */}
                                <div className="absolute inset-0 bg-white/5 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Download Button */}
                <button
                    onClick={downloadReport}
                    className="btn-neon btn-neon-green w-full flex items-center justify-center gap-2 cursor-pointer"
                >
                    <Download className="w-4 h-4" />
                    DOWNLOAD INCIDENT REPORT
                </button>
            </div>
        </div>
    );
}
