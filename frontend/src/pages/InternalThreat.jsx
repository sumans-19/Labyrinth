import { useState } from 'react';
import {
    Users, ShieldAlert, FileWarning, Eye, Activity,
    Search, Filter, Lock, Unlock, Download,
    AlertCircle, Terminal, BarChart3, Database,
    Network, UserX, Bomb, Crosshair, Target
} from 'lucide-react';

export default function InternalThreat({ onNavigate }) {
    const [searchTerm, setSearchTerm] = useState('');

    const THREAT_PROFILES = [
        {
            title: 'The Leaker',
            icon: Download,
            color: 'text-neon-red',
            border: 'border-neon-red/30',
            bg: 'bg-neon-red/5',
            glow: 'group-hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]',
            method: 'Copies sensitive documents (PDFs, Excel) to a USB or personal Cloud.',
            solution: 'Honey-Tokens: Files with tracking pixels. Opening the file pings your FastAPI backend instantly.'
        },
        {
            title: 'The Lateral Mover',
            icon: Network,
            color: 'text-neon-amber',
            border: 'border-neon-amber/30',
            bg: 'bg-neon-amber/5',
            glow: 'group-hover:shadow-[0_0_20px_rgba(245,158,11,0.3)]',
            method: 'Tries to access servers or databases outside their job role.',
            solution: 'Shadow Credentials: Plant fake .env files or config.json on employee machines. Using these "keys" triggers an immediate alarm.'
        },
        {
            title: 'The Impersonator',
            icon: UserX,
            color: 'text-neon-blue',
            border: 'border-neon-blue/30',
            bg: 'bg-neon-blue/5',
            glow: 'group-hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]',
            method: "Uses a co-worker's unattended laptop to access the internal network.",
            solution: 'Biometric Analysis: AI detects if the typing rhythm or command frequency deviates from the "owner\'s" profile.'
        },
        {
            title: 'The Saboteur',
            icon: Bomb,
            color: 'text-neon-purple',
            border: 'border-neon-purple/30',
            bg: 'bg-neon-purple/5',
            glow: 'group-hover:shadow-[0_0_20px_rgba(139,92,246,0.3)]',
            method: 'Injects a "Logic Bomb" or backdoor into the company\'s codebase.',
            solution: 'Aegis Integration: Git-hook intercepts the commit, and Gemini identifies the malicious logic before merge.'
        }
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

            {/* Threat Profiles Animated Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12 max-w-5xl mx-auto mt-12">
                {THREAT_PROFILES.map((tp, i) => (
                    <div
                        key={i}
                        onClick={() => i === 0 && onNavigate ? onNavigate('leaker') : null}
                        className={`glass-card p-8 border min-h-[280px] ${tp.border} ${tp.bg} hover:bg-black/80 transition-all duration-500 group relative overflow-hidden ${tp.glow} ${i === 0 ? 'cursor-pointer hover:scale-[1.02] hover:border-neon-red' : 'cursor-default'}`}
                    >
                        {/* Hover accent background overlay */}
                        <div className={`absolute inset-0 bg-gradient-to-b from-transparent to-black/95 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                        <div className="relative z-10 flex flex-col h-full">
                            {/* Card Header */}
                            <div className="flex items-center gap-4 mb-6">
                                <div className={`p-3 rounded-xl bg-black/50 border ${tp.border}`}>
                                    <tp.icon className={`w-8 h-8 ${tp.color}`} />
                                </div>
                                <h3 className={`font-[Orbitron] font-black text-xl tracking-wider uppercase ${tp.color}`}>
                                    {tp.title}
                                </h3>
                            </div>

                            {/* Default View: Attack Method */}
                            <div className="flex-1 transform transition-all duration-500 group-hover:-translate-y-12 group-hover:opacity-0 relative z-10 mt-2">
                                <div className="text-xs font-mono text-white/40 mb-2 uppercase tracking-widest">Threat Vector</div>
                                <p className="text-sm text-gray-300 leading-relaxed font-sans">
                                    {tp.method}
                                </p>
                            </div>

                            {/* Hover View: Labyrinth Countermeasure */}
                            <div className="absolute inset-x-0 bottom-0 top-24 transform transition-all duration-500 translate-y-12 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 flex flex-col justify-center pointer-events-none">
                                <div className="text-sm font-[Orbitron] text-neon-green mb-3 uppercase tracking-widest font-bold flex items-center gap-2">
                                    <Crosshair className="w-5 h-5" /> Labyrinth Forge Solution
                                </div>
                                <p className="text-base text-white leading-relaxed font-mono border-l-2 border-neon-green/50 pl-4 bg-black/20 py-2">
                                    {tp.solution}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
