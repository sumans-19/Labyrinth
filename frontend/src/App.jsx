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
import NeuralAnalytics from './pages/NeuralAnalytics';
import RemoteAttackerConsole from './pages/RemoteAttackerConsole';
import CyberCorner from './components/CyberCorner';
import { Shield, Swords, Code2, Home, ShieldAlert, Box, UserCheck, BrainCircuit, Menu, X } from 'lucide-react';

const TABS = [
  { id: 'landing', label: 'Home', icon: Home },
  { id: 'warroom', label: 'External Threat', icon: Swords },
  { id: 'devsecops', label: 'Vulnerability Detector', icon: Code2 },
  { id: 'internalthreat', label: 'Internal Threat', icon: ShieldAlert },
  { id: 'neural-analytics', label: 'Neural Analytics', icon: BrainCircuit },
];

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const screenMode = params.get('screen');
  const initialTab = params.get('tab');
  const [activeTab, setActiveTab] = useState(initialTab || 'landing');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  if (screenMode === 'attacker') {
    return <RemoteAttackerConsole />;
  }

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen relative">
      <CyberGrid />

      {/* ── Navigation ── */}
      <nav className="fixed top-0 left-0 right-0 z-[100] glass-card rounded-none border-t-0 border-x-0"
        style={{ borderRadius: 0 }}>
        <CyberCorner position="bottom-left" className="text-neon-blue opacity-30" />
        <CyberCorner position="bottom-right" className="text-neon-purple opacity-30" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3 cursor-pointer shrink-0" onClick={() => handleTabChange('landing')}>
              <Shield className="w-7 h-7 text-neon-blue" style={{ filter: 'drop-shadow(0 0 8px rgba(59,130,246,0.6))' }} />
              <span className="font-[Orbitron] text-base md:text-lg font-bold tracking-widest text-white text-glow-blue whitespace-nowrap">
                LABYRINTH FORGE
              </span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-1">
              {TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
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
                    <span className="font-[Orbitron] text-xs tracking-wider">{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Mobile Menu Toggle */}
            <div className="flex lg:hidden">
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                {isMobileMenuOpen ? <X className="w-6 h-6 text-neon-red" /> : <Menu className="w-6 h-6 text-neon-blue" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        <div className={`lg:hidden transition-all duration-300 overflow-hidden bg-black/90 backdrop-blur-xl border-t border-white/10 ${isMobileMenuOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0'}`}>
          <div className="px-4 py-6 space-y-4">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-4 w-full p-4 rounded-lg transition-all
                    ${isActive 
                      ? 'bg-neon-blue/10 border border-neon-blue/30 text-neon-blue shadow-[0_0_20px_rgba(59,130,246,0.1)]' 
                      : 'text-gray-400 border border-transparent'}`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-[Orbitron] text-sm tracking-widest uppercase">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>


      {/* ── Content ── */}
      <main className="relative z-10 pt-16">
        {activeTab === 'landing' && <LandingPage onNavigate={setActiveTab} />}
        {activeTab === 'warroom' && <WarRoom />}
        {activeTab === 'devsecops' && <DevSecOps onNavigate={setActiveTab} />}
        {activeTab === 'sentinel' && <SentinelSandbox />}
        {activeTab === 'internalthreat' && <InternalThreat onNavigate={setActiveTab} />}
        {activeTab === 'leaker' && <TheLeakerDashboard onNavigate={setActiveTab} />}
        {activeTab === 'lateral-mover' && <LateralMoverPortal onNavigate={setActiveTab} />}
        {activeTab === 'impersonator' && <ImpersonatorPortal onNavigate={setActiveTab} />}
        {activeTab === 'neural-analytics' && <NeuralAnalytics onNavigate={setActiveTab} />}
      </main>
    </div>
  );
}
