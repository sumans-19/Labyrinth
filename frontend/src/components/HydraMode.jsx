import { Monitor, Server, Cpu } from 'lucide-react';

const MODES = [
    { id: 'ubuntu', label: 'Ubuntu', icon: Monitor, color: 'neon-green' },
    { id: 'windows', label: 'Windows', icon: Server, color: 'neon-blue' },
];

export default function HydraMode({ mode, onModeChange }) {
    return (
        <div className="flex items-center gap-1 p-1 rounded-lg bg-black/30 border border-white/5">
            {MODES.map((m) => {
                const Icon = m.icon;
                const isActive = mode === m.id;
                return (
                    <button
                        key={m.id}
                        onClick={() => onModeChange(m.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-mono transition-all duration-200 cursor-pointer
              ${isActive
                                ? `bg-${m.color}/15 text-${m.color} border border-${m.color}/30`
                                : 'text-gray-500 hover:text-gray-300 border border-transparent'
                            }`}
                        title={`Switch to ${m.label} Simulation`}
                    >
                        <Icon className="w-3.5 h-3.5" />
                        {m.label}
                    </button>
                );
            })}
        </div>
    );
}
