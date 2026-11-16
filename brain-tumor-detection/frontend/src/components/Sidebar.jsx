import React from 'react';
import { 
  LayoutDashboard, 
  UploadCloud, 
  Sliders, 
  Activity, 
  History, 
  Info, 
  Brain,
  ShieldAlert,
  ChevronRight,
  Crosshair,
  Layers,
  FileCheck
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Main Dashboard', icon: LayoutDashboard, badge: null, desc: 'Scouts & Vitals' },
  { id: 'upload', label: 'MRI Scan Upload', icon: UploadCloud, badge: 'Step 1', desc: 'Ingestion & Triage' },
  { id: 'enhance', label: 'MRI Enhancement', icon: Sliders, badge: 'Step 2', desc: 'OpenCV CLAHE' },
  { id: 'results', label: 'AI Detection & Seg', icon: Crosshair, badge: 'Step 3', desc: 'Workstation View' },
  { id: 'history', label: 'Scan History', icon: History, badge: null, desc: 'Archival Registry' },
  { id: 'about', label: 'About Project', icon: Info, badge: null, desc: 'Academic Specs' },
];

export default function Sidebar({ activeTab, setActiveTab, currentScan, onNewScan }) {
  return (
    <aside className="w-64 bg-navy-900 border-r border-navy-800 flex flex-col shrink-0 select-none z-30">
      {/* Brand Header: BrainSight AI / AI MEDIX */}
      <div className="p-4 border-b border-navy-800 flex items-center space-x-3 bg-navy-950/80">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-teal-300 flex items-center justify-center shadow-lg shadow-cyan-500/25 ring-1 ring-cyan-400/40">
          <Brain className="w-5 h-5 text-navy-950 stroke-[2.4]" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1 className="font-extrabold text-sm tracking-wide text-white">BrainSight</h1>
            <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-cyan-500 text-navy-950">AI</span>
          </div>
          <p className="text-[10px] text-cyan-400/80 font-mono tracking-tight">AI MEDIX Workstation</p>
        </div>
      </div>

      {/* Operator & System Status Badge */}
      <div className="mx-3 mt-3 px-3 py-2 rounded-lg bg-navy-850/80 border border-navy-800 text-[10px] space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 uppercase font-semibold tracking-wider">Station Status</span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            ACTIVE
          </span>
        </div>
        <div className="text-slate-400 flex justify-between font-mono">
          <span>User:</span>
          <span className="text-slate-200 font-semibold">DR_ELIZA_CHEN</span>
        </div>
        <div className="text-slate-400 flex justify-between font-mono">
          <span>Project:</span>
          <span className="text-cyan-300">Neuro_Oncology_v4.1</span>
        </div>
      </div>

      {/* Active Scan Indicator Widget */}
      {currentScan ? (
        <div className="mx-3 mt-2.5 p-2.5 rounded-lg bg-navy-850 border border-cyan-500/30 shadow-inner">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span className="font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
              <Crosshair className="w-3 h-3 text-cyan-400" />
              <span>Loaded Scan</span>
            </span>
            <span className="font-mono text-cyan-300 font-bold">{currentScan.scan_id.slice(-6)}</span>
          </div>
          <p className="text-[11px] font-medium text-slate-200 truncate">{currentScan.filename}</p>
          {currentScan.predicted_category && (
            <div className="mt-1.5 flex items-center justify-between text-[10px] pt-1 border-t border-navy-750">
              <span className="text-slate-400">Class:</span>
              <span className="font-bold text-cyan-300">{currentScan.predicted_category}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="mx-3 mt-2.5 p-2.5 rounded-lg bg-navy-950/70 border border-navy-800 text-[10px] text-slate-400 flex items-center justify-between">
          <span>No study loaded</span>
          <button
            onClick={(e) => {
              e.preventDefault();
              if (onNewScan) {
                onNewScan();
              } else {
                setActiveTab('upload');
              }
            }}
            className="text-cyan-400 hover:text-cyan-300 font-bold"
          >
            + Ingest Scan
          </button>
        </div>
      )}

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-1.5 text-[9px] font-bold uppercase tracking-wider text-slate-500">
          Clinical Workflow
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={(e) => {
                e.preventDefault();
                if (item.id === 'upload') {
                  if (onNewScan) {
                    onNewScan();
                  } else {
                    setActiveTab('upload');
                  }
                } else {
                  setActiveTab(item.id);
                }
              }}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 via-blue-600/20 to-transparent text-cyan-300 border-l-4 border-cyan-400 shadow-md shadow-cyan-950/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-navy-850/60'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Icon className={`w-4 h-4 transition-colors ${isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <div className="text-left">
                  <div className="tracking-wide text-xs">{item.label}</div>
                  <div className="text-[9px] text-slate-500 font-normal">{item.desc}</div>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                {item.badge && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                    isActive ? 'bg-cyan-500/25 text-cyan-300' : 'bg-navy-800 text-slate-500'
                  }`}>
                    {item.badge}
                  </span>
                )}
                {isActive && <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />}
              </div>
            </button>
          );
        })}
      </nav>

      {/* Safety Notice Footer */}
      <div className="p-2.5 mx-3 mb-2 rounded-lg bg-navy-950/80 border border-navy-800 text-[10px] text-slate-400">
        <div className="flex items-center gap-1.5 text-amber-400/90 font-medium mb-1">
          <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
          <span>Workflow & CADx Support</span>
        </div>
        <p className="text-[9px] leading-tight text-slate-500">
          Does not constitute definitive clinical diagnosis. Professional review required.
        </p>
      </div>

      {/* Footer Version */}
      <div className="px-4 py-2 border-t border-navy-800/80 text-[10px] text-slate-500 flex justify-between items-center bg-navy-950/60">
        <span className="font-mono text-[9px]">DICOM Workstation v4.2</span>
        <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400"></span>
      </div>
    </aside>
  );
}
