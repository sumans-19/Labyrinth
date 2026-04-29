import { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, Radio, Send, Shield, TerminalSquare } from 'lucide-react';
import AttackerTerminal from '../components/AttackerTerminal';
import CyberGrid from '../components/CyberGrid';
import MatrixRain from '../components/MatrixRain';
import { getBackendWsBase, getDashboardUrl } from '../utils/runtime';

const QUICK_COMMANDS = [
  'whoami',
  'ls -la',
  'pwd',
  'cat /etc/passwd',
  'sudo apt update',
  'nmap 10.0.0.0/24',
];

export default function RemoteAttackerConsole() {
  const termRef = useRef(null);
  const socketRef = useRef(null);
  const [command, setCommand] = useState('');
  const [status, setStatus] = useState('CONNECTING');
  const [sessionId, setSessionId] = useState(null);
  const [targetIp, setTargetIp] = useState(null);
  const dashboardUrl = useMemo(() => getDashboardUrl(), []);

  useEffect(() => {
    const socket = new WebSocket(`${getBackendWsBase()}/ws/attacker`);
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus('CONNECTED');
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === 'init') {
        setSessionId(msg.session_id);
        setTargetIp(msg.attacker_ip);
        termRef.current?.writeln(`\x1b[1;31m${msg.message}\x1b[0m`);
        termRef.current?.writeln('\x1b[90mSimulation mode only: commands are processed by the honeypot engine, not a real shell.\x1b[0m');
        termRef.current?.writeln('');
        return;
      }

      if (msg.type === 'output') {
        termRef.current?.writeln(`\x1b[1;32m${msg.prompt}\x1b[0m${msg.command}`);
        if (msg.output) {
          msg.output.split('\n').forEach((line) => termRef.current?.writeln(line));
        }
        termRef.current?.writeln('');
      }
    };

    socket.onerror = () => {
      setStatus('FAILED');
      termRef.current?.writeln('\x1b[1;31m[NETWORK ERROR] Unable to reach the backend attacker bridge.\x1b[0m');
    };

    socket.onclose = () => {
      setStatus('DISCONNECTED');
    };

    return () => {
      socket.close();
    };
  }, []);

  const submitCommand = (value) => {
    const nextCommand = value.trim();
    if (!nextCommand || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'command',
      command: nextCommand,
    }));
    setCommand('');
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <CyberGrid />
      <MatrixRain />

      <main className="relative z-10 container-responsive py-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <TerminalSquare className="w-7 h-7 text-neon-red" />
              <h1 className="font-[Orbitron] text-2xl font-bold text-white tracking-wider">
                REMOTE OPERATOR CONSOLE
              </h1>
            </div>
            <p className="text-sm text-gray-400 max-w-3xl">
              This page is for a controlled demo only. Commands go into the Labyrinth Forge honeypot simulator and are mirrored to the dashboard with live ML threat analysis.
            </p>
          </div>

          <div className="glass-card p-4 min-w-[280px]">
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400 uppercase tracking-[0.2em] mb-3">
              <Radio className={`w-3 h-3 ${status === 'CONNECTED' ? 'text-neon-green animate-pulse' : 'text-neon-red'}`} />
              Session Link
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="text-gray-400">Status</span>
                <span className="font-[Orbitron] text-neon-blue">{status}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-gray-400">Session</span>
                <span className="font-mono text-white">{sessionId || 'pending'}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-gray-400">Source IP</span>
                <span className="font-mono text-white">{targetIp || 'pending'}</span>
              </div>
              <div className="pt-2 border-t border-white/10">
                <div className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.2em] mb-1">Dashboard URL</div>
                <div className="text-xs text-neon-cyan break-all">{dashboardUrl}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="glass-card p-4 border border-neon-amber/20 bg-neon-amber/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-neon-amber mt-0.5 shrink-0" />
            <div>
              <div className="font-[Orbitron] text-sm text-neon-amber">Safe Simulation Boundary</div>
              <div className="text-sm text-gray-300 mt-1">
                This console does not connect to or execute on a real terminal. It only drives the defensive honeypot workflow for demonstration and monitoring.
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          <div className="xl:col-span-3">
            <AttackerTerminal
              ref={termRef}
              mode="ubuntu"
              title="REMOTE OPERATOR SESSION"
              waitingMessage="Connecting to the attacker WebSocket bridge..."
              helperMessage='Type a command below to drive the simulation.'
            />
          </div>

          <div className="glass-card p-4 space-y-4">
            <div>
              <div className="flex items-center gap-2 text-sm font-[Orbitron] text-neon-purple mb-2">
                <Shield className="w-4 h-4" />
                Demo Macros
              </div>
              <div className="space-y-2">
                {QUICK_COMMANDS.map((quickCommand) => (
                  <button
                    key={quickCommand}
                    type="button"
                    onClick={() => submitCommand(quickCommand)}
                    className="w-full text-left px-3 py-2 rounded border border-white/10 bg-black/30 hover:border-neon-blue/40 hover:bg-neon-blue/5 transition-all font-mono text-xs text-gray-200"
                  >
                    {quickCommand}
                  </button>
                ))}
              </div>
            </div>

            <div className="rounded border border-white/10 bg-black/20 p-3">
              <div className="text-[10px] font-mono text-gray-500 uppercase tracking-[0.2em] mb-2">Presentation Tip</div>
              <div className="text-xs text-gray-300">
                Keep the External Threat dashboard open on the other laptop. Each command you send here is mirrored there with updated prediction, MITRE mapping, and anomaly scoring.
              </div>
            </div>
          </div>
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            submitCommand(command);
          }}
          className="glass-card p-4"
        >
          <div className="flex flex-col lg:flex-row gap-3">
            <input
              type="text"
              value={command}
              onChange={(event) => setCommand(event.target.value)}
              placeholder="Enter a simulated command..."
              className="flex-1 bg-black/40 border border-neon-blue/30 rounded px-4 py-3 font-mono text-sm text-white focus:outline-none focus:border-neon-blue"
            />
            <button
              type="submit"
              className="btn-neon btn-neon-blue flex items-center justify-center gap-2 min-w-[180px]"
              disabled={status !== 'CONNECTED' || !command.trim()}
            >
              <Send className="w-4 h-4" />
              Send Command
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
