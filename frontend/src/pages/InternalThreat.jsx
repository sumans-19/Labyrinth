import { useState, useMemo } from 'react';
import {
    Users, ShieldAlert, FileWarning, Eye, Activity,
    Search, Filter, Lock, Unlock, Download,
    AlertCircle, Terminal, BarChart3, Database
} from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts';
import CyberCorner from '../components/CyberCorner';

const MOCK_ALERTS = [
    { id: 'ALT-8821', user: 'j.smith@acme.com', action: 'Bulk File Download', risk: 'HIGH', time: '10:24:15', dept: 'Engineering' },
    { id: 'ALT-8822', user: 's.chen@acme.com', action: 'Off-hours SSH Access', risk: 'MEDIUM', time: '11:05:02', dept: 'IT Admin' },
    { id: 'ALT-8823', user: 'unknown_service', action: 'API Key Leakage', risk: 'CRITICAL', time: '12:15:44', dept: 'DevOps' },
    { id: 'ALT-8824', user: 'm.wilson@acme.com', action: 'External Data Upload', risk: 'HIGH', time: '13:42:11', dept: 'Finance' },
    { id: 'ALT-8825', user: 'a.sharma@acme.com', action: 'Privilege Escalation', risk: 'CRITICAL', time: '14:20:00', dept: 'Marketing' },
];

const MOCK_DATA_FLOW = [
    { name: 'Mon', internal: 4000, external: 2400 },
    { name: 'Tue', internal: 3000, external: 1398 },
    { name: 'Wed', internal: 2000, external: 9800 },
    { name: 'Thu', internal: 2780, external: 3908 },
    { name: 'Fri', internal: 1890, external: 4800 },
    { name: 'Sat', internal: 2390, external: 3800 },
    { name: 'Sun', internal: 3490, external: 4300 },
];

