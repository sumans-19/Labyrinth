import React, { useState, useEffect, useRef } from 'react';
import { Box, Terminal, Activity, ShieldAlert, CheckCircle, Shield, XCircle, Code, Loader } from 'lucide-react';
import CyberCorner from '../components/CyberCorner';

export default function SentinelSandbox() {
  const [sourceUrl, setSourceUrl] = useState('');
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('IDLE');
  const [report, setReport] = useState(null);
  const [ws, setWs] = useState(null);
  const logsEndRef = useRef(null);

  // Auto-scroll to bottom of logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const connectAndDetonate = () => {
    if (!sourceUrl) return;

    // Reset state
    setLogs([]);
    setReport(null);
    setStatus('INITIALIZING');

    // Make sure we connect via correct protocol (ws vs wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use window.location.hostname for robustness, defaulting to port 8000
    const host = window.location.hostname || 'localhost';
    const wsUrl = `${protocol}//${host}:8000/ws/sentinel`;
    
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setStatus('CONNECTED');
      // Send the payload
      socket.send(JSON.stringify({
        type: 'url',
        data: sourceUrl
      }));
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'status') {
        setLogs(prev => [...prev, { type: 'system', text: `[SYSTEM] ${msg.message}` }]);
      } else if (msg.type === 'log') {
        setLogs(prev => [...prev, { type: 'stdout', text: msg.data }]);
      } else if (msg.type === 'error') {
        setLogs(prev => [...prev, { type: 'error', text: `[ERROR] ${msg.message}` }]);
        setStatus('FAILED');
      } else if (msg.type === 'report') {
        setReport({
          status: msg.status,
          risk_score: msg.risk_score,
          findings: msg.findings
        });
        setStatus('COMPLETED');
      }
    };

    socket.onclose = () => {
      if (status !== 'COMPLETED' && status !== 'FAILED') {
        setStatus('DISCONNECTED');
      }
      setWs(null);
    };

    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setLogs(prev => [...prev, { type: 'error', text: '[NETWORK ERROR] Failed to connect to Sandbox Backend.' }]);
      setStatus('FAILED');
    };

    setWs(socket);
  };

  const handleDetonate = (e) => {
    e.preventDefault();
    connectAndDetonate();
  };

  const isExecuting = status === 'INITIALIZING' || status === 'CONNECTED';

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-neon-blue/10 rounded-lg border border-neon-blue/30 relative overflow-hidden group">
          <div className="absolute inset-0 bg-neon-blue/20 blur-xl group-hover:bg-neon-blue/40 transition-colors" />
          <Box className="w-8 h-8 text-neon-blue relative z-10" />
        </div>
        <div>
          <h1 className="font-[Orbitron] text-3xl font-bold text-white text-glow-blue tracking-wider flex items-center gap-3">
            ZERO-TOUCH SENTINEL SANDBOX
          </h1>
          <p className="text-neon-blue/70 font-mono text-sm mt-1">
            AUTONOMOUS DETONATION & BEHAVIORAL ANALYSIS ENGINE
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Input and Report */}
        <div className="space-y-6">
          {/* Input Panel */}
          <div className="glass-card p-6 relative group">
            <CyberCorner position="top-right" className="text-neon-blue opacity-50" />
            <CyberCorner position="bottom-left" className="text-neon-purple opacity-50" />
            
            <h2 className="font-[Orbitron] text-lg text-neon-blue mb-4 flex items-center gap-2">
              <Code className="w-5 h-5" />
              Target Acquisition
            </h2>
            
            <form onSubmit={handleDetonate} className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-gray-400 mb-2">GIT REPOSITORY URL</label>
                <div className="relative">
                  <input
                    type="url"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    placeholder="https://github.com/user/untrusted-repo.git"
                    className="w-full bg-black/50 border border-neon-blue/30 rounded px-4 py-2 font-mono text-sm text-neon-blue focus:outline-none focus:border-neon-blue focus:shadow-[0_0_10px_rgba(59,130,246,0.3)] transition-all"
                    required
                    disabled={isExecuting}
                  />
                  <div className="absolute right-0 top-0 bottom-0 w-1 bg-neon-blue/30" />
                </div>
              </div>
              
              <button
                type="submit"
                disabled={isExecuting || !sourceUrl}
                className="w-full relative overflow-hidden group py-3 rounded border border-neon-purple/50 bg-neon-purple/10 text-white font-[Orbitron] tracking-widest hover:bg-neon-purple/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-neon-purple/0 via-neon-purple/30 to-neon-purple/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                <div className="flex items-center justify-center gap-2 relative z-10">
                  {isExecuting ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin text-neon-purple" />
                      DETONATING...
                    </>
                  ) : (
                    <>
                      <Activity className="w-5 h-5 text-neon-purple" />
                      INITIATE DETONATION
                    </>
                  )}
                </div>
              </button>
            </form>
          </div>

          {/* Report Card */}
          {report && (
            <div className="glass-card p-6 relative animate-fade-in" style={{ animationDelay: '200ms' }}>
              <CyberCorner position="top-left" className="text-neon-blue opacity-50" />
              
              <h2 className="font-[Orbitron] text-lg mb-6 flex items-center gap-2 text-white">
                <Shield className="w-5 h-5 text-neon-blue" />
                Behavioral Report
              </h2>
              
              <div className="space-y-6">
                {/* Status Badge */}
                <div className={`p-4 rounded border flex items-center justify-between ${
                  report.status === 'CLEAN' 
                    ? 'bg-green-500/10 border-green-500/30 text-green-400' 
                    : report.status === 'SUSPICIOUS'
                      ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                      : 'bg-red-500/10 border-red-500/30 text-red-400'
                }`}>
                  <div className="flex items-center gap-3">
                    {report.status === 'CLEAN' ? <CheckCircle className="w-6 h-6" /> : 
                     report.status === 'SUSPICIOUS' ? <ShieldAlert className="w-6 h-6" /> : 
                     <XCircle className="w-6 h-6" />}
                    <div>
                      <div className="text-xs font-mono opacity-80 uppercase tracking-widest">Verdict</div>
                      <div className="font-[Orbitron] font-bold text-xl">{report.status}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-mono opacity-80 uppercase tracking-widest">Risk Score</div>
                    <div className="font-[Orbitron] font-bold text-xl">{report.risk_score} / 100</div>
                  </div>
                </div>

                {/* Findings */}
                {report.findings.length > 0 && (
                  <div>
                    <h3 className="font-mono text-xs text-gray-400 mb-3 uppercase tracking-wider">High-Risk Patterns Detected</h3>
                    <ul className="space-y-2">
                      {report.findings.map((finding, idx) => (
                        <li key={idx} className="flex items-start gap-2 bg-black/40 p-3 rounded border border-red-500/20">
                          <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <span className="font-mono text-sm text-red-200">{finding}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {report.findings.length === 0 && (
                  <div className="bg-black/40 p-4 rounded border border-green-500/20 text-center">
                    <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2 opacity-50" />
                    <p className="font-mono text-sm text-green-400">No high-risk behaviors detected during execution window.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Terminal */}
        <div className="lg:col-span-2 glass-card p-1 relative flex flex-col h-[600px]">
          <CyberCorner position="top-left" className="text-neon-blue opacity-50" />
          <CyberCorner position="bottom-right" className="text-neon-purple opacity-50" />
          
          <div className="bg-black/80 px-4 py-3 border-b border-neon-blue/20 flex items-center justify-between">
            <div className="flex items-center gap-2 text-neon-blue font-[Orbitron] text-sm">
              <Terminal className="w-4 h-4" />
              LIVE EXECUTION FEED
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isExecuting ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} />
              <span className="font-mono text-xs text-gray-400">{status}</span>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 bg-[#0a0a0f] font-mono text-sm">
            {logs.length === 0 && status === 'IDLE' && (
              <div className="text-gray-500 text-center h-full flex flex-col items-center justify-center">
                <Terminal className="w-12 h-12 opacity-20 mb-4" />
                <p>Awaiting detonation payload.</p>
                <p className="text-xs mt-2 opacity-50">Provide a repository URL to begin isolated execution.</p>
              </div>
            )}
            
            {logs.map((log, idx) => (
              <div key={idx} className={`mb-1 break-words ${
                log.type === 'system' ? 'text-neon-purple font-bold' : 
                log.type === 'error' ? 'text-red-500' : 
                'text-gray-300'
              }`}>
                {log.text}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
