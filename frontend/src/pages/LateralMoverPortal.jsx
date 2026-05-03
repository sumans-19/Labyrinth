import React, { useState, useEffect } from 'react';
import { 
    Users, Shield, Database, Cloud, Lock, Terminal, 
    AlertTriangle, Server, Key, ArrowLeft, ArrowRight,
    Activity, Globe, Search, RefreshCw, Folder, FileText
} from 'lucide-react';
import { getBackendHttpBase } from '../utils/runtime';


const ROLES = [
    {
        id: 'cloud-dev',
        name: 'Cloud Developer',
        userName: 'Alex Mercer',
        uid: '44291-ALPHA',
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
        userName: 'Sam Rivera',
        uid: '44292-BETA',
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
        userName: 'Jordan Lee',
        uid: '44293-GAMMA',
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
    const [toastAlert, setToastAlert] = useState(null);

    // Auto-hide toast after 3 seconds
    useEffect(() => {
        if (toastAlert) {
            const timer = setTimeout(() => setToastAlert(null), 3000);
            return () => clearTimeout(timer);
        }
    }, [toastAlert]);
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
            const registryRes = await fetch(`${getBackendHttpBase()}/api/decoys/honeytokens`);
            
            if (!registryRes.ok) {
                if (registryRes.status === 403) {
                    setAlert({ type: 'error', message: 'BLOCKED: Your IP has been blacklisted by the Threat Engine.' });
                } else {
                    setAlert({ type: 'error', message: `Failed to fetch tokens (${registryRes.status}).` });
                }
                setIsTriggering(false);
                return;
            }
            
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

            const url = `${getBackendHttpBase()}${token.endpoint}`;

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
        'cloud-dev': ['main.tf', 'deploy.sh', 'prod_backup_keys.env', 'config.json', 'readme.md', 'k8s_deployment.yaml'],
        'db-admin': ['schema.sql', 'db_sync_creds.env', 'maintenance.log', 'backup_schedule.txt', 'query_optimization.sql'],
        'sec-auditor': ['audit_report.pdf', 'internal_api_tokens.env', 'vault_access.log', 'compliance_guidelines.txt', 'incident_response.md']
    };

    const FILE_CONTENTS = {
        'main.tf': `provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "production-vpc" }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
}

resource "aws_s3_bucket" "prod_backup" {
  bucket = "prod-db-backups-2026"
  acl    = "private"
}

resource "aws_eks_cluster" "prod_cluster" {
  name     = "primary-production-cluster"
  role_arn = aws_iam_role.eks_master.arn
  vpc_config {
    subnet_ids = [aws_subnet.public_subnet.id]
  }
}`,
        'deploy.sh': `#!/bin/bash
set -e

echo "[1/5] Authenticating with AWS ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

echo "[2/5] Building Docker image..."
docker build -t microservice-core:latest .

echo "[3/5] Tagging image for registry..."
docker tag microservice-core:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/microservice-core:v2.4.1

echo "[4/5] Pushing to repository..."
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/microservice-core:v2.4.1

echo "[5/5] Updating Kubernetes deployment..."
kubectl set image deployment/microservice-core core=123456789012.dkr.ecr.us-east-1.amazonaws.com/microservice-core:v2.4.1 --record
kubectl rollout status deployment/microservice-core

echo "Deployment complete! Production is now running v2.4.1"`,
        'config.json': `{
  "environment": "production",
  "debug": false,
  "max_connections": 1000,
  "timeout_ms": 5000,
  "features": {
    "new_billing_engine": true,
    "beta_dashboard": false,
    "legacy_api_fallback": true
  },
  "endpoints": {
    "auth": "https://auth.internal.corp/v1",
    "payment": "https://pay.internal.corp/v2",
    "analytics": "tcp://kafka.analytics.corp:9092"
  },
  "rate_limiting": {
    "enabled": true,
    "requests_per_minute": 600,
    "burst_capacity": 50
  }
}`,
        'readme.md': `# Cloud Dev Workspace
## Infrastructure Control Node

Welcome to the centralized development node for the Labyrinth Forge infrastructure.

### Prerequisites
- Terraform v1.5.0+
- AWS CLI v2 configured with SSO
- kubectl & helm

### Deployment Pipeline
All deployments are handled via GitHub Actions. Do NOT run \`deploy.sh\` manually unless the CI pipeline is down.

### Emergency Procedures
If the production cluster loses quorum:
1. SSH into the bastion host.
2. Check \`/var/log/syslog\` for OOM errors.
3. Manually scale the ASG up by 2 instances.
4. Notify the DB Admin team immediately.`,
        'k8s_deployment.yaml': `apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-gateway
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-gateway
  template:
    metadata:
      labels:
        app: payment-gateway
    spec:
      containers:
      - name: gateway-service
        image: registry.corp.local/payment-gateway:v1.12
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        envFrom:
        - secretRef:
            name: gateway-secrets`,
        'schema.sql': `CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_sessions (
  session_id VARCHAR(128) PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  ip_address INET,
  user_agent TEXT,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE transaction_logs (
  tx_id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',
  status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tx_user_status ON transaction_logs(user_id, status);`,
        'maintenance.log': `[2026-04-28 02:15:00] [INFO] Starting scheduled vacuum analyze on database 'production_db'...
[2026-04-28 02:15:12] [INFO] Vacuuming table 'transaction_logs'...
[2026-04-28 02:15:45] [INFO] Vacuum complete. Reclaimed 1.2GB of dead tuples.
[2026-04-28 02:16:00] [INFO] Rebuilding index 'idx_tx_user_status'...
[2026-04-28 02:18:22] [INFO] Index rebuild successful. Duration: 142 seconds.
[2026-04-28 02:19:00] [INFO] Initiating DB Sync to read-replica-1...
[2026-04-28 02:19:05] [WARN] High replication lag detected (1.5s). Throttling WAL sender.
[2026-04-28 02:22:10] [INFO] Replication caught up. Sync service normal.
[2026-04-28 02:30:00] [INFO] Nightly maintenance complete.`,
        'backup_schedule.txt': `###########################################
# DATABASE BACKUP AND RETENTION SCHEDULE #
###########################################

# Hourly Transaction Log Backups
0 * * * * /opt/scripts/wal_archive.sh >> /var/log/wal_archive.log 2>&1

# Daily Differential Backups (2 AM)
0 2 * * * /opt/scripts/pg_dump_diff.sh --target s3://prod-db-backups-2026/daily

# Weekly Full Backups (Sunday 4 AM)
0 4 * * 0 /opt/scripts/pg_dump_full.sh --target s3://prod-db-backups-2026/weekly

# Retention Policies:
# - WAL logs: kept for 7 days
# - Daily diffs: kept for 30 days
# - Weekly fulls: kept for 1 year (moved to Glacier after 90 days)`,
        'query_optimization.sql': `-- Problem: The user dashboard is loading slowly because of the recent transactions widget.
-- Current Query (Cost: 4500.22, Time: 1.2s):
-- SELECT * FROM transaction_logs WHERE user_id = 'xxx' ORDER BY created_at DESC LIMIT 5;

-- Proposed Optimized Query using CTE and Covering Index
WITH recent_tx AS (
  SELECT tx_id, amount, currency, status, created_at
  FROM transaction_logs
  WHERE user_id = :current_user_id
  AND status = 'COMPLETED'
  ORDER BY created_at DESC
  LIMIT 5
)
SELECT u.username, r.*
FROM recent_tx r
JOIN users u ON u.id = :current_user_id;

-- Action Item: Ensure covering index exists:
-- CREATE INDEX CONCURRENTLY idx_tx_user_recent ON transaction_logs(user_id, created_at DESC) INCLUDE (amount, currency, status);`,
        'audit_report.pdf': `[SYSTEM PARSER: Extracting text from binary PDF stream]
======================================================
LABYRINTH FORGE SECURITY AUDIT - Q2 2026
Prepared by: External Red Team Delta

EXECUTIVE SUMMARY:
The infrastructure presents a hardened exterior, but internal lateral movement controls are severely lacking. If an attacker breaches the perimeter, the "soft center" allows unabated access to critical systems.

FINDINGS:
1. [CRITICAL] Legacy internal APIs do not enforce TLS.
2. [HIGH] Developers are storing plaintext shadow credentials in local .env files.
3. [HIGH] Vault access logs show anomalous activity from the VPN subnet.
4. [MEDIUM] S3 Production Backups lack strict IAM bounding.

RECOMMENDATIONS:
- Immediately implement Zero Trust architectures for internal service-to-service communication.
- Rotate all AWS Access Keys stored in development environments.
- Enforce strict role-based access control (RBAC) on the Vault.
======================================================`,
        'vault_access.log': `[2026-04-28T08:00:12Z] [INFO] Vault unsealed by key share 1 (admin_alpha)
[2026-04-28T08:00:15Z] [INFO] Vault unsealed by key share 3 (admin_gamma)
[2026-04-28T08:00:16Z] [INFO] Core: Vault is unsealed
[2026-04-28T09:12:44Z] [WARN] core: login attempt failed: error="invalid token" client_ip="10.0.0.45"
[2026-04-28T09:12:45Z] [WARN] core: login attempt failed: error="invalid token" client_ip="10.0.0.45"
[2026-04-28T09:12:46Z] [WARN] core: login attempt failed: error="invalid token" client_ip="10.0.0.45"
[2026-04-28T09:13:00Z] [ALERT] core: IP 10.0.0.45 temporarily blocked due to brute force attempt.
[2026-04-28T10:45:12Z] [INFO] core: successful login client_ip="10.0.5.112" policies="[db-admin-policy, default]"
[2026-04-28T10:45:15Z] [INFO] audit: synced 450 events to remote SIEM.`,
        'compliance_guidelines.txt': `INTERNAL COMPLIANCE & SECURITY POLICY
Last Updated: January 2026

1. CREDENTIAL MANAGEMENT
- All long-lived credentials MUST be rotated every 90 days.
- Hardcoding passwords, API keys, or AWS access keys in source code is a terminable offense.
- Use HashiCorp Vault for dynamic secret generation whenever possible.

2. ACCESS CONTROL
- The principle of least privilege (PoLP) applies to all roles.
- Root access to production servers requires dual-authorization and a logged change request.
- Cross-role access (e.g., a Developer accessing Audit logs) will trigger an automated SOC alert.

3. INCIDENT REPORTING
- If you suspect your workstation has been compromised, disconnect from the VPN immediately and contact IT Security.
- Do NOT attempt to investigate the breach yourself.`,
        'incident_response.md': `# Incident Response Playbook: Lateral Movement Detection

If a lateral movement alert is triggered by the Threat Engine, follow these steps:

## Phase 1: Triage
1. Review the \`attack_logs\` table in the SIEM dashboard to identify the compromised IP.
2. Cross-reference the IP with the VPN logs to identify the user identity.

## Phase 2: Containment
1. If the threat score exceeds 70 (HIGH), the Global Monitoring Middleware should have already tarpitted the IP.
2. Manually revoke the user's active session token.
3. Isolate the affected node using the AWS EC2 Security Group \`sg-quarantine\`.

## Phase 3: Eradication
1. Identify how the attacker gained initial access (phishing, vulnerable exposed service).
2. If honeytokens were triggered, rotate the actual production keys associated with that decoy immediately as a precaution.
3. Wipe and re-image the compromised workstation.`
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
            // Show all files in the system to encourage lateral movement
            const allFiles = Object.values(ROLE_FILES).flat();
            const lsLines = allFiles.map(file => ({ type: 'info', text: file }));
            newHistory.push(...lsLines);
        } else if (baseCmd === 'cat') {
            const fileName = args[1];
            const ownFiles = ROLE_FILES[selectedRole.id] || [];
            const allFiles = Object.values(ROLE_FILES).flat();
            
            if (!fileName) {
                newHistory.push({ type: 'error', text: 'usage: cat <file_name>' });
            } else if (!allFiles.includes(fileName)) {
                newHistory.push({ type: 'error', text: `cat: ${fileName}: No such file or directory` });
            } else if (!ownFiles.includes(fileName)) {
                // Cross-role access detected!
                newHistory.push({ type: 'error', text: `cat: ${fileName}: Permission denied` });
                
                // Show popup notification
                setToastAlert({ 
                    title: 'LATERAL MOVEMENT DETECTED', 
                    message: `Cross-role access to ${fileName} blocked and reported.` 
                });
                
                // Trigger backend alert
                fetch(`${getBackendHttpBase()}/api/v1/internal/file-access`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: fileName, role: selectedRole.id })
                }).catch(err => console.error(err));
                
                setAlert({ type: 'success', message: 'Cross-Role Access Detected. Check Monitor Dashboard!' });
            } else {
                // Logic for opening their OWN file
                if (fileName.endsWith('.env') || fileName.includes('creds') || fileName.includes('keys')) {
                    newHistory.push({ type: 'warning', text: `[!] ALERT: Opening sensitive system file: ${fileName}` });
                    newHistory.push({ type: 'info', text: '[*] Extracting credentials for automated pivot...' });
                    
                    // Trigger the honeytoken!
                    const tokenToTrigger = selectedRole.honeytokens[0]; // Simplified for demo
                    await handleTriggerHoneytoken(tokenToTrigger);
                    
                    newHistory.push({ type: 'success', text: '[+] Honeytoken Triggered! Check your main dashboard.' });
                } else {
                    newHistory.push({ type: 'info', text: `--- Content of ${fileName} ---` });
                    const content = FILE_CONTENTS[fileName] || '[No readable content found]';
                    const lines = content.split('\n');
                    lines.forEach(line => {
                        newHistory.push({ type: 'success', text: line });
                    });
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
        <div className="max-w-[1400px] mx-auto px-6 py-10 space-y-8 animate-fade-in relative">
            {/* Forensic Toast Notification */}
            {toastAlert && (
                <div className="fixed bottom-8 right-8 z-[1000] animate-slide-in-right w-full max-w-md">
                    <div className="glass-card p-5 border-l-4 border-l-neon-red border-y-white/10 border-r-white/10 bg-black/90 flex items-start gap-4 shadow-[0_10px_40px_rgba(0,0,0,0.8)] backdrop-blur-2xl relative group">
                        {/* Scanning scanline effect */}
                        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-neon-red/5 to-transparent h-1/2 w-full animate-scan pointer-events-none opacity-30" />
                        
                        <div className="relative z-10 mt-1">
                            <AlertTriangle className="w-6 h-6 text-neon-red" />
                        </div>
                        
                        <div className="relative z-10 flex-1">
                            <div className="flex items-center justify-between mb-1">
                                <h4 className="text-neon-red font-[Orbitron] font-black text-xs tracking-widest uppercase">
                                    Forensic Alert: Lateral Movement
                                </h4>
                                <span className="text-[9px] font-mono text-gray-500 uppercase">Just Now</span>
                            </div>
                            <p className="text-gray-200 font-mono text-[11px] leading-relaxed border-t border-white/5 pt-2">
                                {toastAlert.message}
                            </p>
                            <div className="mt-3 flex items-center gap-2">
                                <div className="h-1 flex-1 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-neon-red animate-progress-shrink" />
                                </div>
                            </div>
                        </div>

                        {/* Top Accent */}
                        <div className="absolute top-0 right-0 p-1">
                            <div className="w-1 h-1 rounded-full bg-neon-red animate-pulse" />
                        </div>
                    </div>
                </div>
            )}

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
                        <span className="text-[10px] font-mono text-gray-300 font-bold uppercase tracking-widest">
                            {selectedRole.userName} | UID: {selectedRole.uid}
                        </span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Simulation Console Area */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Simulation Console */}
                    <div className="glass-card bg-black/80 border border-white/10 p-6 font-mono text-[11px] flex flex-col h-[550px] overflow-hidden shadow-[0_0_30px_rgba(0,184,255,0.1)]">
                        <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-4">
                            <div className="flex items-center gap-3">
                                <div className="flex gap-2">
                                    <div className="w-3 h-3 rounded-full bg-red-500/50 hover:bg-red-500 transition-colors cursor-pointer" />
                                    <div className="w-3 h-3 rounded-full bg-yellow-500/50 hover:bg-yellow-500 transition-colors cursor-pointer" />
                                    <div className="w-3 h-3 rounded-full bg-green-500/50 hover:bg-green-500 transition-colors cursor-pointer" />
                                </div>
                                <span className="text-gray-500 ml-2 italic">internal_terminal --bash</span>
                            </div>
                            <span className="text-gray-600">v2.4.1-dist</span>
                        </div>
                        <div className="flex-1 overflow-y-auto custom-scrollbar mb-4 pr-2 space-y-2">
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
                        <form onSubmit={handleCommand} className="flex items-center gap-3 border-t border-white/5 pt-4">
                            <span className="text-neon-green font-bold text-sm">$</span>
                            <input 
                                type="text"
                                autoFocus
                                className="bg-transparent border-none outline-none text-white w-full text-sm font-mono tracking-wide placeholder:text-gray-600"
                                value={commandInput}
                                onChange={(e) => setCommandInput(e.target.value)}
                                placeholder="Type commands here..."
                            />
                        </form>
                    </div>
                </div>

                {/* Workspace Directory / Accessible Files Section */}
                <div className="space-y-6">
                    <div className="flex items-center gap-2 mb-4">
                        <Folder className="w-5 h-5 text-neon-blue" />
                        <h2 className="font-[Orbitron] text-sm font-bold text-neon-blue uppercase tracking-widest">Workspace Directory</h2>
                    </div>

                    <div className="glass-card p-6 border border-neon-blue/20 bg-neon-blue/5 shadow-[0_0_20px_rgba(0,184,255,0.05)]">
                        <h3 className="text-white font-bold text-sm mb-4 border-b border-white/10 pb-2">Accessible Files</h3>
                        <p className="text-[10px] text-gray-400 font-sans mb-6 leading-relaxed">
                            The following files have been mounted to your active session based on your identity access level. Use the terminal to interact with them.
                        </p>
                        
                        <ul className="space-y-4">
                            {ROLE_FILES[selectedRole.id].map(file => (
                                <li key={file} className="flex items-center gap-3 p-3 rounded bg-black/40 border border-white/5 hover:border-white/20 hover:bg-white/5 transition-colors cursor-default group">
                                    <FileText className="w-4 h-4 text-neon-green group-hover:text-neon-blue transition-colors" />
                                    <span className="font-mono text-xs text-gray-300 group-hover:text-white transition-colors">{file}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
}
