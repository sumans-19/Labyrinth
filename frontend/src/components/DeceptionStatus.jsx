import { useState, useEffect } from 'react';
import { BrainCircuit, CheckCircle2, Loader2, ChevronRight } from 'lucide-react';

export default function DeceptionStatus({ phase, active }) {
    const [log, setLog] = useState([]);

    useEffect(() => {
        if (phase) {
            // Remove leading emoji if present for the log display
            const cleanPhase = phase.replace(/^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]\s*/u, '');
            setLog(prev => {
                if (prev.find(l => l.text === cleanPhase)) return prev;
                return [...prev.slice(-6), { text: cleanPhase, time: new Date().toLocaleTimeString() }];
            });
        }
    }, [phase]);

    return (
        <div className="glass-card overflow-hidden border-neon-cyan/20">
            <div className="px-4 py-3 border-b border-white/5 bg-black/30 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-neon-cyan" />
                <span className="font-[Orbitron] text-xs font-semibold text-neon-cyan tracking-wider uppercase">Forensic Deception Stream</span>
                {active && <Loader2 className="w-3 h-3 text-neon-cyan animate-spin ml-auto" />}
            </div>

            <div className="p-3 space-y-1.5 max-h-[180px] overflow-y-auto custom-scrollbar">
                {log.length === 0 ? (
                    <div className="flex items-center gap-2 text-gray-500 text-[10px] font-mono p-2">
                        <ChevronRight className="w-3 h-3 text-neon-cyan animate-pulse" />
                        <span className="uppercase tracking-widest">Awaiting system trigger...</span>
                    </div>
                ) : (
                    log.map((entry, i) => (
                        <div
                            key={i}
                            className={`flex items-center gap-3 text-[11px] font-mono p-2 rounded border border-transparent hover:border-white/5 transition-all ${i === log.length - 1 ? 'bg-neon-cyan/5 border-neon-cyan/10' : 'bg-white/[0.02]'}`}
                        >
                            <span className="text-gray-600 shrink-0 text-[10px]">{entry.time}</span>
                            <div className="flex items-center gap-1.5 overflow-hidden">
                                <ChevronRight className={`w-3.5 h-3.5 shrink-0 ${i === log.length - 1 ? 'text-neon-cyan animate-pulse' : 'text-gray-700'}`} />
                                <span className={`${i === log.length - 1 ? 'text-white' : 'text-gray-400'} truncate`}>{entry.text}</span>
                            </div>
                            <div className="ml-auto flex items-center gap-2">
                                {i === log.length - 1 && active ? (
                                    <div className="flex gap-0.5">
                                        <div className="w-1 h-1 bg-neon-cyan animate-bounce [animation-delay:-0.3s]" />
                                        <div className="w-1 h-1 bg-neon-cyan animate-bounce [animation-delay:-0.15s]" />
                                        <div className="w-1 h-1 bg-neon-cyan animate-bounce" />
                                    </div>
                                ) : (
                                    <CheckCircle2 className="w-3 h-3 text-neon-green/40 shrink-0" />
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
