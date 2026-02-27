import { useMemo } from 'react';
import {
    Shield, Brain, Network, Eye, Bug, Layers, BarChart3,
    ChevronDown, Zap, Lock, Server, Cpu, Activity, Terminal, ShieldAlert
} from 'lucide-react';
import CyberCorner from '../components/CyberCorner';
import MatrixRain from '../components/MatrixRain';

/* ── Feature card ── */
function FeatureCard({ icon: Icon, title, desc, color }) {
    const colorMap = {
        blue: 'text-neon-blue border-neon-blue/30 hover:border-neon-blue/60 hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]',
        green: 'text-neon-green border-neon-green/30 hover:border-neon-green/60 hover:shadow-[0_0_30px_rgba(16,185,129,0.15)]',
        purple: 'text-neon-purple border-neon-purple/30 hover:border-neon-purple/60 hover:shadow-[0_0_30px_rgba(139,92,246,0.15)]',
        cyan: 'text-neon-cyan border-neon-cyan/30 hover:border-neon-cyan/60 hover:shadow-[0_0_30px_rgba(6,182,212,0.15)]',
        pink: 'text-neon-pink border-neon-pink/30 hover:border-neon-pink/60 hover:shadow-[0_0_30px_rgba(236,72,153,0.15)]',
        amber: 'text-neon-amber border-neon-amber/30 hover:border-neon-amber/60 hover:shadow-[0_0_30px_rgba(245,158,11,0.15)]',
    };
    return (
        <div className={`glass-card p-6 border ${colorMap[color]} transition-all duration-300 opacity-0 animate-slide-up group overflow-hidden`}>
            <CyberCorner position="top-right" className={colorMap[color].split(' ')[0]} />
            <Icon className={`w-10 h-10 mb-4 ${colorMap[color].split(' ')[0]} transition-transform group-hover:scale-110`} />
            <h3 className="font-[Orbitron] text-base font-semibold text-white mb-2">{title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
        </div>
    );
}

export default function LandingPage({ onNavigate }) {
    return (
        <div className="relative">
            <MatrixRain />
            {/* ═══ Hero ═══ */}
            <section className="relative h-[calc(100vh-64px)] flex items-center justify-center overflow-hidden">
                {/* Radial gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyber-bg/50 to-cyber-bg pointer-events-none z-[1]" />

                <div className="relative z-[2] text-center px-6 max-w-5xl mx-auto">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-neon-green/30 bg-neon-green/5 mb-8 animate-fade-in">
                        <Activity className="w-4 h-4 text-neon-green animate-pulse" />
                        <span className="text-neon-green text-sm font-mono tracking-widest">SYSTEM ACTIVE — ALL DEFENSES ONLINE</span>
                    </div>

                    <div className="relative p-8 md:p-12 mb-6">
                        <CyberCorner position="top-left" className="text-neon-blue" />
                        <CyberCorner position="bottom-right" className="text-neon-purple" />

                        <h1 className="font-[Orbitron] text-5xl sm:text-7xl font-black text-white mb-6 leading-tight animate-slide-up">
                            <span className="text-glow-blue">LABYRINTH</span>{' '}
                            <span className="text-glow-purple">FORGE</span>
                        </h1>

                        <p className="text-xl sm:text-2xl text-gray-300 mb-4 font-light animate-slide-up" style={{ animationDelay: '0.2s' }}>
                            Adaptive Threat Intelligence system
                        </p>
                        <p className="text-gray-500 max-w-2xl mx-auto mb-10 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                            Secure your code from the inside. Trap your attackers on the outside.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center gap-6 animate-slide-up" style={{ animationDelay: '0.4s' }}>
                            <button className="btn-neon px-8 py-3 text-sm" onClick={() => onNavigate('warroom')}>
                                <span className="flex items-center gap-2"><Zap className="w-4 h-4" /> External Threat</span>
                            </button>
                            <button className="btn-neon btn-neon-amber px-8 py-3 text-sm" onClick={() => onNavigate('devsecops')}>
                                <span className="flex items-center gap-2"><Bug className="w-4 h-4" /> Vulnerability Detector</span>
                            </button>
                            <button className="btn-neon btn-neon-purple px-8 py-3 text-sm" onClick={() => onNavigate('internalthreat')}>
                                <span className="flex items-center gap-2"><ShieldAlert className="w-4 h-4" /> Internal Threat</span>
                            </button>
                        </div>
                    </div>

                    {/* Scroll hint */}
                    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-float">
                        <ChevronDown className="w-6 h-6 text-gray-500 opacity-50" />
                    </div>
                </div>
            </section>



            {/* ═══ Footer ═══ */}
            <footer className="relative z-10 py-8 border-t border-white/5 text-center text-gray-600 text-sm font-mono">
                <p>LABYRINTH FORGE © 2024 — AI-Powered Active Defense Platform</p>
            </footer>
        </div>
    );
}
