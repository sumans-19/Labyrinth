import { useState, useEffect } from 'react';
import { BrainCircuit, CheckCircle2, Loader2 } from 'lucide-react';

const PHASES_IDLE = [
    { icon: '🛡️', text: 'Deception Engine standing by...' },
];

export default function DeceptionStatus({ phase, active }) {
    const [log, setLog] = useState([]);

    useEffect(() => {
        if (phase) {
            setLog(prev => {
                if (prev.find(l => l.text === phase)) return prev;
                return [...prev.slice(-6), { text: phase, time: new Date().toLocaleTimeString() }];
            });
        }
    }, [phase]);

    return (
        <div className="glass-card overflow-hidden">
            <div className="px-4 py-3 border-b border-white/5 bg-black/30 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-neon-cyan" />
                <span className="font-[Orbitron] text-xs font-semibold text-neon-cyan tracking-wider">AI DECEPTION ENGINE</span>
                {active && <Loader2 className="w-3 h-3 text-neon-cyan animate-spin ml-auto" />}
            </div>

            <div className="p-3 space-y-1.5 max-h-[180px] overflow-y-auto">
                {log.length === 0 ? (
                    <div className="flex items-center gap-2 text-gray-500 text-xs font-mono p-2">
                        <span>🛡️</span>
                        <span>Deception engine standing by...</span>
                    </div>
                ) : (
                    log.map((entry, i) => (
                        <div
                            key={i}
                            className="flex items-start gap-2 text-xs font-mono p-2 rounded-lg bg-white/3 animate-fade-in"
                        >
                            <span className="text-gray-600 shrink-0">{entry.time}</span>
                            <span className="text-gray-300">{entry.text}</span>
                            {i === log.length - 1 && active ? (
                                <Loader2 className="w-3 h-3 text-neon-cyan animate-spin ml-auto shrink-0" />
                            ) : (
                                <CheckCircle2 className="w-3 h-3 text-neon-green ml-auto shrink-0" />
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
