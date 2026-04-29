import { Activity, Crosshair, FileTerminal, ShieldAlert } from 'lucide-react';

const LEVEL_STYLES = {
  LOW: 'text-neon-green border-neon-green/30 bg-neon-green/10',
  MEDIUM: 'text-neon-amber border-neon-amber/30 bg-neon-amber/10',
  HIGH: 'text-neon-red border-neon-red/30 bg-neon-red/10',
  CRITICAL: 'text-neon-red border-neon-red/40 bg-neon-red/15',
};

export default function CommandTelemetry({ event, active }) {
  const level = event?.risk_level || 'LOW';
  const techniques = event?.matched_techniques || [];
  const outputPreview = event?.output_preview || 'Awaiting command output...';

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-4 py-3 border-b border-white/5 bg-black/30 flex items-center gap-2">
        <Activity className={`w-4 h-4 text-neon-cyan ${active ? 'animate-pulse' : ''}`} />
        <span className="font-[Orbitron] text-xs font-semibold text-neon-cyan tracking-wider">
          LIVE COMMAND TELEMETRY
        </span>
      </div>

      <div className="p-3 space-y-3">
        <div className={`rounded border p-3 ${LEVEL_STYLES[level] || LEVEL_STYLES.LOW}`}>
          <div className="flex items-center justify-between gap-3 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span className="text-[10px] font-mono uppercase tracking-[0.2em]">Command Risk</span>
            </div>
            <span className="font-[Orbitron] text-sm shrink-0">{event?.risk_score ?? 0}/100</span>
          </div>
          <code className="block text-xs text-white break-all">
            {event?.command || 'No command captured yet'}
          </code>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded border border-white/10 bg-black/30 p-3">
            <div className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.2em] mb-1">
              Output Lines
            </div>
            <div className="font-[Orbitron] text-lg text-white">{event?.output_lines ?? 0}</div>
          </div>
          <div className="rounded border border-white/10 bg-black/30 p-3">
            <div className="text-[10px] font-mono text-gray-400 uppercase tracking-[0.2em] mb-1">
              Active Phase
            </div>
            <div className="font-[Orbitron] text-sm text-neon-purple">
              {event?.current_phase || 'Reconnaissance'}
            </div>
          </div>
        </div>

        <div className="rounded border border-white/10 bg-black/30 p-3">
          <div className="flex items-center gap-2 text-[10px] font-mono text-gray-400 uppercase tracking-[0.2em] mb-2">
            <FileTerminal className="w-3 h-3" />
            Output Preview
          </div>
          <div className="text-xs text-gray-300 font-mono break-words">
            {outputPreview}
          </div>
        </div>

        <div className="rounded border border-white/10 bg-black/30 p-3">
          <div className="flex items-center gap-2 text-[10px] font-mono text-gray-400 uppercase tracking-[0.2em] mb-2">
            <Crosshair className="w-3 h-3" />
            MITRE Mapping
          </div>
          {techniques.length === 0 ? (
            <div className="text-xs text-gray-500 font-mono">No ATT&CK mapping triggered yet.</div>
          ) : (
            <div className="space-y-2">
              {techniques.slice(0, 3).map((technique) => (
                <div key={`${technique.technique_id}-${technique.command}`} className="flex items-center justify-between gap-3 text-xs">
                  <span className="font-mono text-neon-blue">{technique.technique_id}</span>
                  <span className="text-gray-300 text-right">{technique.technique_name}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
