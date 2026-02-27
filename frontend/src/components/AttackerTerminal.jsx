import { useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Terminal as XTerminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import { Monitor } from 'lucide-react';

const AttackerTerminal = forwardRef(({ mode }, ref) => {
    const termDivRef = useRef(null);
    const terminalRef = useRef(null);
    const fitAddonRef = useRef(null);

    useImperativeHandle(ref, () => ({
        writeln: (text) => terminalRef.current?.writeln(text),
        write: (text) => terminalRef.current?.write(text),
        clear: () => terminalRef.current?.clear(),
    }));

    useEffect(() => {
        if (!termDivRef.current) return;

        const terminal = new XTerminal({
            theme: {
                background: '#0d1117',
                foreground: '#c9d1d9',
                cursor: '#58a6ff',
                cursorAccent: '#0d1117',
                selectionBackground: '#264f78',
                black: '#0d1117',
                red: '#ff7b72',
                green: '#3fb950',
                yellow: '#d29922',
                blue: '#58a6ff',
                magenta: '#bc8cff',
                cyan: '#39d353',
                white: '#c9d1d9',
                brightBlack: '#484f58',
                brightRed: '#ffa198',
                brightGreen: '#56d364',
                brightYellow: '#e3b341',
                brightBlue: '#79c0ff',
                brightMagenta: '#d2a8ff',
                brightCyan: '#56d364',
                brightWhite: '#f0f6fc',
            },
            fontSize: 14,
            fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
            cursorBlink: true,
            cursorStyle: 'block',
            scrollback: 5000,
            allowTransparency: true,
        });

        const fitAddon = new FitAddon();
        terminal.loadAddon(fitAddon);
        terminal.open(termDivRef.current);
        fitAddon.fit();

        terminalRef.current = terminal;
        fitAddonRef.current = fitAddon;

        // Welcome message
        terminal.writeln('\x1b[1;36m                        ╔═══════════════════════════════════════════════════╗\x1b[0m');
        terminal.writeln('\x1b[1;36m                        ║       LABYRINTH FORGE — ATTACKER TERMINAL         ║\x1b[0m');
        terminal.writeln('\x1b[1;36m                        ║       Honeypot SSH Session Monitor                ║\x1b[0m');
        terminal.writeln('\x1b[1;36m                        ╚═══════════════════════════════════════════════════╝\x1b[0m');
        terminal.writeln('');
        terminal.writeln('\x1b[90mWaiting for attacker connection...\x1b[0m');
        terminal.writeln('\x1b[90mClick "Start Live Attack Simulation" to begin.\x1b[0m');
        terminal.writeln('');

        const handleResize = () => fitAddon.fit();
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            terminal.dispose();
        };
    }, []);

    const modeLabel = { ubuntu: 'Ubuntu 20.04 LTS', windows: 'Windows Server 2019', iot: 'IoT Gateway v2.3' }[mode] || mode;

    return (
        <div className="glass-card overflow-hidden scanline-overlay">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-black/30">
                <div className="flex items-center gap-2">
                    <Monitor className="w-4 h-4 text-neon-green" />
                    <span className="font-[Orbitron] text-xs font-semibold text-neon-green tracking-wider">LIVE ATTACKER TERMINAL</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-gray-500">{modeLabel}</span>
                    <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-red-500/80" />
                        <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                        <div className="w-3 h-3 rounded-full bg-green-500/80" />
                    </div>
                </div>
            </div>

            {/* Terminal */}
            <div ref={termDivRef} className="h-[420px]" />
        </div>
    );
});

AttackerTerminal.displayName = 'AttackerTerminal';
export default AttackerTerminal;
