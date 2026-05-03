import { useState, useEffect } from 'react';
import { Activity, BrainCircuit, ShieldAlert, Target, Crosshair } from 'lucide-react';
import { getBackendHttpBase } from '../utils/runtime';


export default function MLAnalyticsPanel({ profile, commands, active }) {
    const [mlState, setMlState] = useState({
        anomaly_score: 0,
        is_anomaly: false,
        threat_label: 'NORMAL',
        confidence: 100,
        cluster_id: 0,
        psych_profile: 'Neutral Observer',
        mitre_tag: { id: 'N/A', name: 'None', tactic: 'None' }
    });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Fetch ML insights when tracking is active or commands list updates
        if (!active || commands.length === 0) return;

        const cmd_freq = commands.length / Math.max((profile.session_duration / 60), 1);
        const unique_cmds = new Set(commands).size;
        const duration = profile.session_duration || 1;
        const rpm = (commands.length / duration) * 60;
        
        // Mock ip_score (could be derived from profile or backend)
        const ip_score = 50; 

        const payload = {
            command_list: commands,
            cmd_freq: cmd_freq,
            duration: duration,
            unique_cmds: unique_cmds,
            ip_score: ip_score,
            rpm: rpm
        };

        const fetchMLData = async () => {
            setLoading(true);
            try {
                const response = await fetch(`${getBackendHttpBase()}/api/ml/analyze-session`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    const data = await response.json();
                    setMlState(data);
                }
            } catch (error) {
                console.error("ML Engine Fetch Error:", error);
            } finally {
                setLoading(false);
            }
        };

        // Throttle updates so we don't bombard the server on every rapid keystroke/command
        const timeoutId = setTimeout(fetchMLData, 500);
        return () => clearTimeout(timeoutId);
    }, [commands, profile, active]);

    // Anomaly color logic
    const scoreColor = mlState.anomaly_score > 75 ? 'text-neon-red shadow-neon-red' 
                     : mlState.anomaly_score > 40 ? 'text-neon-purple shadow-neon-purple'
                     : 'text-neon-green shadow-neon-green';

    const scoreBarColor = mlState.anomaly_score > 75 ? 'bg-neon-red' 
                     : mlState.anomaly_score > 40 ? 'bg-neon-purple'
                     : 'bg-neon-green';

    return (
        <div className="glass-card p-4 relative overflow-hidden group animate-fade-in border border-white/5">
            <div className="flex items-center justify-between mb-4">
                <h3 className="font-[Orbitron] text-sm text-neon-blue font-bold flex items-center gap-2">
                    <BrainCircuit className={`w-4 h-4 ${loading ? 'animate-pulse' : ''}`} />
                    ML THREAT ANALYSIS
                </h3>
            </div>

            <div className="space-y-4">
                {/* 1. Anomaly Score */}
                <div>
                    <div className="flex justify-between items-end mb-1">
                        <span className="text-xs text-gray-400 font-mono tracking-wider flex items-center gap-1">
                            <Activity className="w-3 h-3"/> ISOLATION FOREST ENSEMBLE
                        </span>
                        <span className={`text-sm font-bold font-mono ${scoreColor}`}>
                            {mlState.anomaly_score.toFixed(1)}% ANOMALY
                        </span>
                    </div>
                    <div className="h-1.5 bg-black/50 rounded-full overflow-hidden">
                        <div 
                            className={`h-full ${scoreBarColor} transition-all duration-700 ease-in-out`}
                            style={{ width: `${Math.max(0, Math.min(100, mlState.anomaly_score))}%`, boxShadow: `0 0 10px var(--tw-colors-neon-${scoreBarColor.split('-')[2]})` }}
                        />
                    </div>
                </div>

                {/* 2. Threat Classifier & Clustering */}
                <div className="flex flex-col gap-2 p-3 bg-black/30 border border-white/10 rounded">
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-400 font-mono">THREAT CLASSIFIER (PIPELINE)</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono border ${mlState.threat_label === 'NORMAL' ? 'border-neon-green text-neon-green bg-neon-green/10' : 'border-neon-red text-neon-red bg-neon-red/10'}`}>
                            {mlState.threat_label}
                        </span>
                    </div>
                    <div className="flex justify-between items-center">
                         <span className="text-xs text-gray-400 font-mono">DBSCAN CLUSTER ID</span>
                         <span className={`text-xs font-mono font-bold ${mlState.cluster_id === -1 ? 'text-neon-red animate-pulse' : 'text-neon-blue'}`}>
                             {mlState.cluster_id === -1 ? 'UNKNOWN_CLUSTER_DETECTED' : `CLUSTER_${mlState.cluster_id}`}
                         </span>
                    </div>
                </div>

                {/* 3. Psychological Profiler */}
                <div className="flex justify-between items-center p-3 bg-black/30 border border-white/10 rounded">
                    <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
                        <Target className="w-3 h-3" />
                        ATTACKER ARCHETYPE
                    </div>
                    <span className="text-sm font-[Orbitron] text-neon-purple tracking-wider">
                        {mlState.psych_profile}
                    </span>
                </div>

                {/* 4. MITRE ATT&CK Mapper */}
                <div className="p-3 bg-black/30 border border-white/10 rounded">
                    <div className="flex items-center gap-2 text-xs text-gray-400 font-mono mb-2">
                        <Crosshair className="w-3 h-3" />
                        MITRE ATT&CK MAPPING
                    </div>
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center justify-between">
                            <span className="text-xs font-mono text-neon-blue bg-neon-blue/10 px-1 rounded">{mlState.mitre_tag.id}</span>
                            <span className="text-xs font-mono text-gray-300">{mlState.mitre_tag.name}</span>
                        </div>
                        <div className="text-[10px] text-gray-500 font-mono text-right mt-1 uppercase border-t border-white/5 pt-1">
                            TACTIC: {mlState.mitre_tag.tactic}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
