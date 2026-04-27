import { useMemo } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from 'recharts';
import { Activity } from 'lucide-react';

export default function ThreatIntelligenceGraph({ profile, commands }) {
    // Generate some mock history data based on the current session stats
    // In a real app, this would be a time-series state updated per command
    const data = useMemo(() => {
        const count = Math.max(10, commands.length);
        const baseThreat = profile.threat_level || 0;
        const baseFrustration = profile.frustration_index || 0;

        return Array.from({ length: 15 }, (_, i) => {
            const factor = (i + 1) / 15;
            return {
                time: `T-${15 - i}m`,
                intensity: Math.floor(baseThreat * factor * (0.8 + Math.random() * 0.4)),
                frustration: Math.floor(baseFrustration * factor * (0.9 + Math.random() * 0.2)),
                load: Math.floor(Math.random() * 100),
            };
        });
    }, [profile.threat_level, profile.frustration_index, commands.length]);

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-black/80 border border-neon-blue/50 p-2 backdrop-blur-md rounded font-mono text-[10px]">
                    <p className="text-neon-blue font-bold">{`TIMESTAMP: ${payload[0].payload.time}`}</p>
                    <p className="text-neon-green">{`THREAT_INTENSITY: ${payload[0].value}%`}</p>
                    <p className="text-neon-purple">{`ATTACK_ANOMALY: ${payload[1].value}%`}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="glass-card overflow-hidden h-[300px] flex flex-col relative border-neon-blue/20">
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between bg-black/40">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-neon-blue animate-pulse" />
                    <span className="font-[Orbitron] text-[10px] font-bold text-neon-blue tracking-widest uppercase">
                        Real-time Threat Intelligence
                    </span>
                </div>
                <div className="flex gap-4">
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-neon-green shadow-[0_0_5px_#00FF41]" />
                        <span className="text-[9px] font-mono text-gray-400">INTENSITY</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-neon-purple shadow-[0_0_5px_#A855F7]" />
                        <span className="text-[9px] font-mono text-gray-400">ANOMALY</span>
                    </div>
                </div>
            </div>

            {/* Graph Content */}
            <div className="flex-1 p-2 pt-4" style={{ minHeight: '200px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorIntensity" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00FF41" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#00FF41" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorAnomaly" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#A855F7" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#A855F7" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                        <XAxis
                            dataKey="time"
                            stroke="#475569"
                            fontSize={9}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="#475569"
                            fontSize={9}
                            tickLine={false}
                            axisLine={false}
                            domain={[0, 100]}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                            type="monotone"
                            dataKey="intensity"
                            stroke="#00FF41"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorIntensity)"
                            isAnimationActive={true}
                            animationDuration={2000}
                        />
                        <Area
                            type="monotone"
                            dataKey="frustration"
                            stroke="#A855F7"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorAnomaly)"
                            isAnimationActive={true}
                            animationDuration={2500}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Scanning Line Effect */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-10">
                <div className="w-full h-[2px] bg-neon-blue/50 absolute animate-[scan_4s_linear_infinite]" />
            </div>


        </div>
    );
}
