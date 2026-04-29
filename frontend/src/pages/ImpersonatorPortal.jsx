import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Terminal, Cpu, UserX, ShieldAlert } from 'lucide-react';
import ImpersonatorPanel from '../components/impersonator/ImpersonatorPanel';
import { KeystrokeCapture } from '../utils/KeystrokeCapture';

export default function ImpersonatorPortal({ onNavigate }) {
    const [consoleHistory, setConsoleHistory] = useState([
        { type: 'info', text: 'LABYRINTH OS v2.1' },
        { type: 'info', text: 'Terminal initialized. Ready for command input.' },
        { type: 'info', text: 'Type normal commands (ls, cat, whoami) to establish baseline.' }
    ]);
    const [commandInput, setCommandInput] = useState('');
    const consoleEndRef = useRef(null);
    const inputRef = useRef(null);
    const captureRef = useRef(null);

    const sessionId = 'session_test_xyz';
    const userId = 'admin_user';

    useEffect(() => {
        // Initialize keystroke capture
        captureRef.current = new KeystrokeCapture(sessionId, userId, (scoreData) => {
            // Dispatch event for the Panel
            window.dispatchEvent(new CustomEvent('irs-update', { detail: scoreData }));
        });

        if (inputRef.current) {
            captureRef.current.attach(inputRef.current);
        }

        return () => {
            if (captureRef.current) captureRef.current.detach();
        };
    }, []);

    useEffect(() => {
        consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [consoleHistory]);

    const handleCommand = (e) => {
        e.preventDefault();
        const cmd = commandInput.trim().toLowerCase();
        if (!cmd) return;

        const newHistory = [...consoleHistory, { type: 'input', text: cmd }];
        
        if (cmd === 'clear') {
            setConsoleHistory([]);
            setCommandInput('');
            return;
        } else if (cmd === 'ls') {
            newHistory.push({ type: 'info', text: 'passwords.xlsx   auth.log   main.py   config.json' });
        } else if (cmd.startsWith('cat ')) {
            const file = cmd.split(' ')[1];
            newHistory.push({ type: 'info', text: `Opening ${file}...` });
            
            // If they access decoy, notify backend
            fetch('/api/impersonator/event', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_id: userId,
                    event_type: 'file_access',
                    timestamp: Date.now(),
                    payload: { files_accessed: [file.includes('password') ? '/backend/decoys/passwords.xlsx' : file] }
                })
            }).then(r => r.json()).then(score => {
                window.dispatchEvent(new CustomEvent('irs-update', { detail: { ...score, command: cmd } }));
            });
        } else {
            // Normal command, capture logic handles event dispatch but let's pass the cmd name along
            // We can't easily intercept KeystrokeCapture's dispatch here without modifying it,
            // so KeystrokeCapture needs to just record keystrokes. But wait, KeystrokeCapture sends "event_type: keystroke".
            // Since we want the timeline to show commands, let's just dispatch the command separately if we don't intercept it.
            // Actually, we'll let KeystrokeCapture handle it, but we can also fire a placeholder event if we wanted.
            newHistory.push({ type: 'error', text: `command not found: ${cmd}` });
        }

        setConsoleHistory(newHistory);
        setCommandInput('');
    };

    return (
        <div className="max-w-[1600px] mx-auto px-6 py-10 lg:px-12 space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/5">
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => onNavigate('internalthreat')}
                        className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors group"
                    >
                        <ArrowLeft className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
                    </button>
                    <div className="p-3 bg-neon-blue/10 border border-neon-blue/30 rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                        <UserX className="w-8 h-8 text-neon-blue" />
                    </div>
                    <div>
                        <h1 className="font-[Orbitron] text-3xl font-black text-white tracking-widest uppercase drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]">
                            The Impersonator Portal
                        </h1>
                        <p className="text-xs text-gray-500 font-mono tracking-widest uppercase mt-1">
                            Behavioral Biometric ML Engine Testing
                        </p>
                    </div>
                </div>
                
                <div className="flex items-center gap-3">
                    <button 
                        onClick={() => {
                            fetch(`/api/impersonator/reset/${sessionId}/${userId}`, { method: 'POST' })
                                .then(() => window.dispatchEvent(new CustomEvent('irs-update', { detail: { phase: 'LEARNING', progress: '0/30' } })));
                            setConsoleHistory([]);
                        }}
                        className="btn-neon btn-neon-blue text-[10px] py-2"
                    >
                        RESET BASELINE
                    </button>
                    <button 
                        onClick={() => {
                            fetch('/api/impersonator/event', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    session_id: sessionId,
                                    user_id: userId,
                                    event_type: 'keystroke',
                                    timestamp: Date.now(),
                                    payload: {
                                        keystrokes: Array(10).fill({ key: 'X', dwell: 400, flight: 600 })
                                    }
                                })
                            }).then(r => r.json()).then(score => {
                                window.dispatchEvent(new CustomEvent('irs-update', { detail: { ...score, command: 'SYNTHETIC_ANOMALY_PAYLOAD' } }));
                            });
                        }}
                        className="btn-neon btn-neon-red text-[10px] py-2 flex items-center gap-2"
                    >
                        <ShieldAlert className="w-3.5 h-3.5" /> SYNTHETIC ATTACK
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Simulation Console */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center gap-3 mb-4">
                        <Terminal className="w-5 h-5 text-neon-blue" />
                        <h2 className="font-[Orbitron] text-sm font-bold text-white uppercase tracking-widest drop-shadow-[0_0_5px_rgba(59,130,246,0.5)]">Active Terminal Session</h2>
                    </div>

                    <div className="glass-card bg-black/90 border-neon-blue/30 shadow-[0_0_20px_rgba(59,130,246,0.1)] p-6 font-mono text-[11px] overflow-hidden group">
                        <div className="flex items-center justify-between mb-4 border-b border-neon-blue/20 pb-2">
                            <span className="text-neon-blue font-bold tracking-widest drop-shadow-[0_0_5px_rgba(59,130,246,0.5)]">admin_user@prod-server</span>
                        </div>
                        <div className="space-y-1.5 h-[400px] overflow-y-auto custom-scrollbar mb-4 pr-2">
                            {consoleHistory.map((line, i) => (
                                <p key={i} className={
                                    line.type === 'input' ? 'text-neon-green' : 
                                    line.type === 'error' ? 'text-neon-red' : 'text-gray-400'
                                }>
                                    {line.type === 'input' && <span className="mr-2">$</span>}
                                    {line.text}
                                </p>
                            ))}
                            <div ref={consoleEndRef} />
                        </div>
                        <form onSubmit={handleCommand} className="flex items-center gap-2 border-t border-neon-blue/20 pt-3 group-focus-within:border-neon-blue/50 transition-colors">
                            <span className="text-neon-green font-bold drop-shadow-[0_0_5px_rgba(16,185,129,0.5)]">$</span>
                            <input 
                                ref={inputRef}
                                type="text"
                                autoFocus
                                className="bg-transparent border-none outline-none text-white w-full placeholder-gray-600"
                                value={commandInput}
                                onChange={(e) => setCommandInput(e.target.value)}
                                placeholder="Start typing... keystrokes are being analyzed."
                            />
                        </form>
                    </div>
                </div>

                {/* Dashboard Panel */}
                <div className="space-y-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Cpu className="w-5 h-5 text-neon-blue" />
                        <h2 className="font-[Orbitron] text-sm font-bold text-neon-blue uppercase tracking-widest">Biometric ML Engine</h2>
                    </div>
                    <ImpersonatorPanel sessionId={sessionId} userId={userId} />

                </div>
            </div>
        </div>
    );
}
