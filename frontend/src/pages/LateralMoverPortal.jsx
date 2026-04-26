import React, { useState, useEffect } from 'react';
import { 
    Users, Shield, Database, Cloud, Lock, Terminal, 
    AlertTriangle, Server, Key, ArrowLeft, ArrowRight,
    Activity, Globe, Search, RefreshCw
} from 'lucide-react';

const ROLES = [
    {
        id: 'cloud-dev',
        name: 'Cloud Developer',
        icon: Cloud,
        description: 'Infrastructure management and deployment pipelines.',
        authorized_tools: [
            { name: 'CI/CD Pipelines', endpoint: '/internal/pipelines', status: 'ACTIVE' },
            { name: 'Log Explorer', endpoint: '/internal/logs', status: 'STABLE' }
        ],
        honeytokens: [
            { name: 'S3 Production Backup', endpoint: '/api/v1/internal/s3-mock', type: 'AWS_ACCESS_KEY_ID', auth_header: 'X-API-Key' }
        ]
    },
    {
        id: 'db-admin',
        name: 'Database Administrator',
        icon: Database,
        description: 'Maintaining production clusters and query optimization.',
        authorized_tools: [
            { name: 'Query Optimizer', endpoint: '/internal/queries', status: 'IDLE' },
            { name: 'User Management', endpoint: '/internal/iam', status: 'LOCKED' }
        ],
        honeytokens: [
            { name: 'Database Sync Service', endpoint: '/api/v1/internal/db-sync', type: 'MONGODB_URI', auth_header: 'Authorization' }
        ]
    },
    {
        id: 'sec-auditor',
        name: 'Security Auditor',
        icon: Shield,
        description: 'Compliance verification and vulnerability assessments.',
        authorized_tools: [
            { name: 'Audit Logs', endpoint: '/internal/audits', status: 'VIEW-ONLY' },
            { name: 'Policy Review', endpoint: '/internal/policies', status: 'IDLE' }
        ],
        honeytokens: [
            { name: 'HashiCorp Vault Secrets', endpoint: '/api/v1/internal/vault/secrets', type: 'INTERNAL_API_TOKEN', auth_header: 'token' }
        ]
    }
];

