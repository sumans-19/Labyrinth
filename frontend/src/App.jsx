import { useState } from 'react';
import CyberGrid from './components/CyberGrid';
import LandingPage from './pages/LandingPage';
import WarRoom from './pages/WarRoom';
import DevSecOps from './pages/DevSecOps';
import InternalThreat from './pages/InternalThreat';
import TheLeakerDashboard from './pages/TheLeakerDashboard';
import LateralMoverPortal from './pages/LateralMoverPortal';
import SentinelSandbox from './pages/SentinelSandbox';
import ImpersonatorPortal from './pages/ImpersonatorPortal';
import CyberCorner from './components/CyberCorner';
import { Shield, Swords, Code2, Home, ShieldAlert, Box, UserCheck } from 'lucide-react';

const TABS = [
  { id: 'landing', label: 'Home', icon: Home },
  { id: 'warroom', label: 'External Threat', icon: Swords },
  { id: 'devsecops', label: 'Vulnerability Detector', icon: Code2 },
  { id: 'sentinel', label: 'Sentinel Sandbox', icon: Box },
  { id: 'internalthreat', label: 'Internal Threat', icon: ShieldAlert },
  { id: 'impersonator', label: 'Impersonator', icon: UserCheck },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('landing');

  return (
    <div className="min-h-screen relative">
      <CyberGrid />

      {/* ── Navigation ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card rounded-none border-t-0 border-x-0"
        style={{ borderRadius: 0 }}>
        <CyberCorner position="bottom-left" className="text-neon-blue opacity-30" />
        <CyberCorner position="bottom-right" className="text-neon-purple opacity-30" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('landing')}>
              <Shield className="w-8 h-8 text-neon-blue" style={{ filter: 'drop-shadow(0 0 8px rgba(59,130,246,0.6))' }} />
              <span className="font-[Orbitron] text-lg font-bold tracking-widest text-white text-glow-blue">
                LABYRINTH FORGE
              </span>
            </div>

            {/* Tab Buttons */}
            <div className="flex items-center gap-1">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-all duration-300 cursor-pointer
                        ${isActive
                        ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/40 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                        : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                      }`}
                    style={{
                      clipPath: 'polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)'
                    }}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline font-[Orbitron] text-xs tracking-wider">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </nav>

      {/* ── Content ── */}
      <main className="relative z-10 pt-16">
        {activeTab === 'landing' && <LandingPage onNavigate={setActiveTab} />}
        {activeTab === 'warroom' && <WarRoom />}
        {activeTab === 'devsecops' && <DevSecOps />}
        {activeTab === 'sentinel' && <SentinelSandbox />}
        {activeTab === 'internalthreat' && <InternalThreat onNavigate={setActiveTab} />}
        {activeTab === 'leaker' && <TheLeakerDashboard onNavigate={setActiveTab} />}
        {activeTab === 'lateral-mover' && <LateralMoverPortal onNavigate={setActiveTab} />}
        {activeTab === 'impersonator' && <ImpersonatorPortal onNavigate={setActiveTab} />}
      </main>
    </div>
  );
}
