import { useMemo, useEffect } from 'react';
import {
    ReactFlow,
    Background,
    Handle,
    Position,
    useNodesState,
    useEdgesState,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Server, Zap, Shield, Globe, Terminal, Code2 } from 'lucide-react';

/* ── Custom Node ── */
function BranchNode({ data }) {
    const Icon = data.icon || Terminal;
    const colors = {
        core: { border: '#3b82f6', shadow: 'rgba(59,130,246,0.6)', text: '#93c5fd' },
        recon: { border: '#10b981', shadow: 'rgba(16,185,129,0.4)', text: '#6ee7b7' },
        attack: { border: '#ef4444', shadow: 'rgba(239,68,68,0.4)', text: '#fca5a5' },
        system: { border: '#8b5cf6', shadow: 'rgba(139,92,246,0.4)', text: '#c4b5fd' },
        other: { border: '#f59e0b', shadow: 'rgba(245,158,11,0.4)', text: '#fcd34d' },
    };
    const c = colors[data.nodeType] || colors.other;

    return (
        <div
            className="px-4 py-2 rounded-lg border text-center min-w-[120px] transition-all duration-500 animate-in zoom-in-50 fade-in duration-700"
            style={{
                background: 'rgba(10, 14, 26, 0.8)',
                borderColor: c.border,
                boxShadow: `0 0 15px ${c.shadow}`,
                backdropFilter: 'blur(4px)'
            }}
        >
            <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-current" style={{ color: c.border }} />
            <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-current" style={{ color: c.border }} />
            <Icon className="w-5 h-5 mx-auto mb-1" style={{ color: c.border }} />
            <div className="font-[Orbitron] text-[10px] font-bold truncate max-w-[150px]" style={{ color: c.text }}>
                {data.label}
            </div>
        </div>
    );
}

const nodeTypes = { branch: BranchNode };

export default function NetworkTopology({ commands = [] }) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        // Initial core node
        const coreNode = {
            id: 'core',
            type: 'branch',
            position: { x: 0, y: 150 },
            data: { label: 'CORE DEFENSE CENTER', icon: Shield, nodeType: 'core' }
        };

        const newNodes = [coreNode];
        const newEdges = [];

        // Command categories for coloring
        const getCmdType = (cmd) => {
            const low = cmd.toLowerCase();
            if (low.includes('ls') || low.includes('dir') || low.includes('pwd')) return 'recon';
            if (low.includes('cat') || low.includes('whoami')) return 'recon';
            if (low.includes('rm') || low.includes('sudo') || low.includes('chmod')) return 'attack';
            if (low.includes('ps') || low.includes('netstat') || low.includes('ip')) return 'system';
            return 'other';
        };

        const getIcon = (type) => {
            if (type === 'recon') return Globe;
            if (type === 'attack') return Zap;
            if (type === 'system') return Server;
            return Terminal;
        };

        // Create branches for commands
        // Limit to last 15 commands to avoid overcrowding
        const recentCommands = commands.slice(-15);

        recentCommands.forEach((cmd, idx) => {
            const type = getCmdType(cmd);
            const nodeId = `cmd-${idx}`;

            // Circular/Radial or Branching layout
            // Let's go with vertical spread on the right
            const x = 300 + (Math.floor(idx / 5) * 200);
            const y = (idx % 5) * 80 + 20;

            newNodes.push({
                id: nodeId,
                type: 'branch',
                position: { x: x, y: y },
                data: { label: cmd.toUpperCase(), icon: getIcon(type), nodeType: type }
            });

            newEdges.push({
                id: `e-${nodeId}`,
                source: 'core',
                target: nodeId,
                animated: true,
                style: { stroke: '#3b82f6', strokeWidth: 1, opacity: 0.4 }
            });
        });

        setNodes(newNodes);
        setEdges(newEdges);
    }, [commands, setNodes, setEdges]);

    return (
        <div className="glass-card overflow-hidden h-[450px] relative">
            <div className="absolute top-4 left-4 z-10 flex items-center gap-2 pointer-events-none">
                <div className="w-2 h-2 rounded-full bg-neon-blue animate-pulse" />
                <span className="font-[Orbitron] text-xs font-semibold text-neon-blue tracking-widest">DYNAMIC THREAT TOPOLOGY</span>
            </div>

            <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                proOptions={{ hideAttribution: true }}
                nodesDraggable={true}
                panOnDrag={true}
                style={{ background: 'transparent' }}
            >
                <Background color="#1e293b" gap={30} size={1} />
            </ReactFlow>
        </div>
    );
}
