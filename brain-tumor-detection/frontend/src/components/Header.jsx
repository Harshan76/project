import React from 'react';
import { 
  PlusCircle, 
  Cpu, 
  Activity, 
  Heart, 
  HelpCircle, 
  ZoomIn, 
  Crosshair, 
  SlidersHorizontal,
  Bookmark
} from 'lucide-react';

export default function Header({ activeTab, setActiveTab, modelStatus, backendHealth, onNewAnalysis, currentScan }) {
  const patientName = currentScan?.patient_id || 'JOHNY MARTIN';
  const scanId = currentScan?.scan_id || 'SCAN-REF-88301';
  const currentDate = new Date().toISOString().slice(0, 10);

  return (
    <header className="bg-navy-900 border-b border-navy-800 text-xs select-none sticky top-0 z-20 shadow-lg">
      {/* Top Patient & EEG/ECG Monitor Strip (matching Image 2) */}
      <div className="h-10 px-4 bg-navy-950 border-b border-navy-850 flex items-center justify-between overflow-hidden">
        {/* Patient Vitals Badge */}
        <div className="flex items-center space-x-4 shrink-0 font-mono text-[11px]">
          <div className="flex items-center space-x-1.5 text-slate-300">
            <span className="font-bold text-white tracking-wide">{patientName}</span>
            <span className="text-[10px] text-slate-500">ID: {scanId.slice(-8)}</span>
          </div>
          <div className="hidden sm:flex items-center space-x-3 text-[10px] text-slate-400 border-l border-navy-800 pl-3">
            <span>Gender: <strong className="text-slate-200">M</strong></span>
            <span>Age: <strong className="text-slate-200">38</strong></span>
            <span>Date: <strong className="text-slate-200">{currentDate}</strong></span>
          </div>
        </div>

        {/* Animated ECG / EEG Real-Time Rhythm Monitor Line */}
        <div className="hidden md:flex items-center flex-1 max-w-md mx-6 h-5 relative overflow-hidden opacity-85">
          <svg className="w-[800px] h-full animate-eeg" viewBox="0 0 800 24" fill="none" stroke="#00F2FE" strokeWidth="1.5">
            <path d="M0,12 L50,12 L55,12 L60,3 L65,21 L70,8 L75,16 L80,12 L130,12 L180,12 L185,12 L190,3 L195,21 L200,8 L205,16 L210,12 L260,12 L310,12 L315,12 L320,3 L325,21 L330,8 L335,16 L340,12 L390,12 L440,12 L445,12 L450,3 L455,21 L460,8 L465,16 L470,12 L520,12 L570,12 L575,12 L580,3 L585,21 L590,8 L595,16 L600,12 L650,12 L700,12 L705,12 L710,3 L715,21 L720,8 L725,16 L730,12 L800,12" />
          </svg>
          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-navy-950 to-transparent"></div>
        </div>

        {/* Vitals & Status */}
        <div className="flex items-center space-x-2 shrink-0">
          {/* Backend API Health Status */}
          <div 
            title={backendHealth?.online ? "Flask REST API connected" : "Flask backend offline"}
            className={`flex items-center space-x-1 px-2 py-0.5 rounded border text-[10px] font-mono ${
              backendHealth?.online 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-red-500/15 border-red-500/40 text-red-300 animate-pulse'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${backendHealth?.online ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
            <span>{backendHealth?.online ? 'API ONLINE' : 'API OFFLINE'}</span>
          </div>

          <div className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-mono">
            <Heart className="w-3 h-3 text-red-400 animate-pulse fill-red-400" />
            <span>72 BPM</span>
          </div>

          <div className={`flex items-center space-x-1 px-2 py-0.5 rounded border text-[10px] font-mono ${
            modelStatus?.model_available 
              ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300' 
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            <Cpu className="w-3 h-3" />
            <span>{modelStatus?.model_available ? 'CNN ONLINE' : 'TRAIN CNN'}</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Bar */}
      <div className="h-12 px-5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h2 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400"></span>
            {activeTab === 'dashboard' && 'AI MEDIX Clinical Monitor • Main Dashboard'}
            {activeTab === 'upload' && 'MRI Scan Upload & Triage Assessment'}
            {activeTab === 'enhance' && 'OpenCV CLAHE & Multi-Filter Preprocessing'}
            {activeTab === 'results' && 'AI Detection & Segmentation • Diagnostic Workstation'}
            {activeTab === 'history' && 'Archival Registry & Patient Studies'}
            {activeTab === 'about' && 'System Architecture & Mathematical Foundations'}
          </h2>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* AI Help Pill (matching Image 2) */}
          <button 
            onClick={() => setActiveTab('about')}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-navy-800 hover:bg-navy-750 text-cyan-300 border border-cyan-500/30 text-[11px] font-semibold transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI HELP</span>
          </button>

          {/* Quick Action: Ingest New Scan */}
          <button
            onClick={(e) => {
              e.preventDefault();
              if (onNewAnalysis) {
                onNewAnalysis();
              } else {
                setActiveTab('upload');
              }
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 via-cyan-500 to-teal-400 hover:from-blue-500 hover:to-cyan-300 text-navy-950 font-bold text-xs shadow-md shadow-cyan-500/20 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <PlusCircle className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>New Scan</span>
          </button>
        </div>
      </div>
    </header>
  );
}
