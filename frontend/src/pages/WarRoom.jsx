import { useState, useRef, useCallback, useEffect } from 'react';
import { Copy, Radio, Wifi, Zap } from 'lucide-react';
import AttackerTerminal from '../components/AttackerTerminal';
import NetworkTopology from '../components/NetworkTopology';
import HackerProfile from '../components/HackerProfile';
import DeceptionStatus from '../components/DeceptionStatus';
import SystemCapture from '../components/SystemCapture';
import HydraMode from '../components/HydraMode';
import ThreatPrediction from '../components/ThreatPrediction';
import IncidentReport from '../components/IncidentReport';
import CommandTelemetry from '../components/CommandTelemetry';
import CyberCorner from '../components/CyberCorner';
import MatrixRain from '../components/MatrixRain';
import ThreatIntelligenceGraph from '../components/ThreatIntelligenceGraph';
import MLAnalyticsPanel from '../components/MLAnalyticsPanel';
import LiveEnsemblePanel from '../components/LiveEnsemblePanel';
import { getAttackerConsoleUrl, getBackendHttpBase, getBackendWsBase } from '../utils/runtime';

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
    const [latestEvent, setLatestEvent] = useState(null);
    const [ensembleData, setEnsembleData] = useState(null);
    const [aiNarration, setAiNarration] = useState('');
    const [shareInfo, setShareInfo] = useState({
        attacker_console_url: getAttackerConsoleUrl(),
        dashboard_url: window.location.href,
        lan_ip: window.location.hostname || 'localhost',
        ssh_command: `ssh root@${window.location.hostname || 'localhost'} -p 2222`,
        raw_port_command: `nc ${window.location.hostname || 'localhost'} 8888`,
    });
    const wsRef = useRef(null);
    const termRef = useRef(null);

    const startLiveMonitor = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.onclose = null;
            wsRef.current.close();
            wsRef.current = null;
        }

        setLiveActive(true);
        setDemoActive(false);
        setIsolated(false);
        setReportData(null);
        setPrediction(null);
        setCommands([]);
        setLatestEvent(null);
        setDeceptionPhase('Awaiting connection from remote attacker console...');
        setActiveNodes(['entry']);

        const ws = new WebSocket(`${getBackendWsBase()}/ws/monitor`);
        wsRef.current = ws;

        ws.onopen = () => {
            setDeceptionPhase('Live monitor active. Waiting for operator activity...');
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'init') {
                setAttackerIp(msg.attacker_ip);
                termRef.current?.writeln(`\n\x1b[1;36m${'-'.repeat(60)}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;36m  ${msg.message}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;36m${'-'.repeat(60)}\x1b[0m\n`);
                setDeceptionPhase('Live data stream established');
            }

            if (msg.type === 'command') {
                termRef.current?.writeln(`\x1b[1;32m${msg.prompt}\x1b[0m${msg.command}`);
                if (msg.output) {
                    msg.output.split('\n').forEach((line) => termRef.current?.writeln(line));
                }
                termRef.current?.writeln('');

                if (msg.profile) {
                    setProfile(msg.profile);
                }
                if (msg.prediction) {
                    setPrediction(msg.prediction);
                }
                if (msg.command) {
                    setCommands((prev) => [...prev, msg.command]);
                }
                if (msg.command_analysis) {
                    setLatestEvent(msg.command_analysis);
                }

                if (msg.risk_event) {
                    setDeceptionPhase(`High risk command observed: ${msg.command.substring(0, 30)}`);
                }

                if (msg.ensemble_analysis) {
                    setEnsembleData(msg.ensemble_analysis);
                }
                if (msg.ai_narration) {
                    setAiNarration(msg.ai_narration);
                }

                const cmdCount = msg.profile?.commands_executed || 0;
                if (cmdCount >= 1) setActiveNodes((prev) => [...new Set([...prev, 'honeypot'])]);
                if (cmdCount >= 4) setActiveNodes((prev) => [...new Set([...prev, 'fakedb'])]);
                if (cmdCount >= 8) setActiveNodes((prev) => [...new Set([...prev, 'internal'])]);
            }

            if (msg.type === 'isolated') {
                setIsolated(true);
                if (msg.report) {
                    setReportData(msg.report);
                }
                termRef.current?.writeln(`\n\x1b[1;31m${'='.repeat(50)}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m  ${msg.message}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m${'='.repeat(50)}\x1b[0m\n`);
                setLiveActive(false);
                setDeceptionPhase('Connection closed');
            }
        };

        ws.onerror = () => {
            setDeceptionPhase('Connection error');
        };

        ws.onclose = () => {
            setLiveActive(false);
            if (wsRef.current) {
                setDeceptionPhase('Monitor disconnected. Reconnecting...');
                setTimeout(() => {
                    if (wsRef.current === ws) { // Ensure we don't start multiple if one is already starting
                        startLiveMonitor();
                    }
                }, 5000);
            }
        };
    }, []);

    const startDemo = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.onclose = null;
            wsRef.current.close();
            wsRef.current = null;
        }

        setDemoActive(true);
        setLiveActive(false);
        setIsolated(false);
        setReportData(null);
        setPrediction(null);
        setCommands([]);
        setLatestEvent(null);
        setDeceptionPhase('');
        setActiveNodes(['entry']);

        const ws = new WebSocket(`${getBackendWsBase()}/ws/demo`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);

            if (msg.type === 'init') {
                setAttackerIp(msg.attacker_ip);
                termRef.current?.writeln(`\x1b[1;31mSTATUS: ${msg.message}\x1b[0m\n`);
            }

            if (msg.type === 'command') {
                termRef.current?.writeln(`\x1b[1;32m${msg.prompt}\x1b[0m${msg.command}`);
                if (msg.output) {
                    msg.output.split('\n').forEach((line) => termRef.current?.writeln(line));
                }
                termRef.current?.writeln('');

                if (msg.profile) {
                    setProfile(msg.profile);
                }
                if (msg.prediction) {
                    setPrediction(msg.prediction);
                }
                if (msg.command) {
                    setCommands((prev) => [...prev, msg.command]);
                }
                if (msg.command_analysis) {
                    setLatestEvent(msg.command_analysis);
                }

                const cmdCount = msg.profile?.commands_executed || 0;
                if (cmdCount >= 3) setActiveNodes((prev) => [...new Set([...prev, 'honeypot'])]);
                if (cmdCount >= 6) setActiveNodes((prev) => [...new Set([...prev, 'fakedb'])]);
                if (cmdCount >= 10) setActiveNodes((prev) => [...new Set([...prev, 'internal'])]);
            }

            if (msg.type === 'deception') {
                setDeceptionPhase(msg.message);
            }

            if (msg.ensemble_analysis) {
                setEnsembleData(msg.ensemble_analysis);
            }
            if (msg.ai_narration) {
                setAiNarration(msg.ai_narration);
            }

            if (msg.type === 'dave') {
                msg.message.split('\n').forEach((line) => {
                    termRef.current?.writeln(`\x1b[1;33m${line}\x1b[0m`);
                });
                if (msg.profile) {
                    setProfile(msg.profile);
                }
            }

            if (msg.type === 'isolated') {
                setIsolated(true);
                if (msg.report) {
                    setReportData(msg.report);
                }
                termRef.current?.writeln(`\n\x1b[1;31m${'='.repeat(50)}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m  ${msg.message}\x1b[0m`);
                termRef.current?.writeln(`\x1b[1;31m${'='.repeat(50)}\x1b[0m\n`);
                if (msg.profile) {
                    setProfile(msg.profile);
                }
                setDemoActive(false);
            }
        };

        ws.onerror = () => {
            termRef.current?.writeln('\x1b[1;31m[CONNECTION ERROR] Could not reach the backend on port 8000.\x1b[0m');
            setDemoActive(false);
        };

        ws.onclose = () => {
            setDemoActive(false);
        };
    }, []);

    useEffect(() => {
        startLiveMonitor();

        return () => {
            if (wsRef.current) {
                wsRef.current.onclose = null;
                wsRef.current.close();
            }
        };
    }, [startLiveMonitor]);

    useEffect(() => {
        const fetchShareInfo = async () => {
            try {
                const response = await fetch(`${getBackendHttpBase()}/api/runtime/network`);
                if (!response.ok) {
                    return;
                }
                const data = await response.json();
                
                // If we are on Vercel/Production, we want to share the current URL
                // If on Localhost, we want the LAN IP URL from the backend
                const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
                
                setShareInfo({
                    attacker_console_url: isLocal ? (data.attacker_console_url || getAttackerConsoleUrl()) : getAttackerConsoleUrl(),
                    dashboard_url: isLocal ? (data.dashboard_url || window.location.href) : window.location.href,
                    lan_ip: data.lan_ip || window.location.hostname || 'localhost',
                    ssh_command: data.ssh_command || `ssh root@${data.lan_ip} -p 2222`,
                    raw_port_command: data.raw_port_command || `nc ${data.lan_ip} 8080`,
                });
            } catch (error) {
                console.error('Runtime network fetch failed:', error);
            }
        };

        fetchShareInfo();
    }, []);

    return (
        <div className="container-responsive py-4 sm:py-6">
            <MatrixRain />

            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                    <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${demoActive ? 'bg-neon-red animate-pulse' : isolated ? 'bg-neon-green' : 'bg-gray-600'}`} />
                        <h1 className="font-[Orbitron] text-xl sm:text-2xl font-bold text-white text-glow-blue relative">
                            EXTERNAL THREAT
                            <CyberCorner position="top-right" className="text-neon-blue -top-2 -right-6 !w-4 !h-4" />
                        </h1>
                    </div>
                    {attackerIp && (
                        <span className="font-mono text-xs sm:text-sm text-neon-red sm:ml-4 bg-neon-red/10 px-2 py-1 rounded border border-neon-red/20">
                            <Wifi className="w-4 h-4 inline mr-1" />
                            Attacker: {attackerIp}
                        </span>
                    )}
                </div>

                <div className="flex flex-col sm:flex-row items-center gap-3 w-full lg:w-auto">
                    <div className="w-full sm:w-auto">
                        <HydraMode mode={hydraMode} onModeChange={setHydraMode} />
                    </div>

                    <button
                        className={`btn-neon ${liveActive ? 'btn-neon-blue active' : 'btn-neon-blue'} flex items-center justify-center gap-2 w-full sm:w-auto text-xs`}
                        onClick={startLiveMonitor}
                        disabled={liveActive}
                    >
                        <Radio className={`w-4 h-4 ${liveActive ? 'animate-pulse' : ''}`} />
                        {liveActive ? 'Monitor Connected' : 'Connect Monitor'}
                    </button>

                    <button
                        className={`btn-neon ${demoActive ? 'btn-neon-red' : 'btn-neon-green'} flex items-center justify-center gap-2 w-full sm:w-auto text-xs`}
                        onClick={startDemo}
                        disabled={demoActive}
                    >
                        {demoActive ? (
                            <><Radio className="w-4 h-4 animate-pulse" /> Simulating...</>
                        ) : (
                            <><Zap className="w-4 h-4" /> Start Demo</>
                        )}
                    </button>
                </div>
            </div>

            <div className="glass-card p-4 mb-4 relative overflow-hidden">
                {shareInfo.lan_ip === 'localhost' || shareInfo.lan_ip === '127.0.0.1' ? (
                    <div className="absolute inset-0 bg-neon-red/10 backdrop-blur-[2px] z-10 flex items-center justify-center p-6 text-center border border-neon-red/30 rounded-xl animate-pulse">
                        <div className="max-w-md">
                            <div className="flex justify-center mb-2"><Radio className="w-8 h-8 text-neon-red" /></div>
                            <h3 className="font-[Orbitron] text-white text-lg font-bold">LOCAL-ONLY MODE DETECTED</h3>
                            <p className="text-xs text-gray-300 mt-2">
                                You are currently on <span className="text-neon-red font-mono">localhost</span>. 
                                Your friend&apos;s laptop CANNOT connect via this link. 
                                <br/><br/>
                                Please open this dashboard using your **LAN IP** instead (e.g., <span className="text-neon-blue">http://192.168.x.x:5173</span>).
                            </p>
                        </div>
                    </div>
                ) : null}

                <div className="font-[Orbitron] text-sm text-neon-cyan tracking-wider mb-4 flex items-center gap-2">
                    <Wifi className="w-4 h-4" /> EXTERNAL CONNECTION GATEWAY (TWO-LAPTOP DEMO)
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Option 1: Web Console */}
                    <div className="p-3 border border-neon-blue/20 bg-neon-blue/5 rounded-lg flex flex-col justify-between">
                        <div>
                            <div className="text-xs font-bold text-neon-blue mb-1 uppercase tracking-tighter">Option 1: Web Attacker Console</div>
                            <div className="text-[10px] text-gray-400 mb-2 leading-tight">Safe, interactive browser terminal for your friend to use.</div>
                            <div className="font-mono text-[10px] text-white break-all bg-black/40 p-2 rounded border border-white/10 mb-3">
                                {shareInfo.attacker_console_url}
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={() => navigator.clipboard?.writeText(shareInfo.attacker_console_url)}
                            className="btn-neon btn-neon-blue !py-1 !px-2 !text-[10px] flex items-center justify-center gap-2 w-full"
                        >
                            <Copy className="w-3 h-3" /> Copy URL
                        </button>
                    </div>

                    {/* Option 2: SSH Tunnel */}
                    <div className="p-3 border border-neon-green/20 bg-neon-green/5 rounded-lg flex flex-col justify-between">
                        <div>
                            <div className="text-xs font-bold text-neon-green mb-1 uppercase tracking-tighter">Option 2: Native SSH Console</div>
                            <div className="text-[10px] text-gray-400 mb-2 leading-tight">Friend connects via their real terminal: <code className="text-white">ssh root@...</code></div>
                            <div className="font-mono text-[10px] text-white break-all bg-black/40 p-2 rounded border border-white/10 mb-3">
                                {shareInfo.ssh_command}
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={() => navigator.clipboard?.writeText(shareInfo.ssh_command)}
                            className="btn-neon btn-neon-green !py-1 !px-2 !text-[10px] flex items-center justify-center gap-2 w-full"
                        >
                            <Copy className="w-3 h-3" /> Copy SSH Cmd
                        </button>
                    </div>

                    {/* Option 3: Raw Port Ping */}
                    <div className="p-3 border border-neon-purple/20 bg-neon-purple/5 rounded-lg flex flex-col justify-between">
                        <div>
                            <div className="text-xs font-bold text-neon-purple mb-1 uppercase tracking-tighter">Option 3: Raw Netcat Ping</div>
                            <div className="text-[10px] text-gray-400 mb-2 leading-tight">Lightweight raw TCP connection via netcat or telnet.</div>
                            <div className="font-mono text-[10px] text-white break-all bg-black/40 p-2 rounded border border-white/10 mb-3">
                                {shareInfo.raw_port_command}
                            </div>
                        </div>
                        <button
                            type="button"
                            onClick={() => navigator.clipboard?.writeText(shareInfo.raw_port_command)}
                            className="btn-neon btn-neon-purple !py-1 !px-2 !text-[10px] flex items-center justify-center gap-2 w-full"
                        >
                            <Copy className="w-3 h-3" /> Copy NC Cmd
                        </button>
                    </div>
                </div>
            </div>

            <div className="mb-4 animate-slide-up">
                <ThreatIntelligenceGraph profile={profile} commands={commands} />
            </div>

            <div className="grid grid-cols-12 gap-4">
                <div className="col-span-12 lg:col-span-7">
                    <AttackerTerminal ref={termRef} mode={hydraMode} />
                </div>

                <div className="col-span-12 lg:col-span-5 space-y-4">
                    <div className="relative">
                        <CyberCorner position="top-right" className="text-neon-green" />
                        <HackerProfile profile={profile} />
                    </div>
                    <CommandTelemetry event={latestEvent} active={demoActive || liveActive} />
                    <ThreatPrediction prediction={prediction} active={demoActive || liveActive} />
                    <LiveEnsemblePanel ensembleData={ensembleData} aiNarration={aiNarration} active={demoActive || liveActive} />
                    <MLAnalyticsPanel profile={profile} commands={commands} active={demoActive || liveActive} />
                    <DeceptionStatus phase={deceptionPhase} active={demoActive || liveActive} />
                    <div className="relative">
                        <CyberCorner position="bottom-left" className="text-neon-purple" />
                        <SystemCapture isolated={isolated} profile={profile} />
                    </div>
                </div>

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