export default function LateralMoverPortal({ onNavigate }) {
    const [selectedRole, setSelectedRole] = useState(null);
    const [alert, setAlert] = useState(null);
    const [isTriggering, setIsTriggering] = useState(false);
    const [honeytokens, setHoneytokens] = useState({});

    // Fetch live honeytokens from the registry (simulation)
    // In a real exfiltration, the attacker would have found these in .env files
    useEffect(() => {
        const fetchRegistry = async () => {
            try {
                // Since we can't easily read a random JSON file via fetch without a route,
                // we'll simulate the "discovered" tokens for the demo.
                // In a production setup, we'd have a specific endpoint for the 'attacker simulation'
            } catch (err) {}
        };
        fetchRegistry();
    }, []);

    const handleTriggerHoneytoken = async (token) => {
        setIsTriggering(true);
        setAlert(null);

        try {
            const registryRes = await fetch(`http://${window.location.hostname}:8000/api/decoys/honeytokens`);
            const registryData = await registryRes.json();
            
            const targetTokenEntry = Object.entries(registryData).find(([hash, info]) => info.type === token.type);
            
            if (!targetTokenEntry || !targetTokenEntry[1].raw_value) {
                setAlert({ type: 'error', message: `Token value for ${token.type} not found. Run generator first!` });
                setIsTriggering(false);
                return;
            }

            const tokenValue = targetTokenEntry[1].raw_value;
            setAlert({ type: 'info', message: 'Simulating unauthorized access attempt...' });
            
            // Perform the unauthorized request
            const fetchOptions = {
                method: token.auth_header === 'X-API-Key' ? 'POST' : 'GET',
                headers: {}
            };

            const url = `http://${window.location.hostname}:8000${token.endpoint}`;

            if (token.auth_header === 'Authorization') {
                fetchOptions.headers['Authorization'] = `Bearer ${tokenValue}`;
            } else if (token.auth_header === 'X-API-Key') {
                fetchOptions.headers['X-API-Key'] = tokenValue;
            } else if (token.auth_header === 'token') {
                // For vault, it's a query param
                const vaultUrl = new URL(url);
                vaultUrl.searchParams.append('token', tokenValue);
                // use new URL
                const response = await fetch(vaultUrl.toString(), fetchOptions);
                const data = await response.json();
                setAlert({ type: 'success', message: 'Access Denied (403). Check Dashboard!' });
                return;
            }

            const response = await fetch(url, fetchOptions);
            const data = await response.json();
            
            if (response.status === 403 || response.status === 401) {
                setAlert({ type: 'success', message: 'Access Denied (403). Check Dashboard!' });
            } else {
                setAlert({ type: 'error', message: 'Request succeeded unexpectedly. Check backend interceptor.' });
            }
        } catch (err) {
            console.error(err);
            setAlert({ type: 'error', message: 'Simulation failed. Ensure backend is running.' });
        } finally {
            setIsTriggering(false);
        }
    };

    const [consoleHistory, setConsoleHistory] = useState([]);
    const [commandInput, setCommandInput] = useState('');
    const consoleEndRef = React.useRef(null);

    const ROLE_FILES = {
        'cloud-dev': ['main.tf', 'deploy.sh', 'prod_backup_keys.env', 'config.json'],
        'db-admin': ['schema.sql', 'db_sync_creds.env', 'maintenance.log'],
        'sec-auditor': ['audit_report.pdf', 'internal_api_tokens.env', 'vault_access.log']
    };

    useEffect(() => {
        if (selectedRole) {
            setConsoleHistory([
                { type: 'input', text: `login --as ${selectedRole.id.replace('-', '_')}` },
                { type: 'info', text: '[*] Authenticating session token...' },
                { type: 'info', text: `[*] Loading local environment for ${selectedRole.name}` },
                { type: 'info', text: '[*] 4 local honeytokens detected in shadow storage.' },
                { type: 'success', text: '[+] Shell Ready. Type "help" for commands.' }
            ]);
        }
    }, [selectedRole]);

    useEffect(() => {
        consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [consoleHistory]);

    const handleCommand = async (e) => {
        e.preventDefault();
        const cmd = commandInput.trim().toLowerCase();
        if (!cmd) return;

        const newHistory = [...consoleHistory, { type: 'input', text: cmd }];
        const args = cmd.split(' ');
        const baseCmd = args[0];

        if (baseCmd === 'help') {
            newHistory.push({ type: 'info', text: 'Available commands: ls, cat <file>, clear, help, whoami' });
        } else if (baseCmd === 'clear') {
            setConsoleHistory([]);
            setCommandInput('');
            return;
        } else if (baseCmd === 'whoami') {
            newHistory.push({ type: 'info', text: `${selectedRole.id}@internal-server-01` });
        } else if (baseCmd === 'ls') {
            const files = ROLE_FILES[selectedRole.id] || [];
            newHistory.push({ type: 'info', text: files.join('    ') });
        } else if (baseCmd === 'cat') {
            const fileName = args[1];
            const files = ROLE_FILES[selectedRole.id] || [];
            
            if (!fileName) {
                newHistory.push({ type: 'error', text: 'usage: cat <file_name>' });
            } else if (!files.includes(fileName)) {
                newHistory.push({ type: 'error', text: `cat: ${fileName}: No such file or directory` });
            } else {
                // Logic for opening a file
                if (fileName.endsWith('.env') || fileName === 'config.json' || fileName.includes('creds') || fileName.includes('keys')) {
                    newHistory.push({ type: 'warning', text: `[!] ALERT: Opening sensitive system file: ${fileName}` });
                    newHistory.push({ type: 'info', text: '[*] Extracting credentials for automated pivot...' });
                    
                    // Trigger the honeytoken!
                    const tokenToTrigger = selectedRole.honeytokens[0]; // Simplified for demo
                    await handleTriggerHoneytoken(tokenToTrigger);
                    
                    newHistory.push({ type: 'success', text: '[+] Honeytoken Triggered! Check your main dashboard.' });
                } else {
                    newHistory.push({ type: 'info', text: `--- Content of ${fileName} ---` });
                    newHistory.push({ type: 'info', text: `[Simulation] Source code for ${fileName} loaded.` });
                }
            }
        } else {
            newHistory.push({ type: 'error', text: `command not found: ${baseCmd}` });
        }

        setConsoleHistory(newHistory);
        setCommandInput('');
    };

    if (!selectedRole) {
        return (
            <div className="max-w-[1200px] mx-auto px-6 py-20 flex flex-col items-center">
                <button 
                    onClick={() => onNavigate('internalthreat')}
                    className="self-start flex items-center gap-2 text-gray-500 hover:text-white transition-colors mb-12 font-mono text-xs uppercase"
                >
                    <ArrowLeft className="w-4 h-4" /> Back to Monitor
                </button>

                <div className="text-center mb-16">
                    <h1 className="font-[Orbitron] text-4xl font-black text-white tracking-[0.2em] uppercase mb-4 text-glow-blue">
                        Lateral Movement Portal
                    </h1>
                    <p className="text-gray-500 font-mono text-sm uppercase tracking-widest max-w-2xl mx-auto">
                        Simulate an internal adversary attempting to pivot through the network. 
                        Select a role to begin the exfiltration simulation.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full">
                    {ROLES.map((role) => (
                        <div 
                            key={role.id}
                            onClick={() => setSelectedRole(role)}
                            className="glass-card p-8 border border-white/10 bg-white/5 hover:bg-neon-blue/5 hover:border-neon-blue/50 transition-all duration-500 group cursor-pointer flex flex-col items-center text-center relative overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-opacity">
                                <role.icon className="w-24 h-24" />
                            </div>
                            
                            <div className="p-4 rounded-2xl bg-black/40 border border-white/5 mb-6 group-hover:scale-110 transition-transform">
                                <role.icon className="w-10 h-10 text-neon-blue" />
                            </div>

                            <h3 className="font-[Orbitron] text-xl font-bold text-white mb-3 tracking-wider">{role.name}</h3>
                            <p className="text-gray-400 text-xs leading-relaxed font-sans">{role.description}</p>
                            
                            <div className="mt-8 flex items-center gap-2 text-[10px] font-mono text-neon-blue font-bold opacity-0 group-hover:opacity-100 transition-opacity uppercase">
                                Initialize Workspace <ArrowRight className="w-3 h-3" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-[1400px] mx-auto px-6 py-10 space-y-8 animate-fade-in">
            {/* Workspace Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-8">
                <div className="flex items-center gap-6">
                    <button 
                        onClick={() => setSelectedRole(null)}
                        className="p-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-gray-400" />
                    </button>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <selectedRole.icon className="w-4 h-4 text-neon-blue" />
                            <span className="text-[10px] font-mono text-neon-blue uppercase font-bold tracking-widest">Active Identity</span>
                        </div>
                        <h1 className="font-[Orbitron] text-2xl font-black text-white tracking-widest uppercase">
                            {selectedRole.name} Workspace
                        </h1>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="px-4 py-2 bg-neon-green/10 border border-neon-green/30 rounded-lg flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse" />
                        <span className="text-[10px] font-mono text-neon-green font-bold uppercase tracking-widest">Connection: Secure</span>
                    </div>
                    <div className="px-4 py-2 bg-black/40 border border-white/5 rounded-lg flex items-center gap-3">
                        <Users className="w-4 h-4 text-gray-500" />
                        <span className="text-[10px] font-mono text-gray-300 font-bold uppercase tracking-widest">UID: 44291-ALPHA</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Authorized Section */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Terminal className="w-5 h-5 text-gray-500" />
                        <h2 className="font-[Orbitron] text-sm font-bold text-white uppercase tracking-widest">Authorized Internal Services</h2>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {selectedRole.authorized_tools.map((tool, i) => (
                            <div key={i} className="glass-card p-6 border border-white/5 bg-white/5 hover:border-white/20 transition-all">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="p-2 bg-black/40 rounded border border-white/5">
                                        <Server className="w-5 h-5 text-gray-400" />
                                    </div>
                                    <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-white/5 text-gray-400 border border-white/10 uppercase">
                                        {tool.status}
                                    </span>
                                </div>
                                <h3 className="text-white font-bold mb-1">{tool.name}</h3>
                                <code className="text-[10px] text-neon-blue font-mono">{tool.endpoint}</code>
                                <button className="w-full mt-4 py-2 bg-white/5 border border-white/10 text-[10px] font-mono text-gray-400 hover:text-white hover:bg-white/10 transition-all uppercase">
                                    Launch Interface
                                </button>
                            </div>
                        ))}
                    </div>

                    {/* Simulation Console */}
                    <div className="glass-card bg-black/80 border border-white/10 p-6 font-mono text-[11px] overflow-hidden">
                        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                            <div className="flex items-center gap-2">
                                <div className="flex gap-1">
                                    <div className="w-2 h-2 rounded-full bg-red-500/50" />
                                    <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
                                    <div className="w-2 h-2 rounded-full bg-green-500/50" />
                                </div>
                                <span className="text-gray-500 ml-2 italic">internal_terminal --bash</span>
                            </div>
                            <span className="text-gray-600">v2.4.1-dist</span>
                        </div>
                        <div className="space-y-1.5 h-[220px] overflow-y-auto custom-scrollbar mb-4 pr-2">
                            {consoleHistory.map((line, i) => (
                                <p key={i} className={
                                    line.type === 'input' ? 'text-neon-green' : 
                                    line.type === 'error' ? 'text-neon-red' : 
                                    line.type === 'success' ? 'text-neon-green/80' : 
                                    line.type === 'warning' ? 'text-neon-amber' : 'text-gray-400'
                                }>
                                    {line.type === 'input' && <span className="mr-2">$</span>}
                                    {line.text}
                                </p>
                            ))}
                            <div ref={consoleEndRef} />
                        </div>
                        <form onSubmit={handleCommand} className="flex items-center gap-2 border-t border-white/5 pt-3">
                            <span className="text-neon-green font-bold">$</span>
                            <input 
                                type="text"
                                autoFocus
                                className="bg-transparent border-none outline-none text-white w-full"
                                value={commandInput}
                                onChange={(e) => setCommandInput(e.target.value)}
                                placeholder="Type commands here..."
                            />
                        </form>
                    </div>
                </div>

                {/* Unauthorized/Trap Section */}
                <div className="space-y-6">
                    <div className="flex items-center gap-2 mb-4">
                        <AlertTriangle className="w-5 h-5 text-neon-amber" />
                        <h2 className="font-[Orbitron] text-sm font-bold text-neon-amber uppercase tracking-widest">Restricted Assets (Decoys)</h2>
                    </div>

                    {selectedRole.honeytokens.map((token, i) => (
                        <div key={i} className="glass-card p-6 border border-neon-red/20 bg-neon-red/5 hover:bg-neon-red/10 transition-all relative group">
                            <div className="absolute top-0 right-0 p-4">
                                <Lock className="w-6 h-6 text-neon-red opacity-20" />
                            </div>
                            
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-neon-red/10 rounded border border-neon-red/30">
                                    <Key className="w-5 h-5 text-neon-red" />
                                </div>
                                <div>
                                    <h3 className="text-white font-bold text-sm">{token.name}</h3>
                                    <p className="text-[10px] text-gray-500 font-mono uppercase tracking-tighter">Requires {token.type}</p>
                                </div>
                            </div>

                            <p className="text-[11px] text-gray-400 mb-6 leading-relaxed">
                                Accessing this asset requires high-level privileges. Using discovered shadow credentials from the local .env might grant access.
                            </p>

                            <button 
                                onClick={() => handleTriggerHoneytoken(token)}
                                disabled={isTriggering}
                                className="w-full py-3 bg-neon-red/20 border border-neon-red/40 text-neon-red text-xs font-bold font-[Orbitron] tracking-widest hover:bg-neon-red hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed uppercase"
                            >
                                {isTriggering ? 'Attempting Breach...' : 'Trigger Unauthorized Access'}
                            </button>

                            {alert && alert.type === 'error' && (
                                <p className="mt-3 text-[10px] text-neon-red font-mono animate-pulse">{alert.message}</p>
                            )}
                        </div>
                    ))}

                    <div className="p-4 bg-neon-amber/5 border border-neon-amber/20 rounded-xl">
                        <h4 className="text-[10px] font-bold text-neon-amber uppercase mb-2 flex items-center gap-2">
                            <Shield className="w-3 h-3" /> Educational Note
                        </h4>
                        <p className="text-[10px] text-gray-400 leading-relaxed font-sans">
                            In a real scenario, the attacker doesn't click a button. They run a script that automatically uses these credentials. Clicking "Trigger" simulates that script execution.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
