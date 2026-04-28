import { useState, useRef, useCallback, useEffect } from 'react';
import AttackerTerminal from '../components/AttackerTerminal';
import NetworkTopology from '../components/NetworkTopology';
import HackerProfile from '../components/HackerProfile';
import DeceptionStatus from '../components/DeceptionStatus';
import SystemCapture from '../components/SystemCapture';
import HydraMode from '../components/HydraMode';
import ThreatPrediction from '../components/ThreatPrediction';
import IncidentReport from '../components/IncidentReport';
import CyberCorner from '../components/CyberCorner';
import MatrixRain from '../components/MatrixRain';
import ThreatIntelligenceGraph from '../components/ThreatIntelligenceGraph';
import MLAnalyticsPanel from '../components/MLAnalyticsPanel';
import { Zap, Radio, Wifi, WifiOff } from 'lucide-react';

export default function WarRoom() {
    const [demoActive, setDemoActive] = useState(false);
    const [liveActive, setLiveActive] = useState(false);
    const [profile, setProfile] = useState({
        threat_level: 0,
        skill_level: 'Unknown',
        frustration_index: 0,
        commands_executed: 0,
        session_duration: 0,
        suspicious_commands: 0,
    });
    const [deceptionPhase, setDeceptionPhase] = useState('');
    const [isolated, setIsolated] = useState(false);
    const [attackerIp, setAttackerIp] = useState(null);
    const [activeNodes, setActiveNodes] = useState(['entry']);
    const [hydraMode, setHydraMode] = useState('ubuntu');
    const [prediction, setPrediction] = useState(null);
    const [reportData, setReportData] = useState(null);
    const [commands, setCommands] = useState([]);
    const wsRef = useRef(null);
    const termRef = useRef(null);

    /* ── Start Live Monitor ── */
    /* ── Start Live Monitor ── */
    const startLiveMonitor = useCallback(() => {
        // Close existing connection if any
        if (wsRef.current) {
            wsRef.current.onclose = null;
            wsRef.current.close();
            wsRef.current = null;
        }

        setLiveActive(true);
        setDemoActive(false); // Ensure demo is off
        setIsolated(false);
        setReportData(null);
        setPrediction(null);
        setDeceptionPhase('🛰️ Awaiting connection from local CLI...');
        setActiveNodes(['entry']);

        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const host = window.location.hostname + ':8000'; // Bypass Vite proxy
        const ws = new WebSocket(`${protocol}://${host}/ws/monitor`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log("Monitor WebSocket connected");
            setDeceptionPhase('🛰️ Live monitor ACTIVE - Awaiting hacker...');
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            console.log("Monitor received:", msg.type);

            if (msg.type === 'init') {
                setAttackerIp(msg.attacker_ip);
                termRef.current?.writeln(`\n\x1b[1;36m${'-'.repeat(60)}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;36m  ${msg.message}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;36m${'-'.repeat(60)}\x1b[0m\n`);
                setDeceptionPhase('🟢 Live data stream established');
            }

            if (msg.type === 'command') {
                termRef.current?.writeln(`\x1b[1;32m${msg.prompt}\x1b[0m${msg.command}`);
                if (msg.output) {
                    msg.output.split('\n').forEach(line => termRef.current?.writeln(line));
                }
                termRef.current?.writeln('');
                if (msg.profile) setProfile(msg.profile);
                if (msg.prediction) setPrediction(msg.prediction);
                if (msg.command) setCommands(prev => [...prev, msg.command]);

                if (msg.risk_event) {
                    setDeceptionPhase(`⚠ HIGH RISK COMMAND: ${msg.command.substring(0, 20)}...`);
                }

                // Progress nodes based on command count or specific commands
                const cmdCount = msg.profile?.commands_executed || 0;
                if (cmdCount >= 1) setActiveNodes(prev => [...new Set([...prev, 'honeypot'])]);
                if (cmdCount >= 4) setActiveNodes(prev => [...new Set([...prev, 'fakedb'])]);
                if (cmdCount >= 8) setActiveNodes(prev => [...new Set([...prev, 'internal'])]);
            }

            if (msg.type === 'isolated') {
                setIsolated(true);
                if (msg.report) setReportData(msg.report);
                termRef.current?.writeln(`\n\x1b[1;31m${'═'.repeat(50)}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m  ${msg.message}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m${'═'.repeat(50)}\x1b[0m\n`);
                setLiveActive(false);
                setDeceptionPhase('🔌 Connection lost');
            }
        };

        ws.onerror = (err) => {
            console.error("Monitor WebSocket error:", err);
            setDeceptionPhase('❌ Connection error');
        };

        ws.onclose = () => {
            console.log("Monitor WebSocket closed");
            setLiveActive(false);
            setDeceptionPhase('🔄 Reconnecting...');
            // Auto-reconnect after 3 seconds unless demo is running
            setTimeout(() => {
                if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
                    startLiveMonitor();
                }
            }, 3000);
        };
    }, []);

    /* ── Start demo simulation ── */
    const startDemo = useCallback(() => {
        // Close existing connection if any
        if (wsRef.current) {
            wsRef.current.onclose = null;
            wsRef.current.close();
            wsRef.current = null;
        }

        setDemoActive(true);
        setLiveActive(false); // Ensure live is off
        setIsolated(false);
        setReportData(null);
        setPrediction(null);
        setDeceptionPhase('');
        setActiveNodes(['entry']);

        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const host = window.location.hostname + ':8000'; // Bypass Vite proxy
        const ws = new WebSocket(`${protocol}://${host}/ws/demo`);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log("Demo WebSocket connected");
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'init') {
                setAttackerIp(msg.attacker_ip);
                termRef.current?.writeln(`\x1b[1;31mSTATUS: ${msg.message}\x1b[0m\n`);
            }

            if (msg.type === 'command') {
                termRef.current?.writeln(`\x1b[1;32m${msg.prompt}\x1b[0m${msg.command}`);
                if (msg.output) {
                    msg.output.split('\n').forEach(line => termRef.current?.writeln(line));
                }
                termRef.current?.writeln('');
                if (msg.profile) setProfile(msg.profile);
                if (msg.prediction) setPrediction(msg.prediction);
                if (msg.command) setCommands(prev => [...prev, msg.command]);

                // Progress nodes
                const cmdCount = msg.profile?.commands_executed || 0;
                if (cmdCount >= 3) setActiveNodes(prev => [...new Set([...prev, 'honeypot'])]);
                if (cmdCount >= 6) setActiveNodes(prev => [...new Set([...prev, 'fakedb'])]);
                if (cmdCount >= 10) setActiveNodes(prev => [...new Set([...prev, 'internal'])]);
            }

            if (msg.type === 'deception') {
                setDeceptionPhase(msg.message);
            }

            if (msg.type === 'dave') {
                msg.message.split('\n').forEach(line => {
                    termRef.current?.writeln(`\x1b[1;33m${line}\x1b[0m`);
                });
                if (msg.profile) setProfile(msg.profile);
            }

            if (msg.type === 'isolated') {
                setIsolated(true);
                if (msg.report) setReportData(msg.report);
                termRef.current?.writeln(`\n\x1b[1;31m${'═'.repeat(50)}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m  ${msg.message}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m${'═'.repeat(50)}\x1b[0m\n`);
                if (msg.profile) setProfile(msg.profile);
                setDemoActive(false);
            }
        };

        ws.onerror = (err) => {
            console.error("Demo WebSocket error:", err);
            termRef.current?.writeln('\x1b[1;31m[CONNECTION ERROR] Could not reach backend. Make sure the FastAPI server is running on port 8000.\x1b[0m');
            setDemoActive(false);
        };

        ws.onclose = () => {
            console.log("Demo WebSocket closed");
            setDemoActive(false);
        };
    }, []);

    /* ── Auto-connect monitor on mount ── */
    useEffect(() => {
        // Auto-start the live monitor so the dashboard is always ready
        startLiveMonitor();

        return () => {
            if (wsRef.current) {
                wsRef.current.onclose = null; // Prevent state update on unmount
                wsRef.current.close();
            }
        };
    }, [startLiveMonitor]);

    return (
        <div className="relative max-w-[1600px] mx-auto px-4 py-6">
            <MatrixRain />
            {/* ── Header ── */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${demoActive ? 'bg-neon-red animate-pulse' : isolated ? 'bg-neon-green' : 'bg-gray-600'}`} />
                    <h1 className="font-[Orbitron] text-2xl font-bold text-white text-glow-blue relative">
                        EXTERNAL THREAT
                        <CyberCorner position="top-right" className="text-neon-blue -top-2 -right-6 !w-4 !h-4" />
                    </h1>
                    {attackerIp && (
                        <span className="font-mono text-sm text-neon-red ml-4">
                            <Wifi className="w-4 h-4 inline mr-1" />
                            Attacker: {attackerIp}
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-3">
                    <HydraMode mode={hydraMode} onModeChange={setHydraMode} />

                    <button
                        className={`btn-neon ${liveActive ? 'btn-neon-blue active' : 'btn-neon-blue'} flex items-center gap-2`}
                        onClick={startLiveMonitor}
                        disabled={liveActive}
                    >
                        <Radio className={`w-4 h-4 ${liveActive ? 'animate-pulse' : ''}`} />
                        {liveActive ? 'Monitor Connected' : 'Connect Local CLI'}
                    </button>

                    <button
                        className={`btn-neon ${demoActive ? 'btn-neon-red' : 'btn-neon-green'} flex items-center gap-2`}
                        onClick={startDemo}
                        disabled={demoActive}
                    >
                        {demoActive ? (
                            <><Radio className="w-4 h-4 animate-pulse" /> Simulation Running...</>
                        ) : (
                            <><Zap className="w-4 h-4" /> Start Demo Simulation</>
                        )}
                    </button>
                </div>
            </div>

            {/* ── Threat Intelligence Graph (Full Width) ── */}
            <div className="mb-4 animate-slide-up">
                <ThreatIntelligenceGraph profile={profile} commands={commands} />
            </div>

            {/* ── Dashboard Grid ── */}
            <div className="grid grid-cols-12 gap-4">
                {/* Left: Terminal */}
                <div className="col-span-12 lg:col-span-7">
                    <AttackerTerminal ref={termRef} mode={hydraMode} />
                </div>

                {/* Right: Panels */}
                <div className="col-span-12 lg:col-span-5 space-y-4">
                    <div className="relative">
                        <CyberCorner position="top-right" className="text-neon-green" />
                        <HackerProfile profile={profile} />
                    </div>
                    <ThreatPrediction prediction={prediction} active={demoActive || liveActive} />
                    <MLAnalyticsPanel profile={profile} commands={commands} active={demoActive || liveActive} />
                    <DeceptionStatus phase={deceptionPhase} active={demoActive} />
                    <div className="relative">
                        <CyberCorner position="bottom-left" className="text-neon-purple" />
                        <SystemCapture isolated={isolated} profile={profile} />
                    </div>
                </div>

                {/* Bottom: Network (Full Width) */}
                <div className="col-span-12">
                    <NetworkTopology activeNodes={activeNodes} commands={commands} />
                </div>

                <div className="col-span-12">
                    {isolated && reportData && (
                        <IncidentReport report={reportData} />
                    )}
                </div>
            </div>
        </div>
    );
}