export default function InternalThreat() {
    const [searchTerm, setSearchTerm] = useState('');

    const stats = [
        { label: 'Active Sessions', value: '142', icon: Activity, color: '#3b82f6' },
        { label: 'High Risk Users', value: '04', icon: ShieldAlert, color: '#ef4444' },
        { label: 'Data Points', value: '2.4M', icon: Database, color: '#10b981' },
        { label: 'Anomalies', value: '12', icon: FileWarning, color: '#f59e0b' },
    ];

    return (
        <div className="max-w-[1600px] mx-auto px-6 py-10 animate-fade-in lg:px-12 space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-neon-purple/10 border border-neon-purple/20 rounded-xl">
                        <Users className="w-8 h-8 text-neon-purple" />
                    </div>
                    <div>
                        <h1 className="font-[Orbitron] text-3xl font-black text-white tracking-widest uppercase">
                            Internal Threat Monitor
                        </h1>
                        <p className="text-xs text-gray-500 font-mono tracking-widest uppercase mt-1">
                            Insider Leakage Detection & Behavioral Forensic Analysis
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                        <input
                            type="text"
                            placeholder="Search identities..."
                            className="bg-black/40 border border-white/10 rounded-lg py-2 pl-10 pr-4 font-mono text-xs text-gray-300 w-64 outline-none focus:border-neon-purple/50 transition-colors"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button className="btn-neon btn-neon-purple text-[10px] py-2">
                        <Download className="w-3.5 h-3.5" /> EXPORT LOGS
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((s, i) => (
                    <div key={i} className="glass-card p-6 border-white/5 bg-black/20 hover:border-white/10 transition-colors relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-5 transition-opacity group-hover:opacity-10">
                            <s.icon size={60} color={s.color} />
                        </div>
                        <s.icon size={20} color={s.color} className="mb-4" />
                        <div className="font-[Orbitron] text-2xl font-black text-white mb-1">{s.value}</div>
                        <div className="text-[10px] font-mono text-gray-500 uppercase tracking-widest font-bold">{s.label}</div>
                    </div>
                ))}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-12 gap-6">

                {/* Left: Behavioral Graph */}
                <div className="col-span-12 lg:col-span-8 flex flex-col space-y-6">
                    <div className="glass-card flex-1 p-6 relative h-[450px] border-neon-purple/20 bg-black/40">
                        <CyberCorner position="top-right" className="text-neon-purple" />
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-2">
                                <BarChart3 className="w-4 h-4 text-neon-purple" />
                                <span className="font-[Orbitron] text-xs font-bold text-neon-purple tracking-widest uppercase">
                                    Network Traffic & Exfiltration Flow
                                </span>
                            </div>
                            <div className="flex gap-4 text-[9px] font-mono text-gray-500 uppercase">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-neon-purple" /> INTERNAL
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-neon-cyan" /> EXTERNAL
                                </div>
                            </div>
                        </div>

                        <div className="h-[350px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={MOCK_DATA_FLOW}>
                                    <defs>
                                        <linearGradient id="colorInt" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#A855F7" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#A855F7" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorExt" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                                    <XAxis dataKey="name" stroke="#ffffff20" fontSize={10} axisLine={false} tickLine={false} />
                                    <YAxis stroke="#ffffff20" fontSize={10} axisLine={false} tickLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0a0e1a', border: '1px solid #ffffff10', fontSize: '12px' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area type="monotone" dataKey="internal" stroke="#A855F7" fillOpacity={1} fill="url(#colorInt)" />
                                    <Area type="monotone" dataKey="external" stroke="#06B6D4" fillOpacity={1} fill="url(#colorExt)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="glass-card p-6 border-white/5 bg-black/20">
                        <div className="flex items-center gap-2 mb-6 text-neon-blue">
                            <Terminal className="w-4 h-4" />
                            <span className="font-[Orbitron] text-[10px] font-bold tracking-widest uppercase">Anomaly Analysis Stream</span>
                        </div>
                        <div className="space-y-4">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="flex gap-4 text-xs font-mono p-3 rounded bg-white/[0.02] border-l-2 border-neon-purple/40">
                                    <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span>
                                    <span className="text-neon-purple font-bold">INFO_CORE:</span>
                                    <span className="text-gray-400">Heuristic scan complete on Node_{i * 1024}. No unauthorized decryption keys found.</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right: Alert Feed */}
                <div className="col-span-12 lg:col-span-4 flex flex-col space-y-6">
                    <div className="glass-card p-6 relative border-white/5 bg-[#0d111b]/80 h-full overflow-hidden flex flex-col shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-2">
                                <ShieldAlert className="w-4 h-4 text-neon-red" />
                                <span className="font-[Orbitron] text-xs font-bold text-white tracking-widest uppercase">High Risk Alerts</span>
                            </div>
                            <span className="text-[10px] font-mono text-gray-500 px-2 py-0.5 rounded bg-white/5">LIVE</span>
                        </div>

                        <div className="flex-1 space-y-3 overflow-y-auto custom-scrollbar">
                            {MOCK_ALERTS.map((alert, i) => (
                                <div key={i} className="p-4 rounded-lg bg-white/[0.03] border border-white/5 hover:border-white/10 transition-colors group relative overflow-hidden">
                                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${alert.risk === 'CRITICAL' ? 'bg-neon-pink' : alert.risk === 'HIGH' ? 'bg-neon-amber' : 'bg-neon-blue'
                                        }`} />
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="text-[10px] font-bold text-gray-200 uppercase tracking-tight">{alert.user}</div>
                                        <span className={`text-[8px] font-black px-1.5 py-0.5 rounded ${alert.risk === 'CRITICAL' ? 'text-neon-pink' : alert.risk === 'HIGH' ? 'text-neon-amber' : 'text-neon-blue'
                                            }`}>
                                            {alert.risk}
                                        </span>
                                    </div>
                                    <div className="text-[11px] text-gray-500 flex justify-between">
                                        <span>{alert.action}</span>
                                        <span className="font-mono">{alert.time}</span>
                                    </div>
                                    <div className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                                        <button className="text-[8px] font-black text-neon-purple border border-neon-purple/30 px-2 py-1 rounded hover:bg-neon-purple/10 uppercase tracking-widest">Investigate</button>
                                        <button className="text-[8px] font-black text-gray-400 border border-white/10 px-2 py-1 rounded hover:bg-white/5 uppercase tracking-widest">Dismiss</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
