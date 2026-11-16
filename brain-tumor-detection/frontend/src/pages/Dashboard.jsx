import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Activity, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Layers, 
  Sparkles,
  ArrowRight,
  TrendingUp,
  RefreshCw,
  Crosshair,
  Maximize2,
  ZoomIn,
  Sliders,
  Send,
  Eye,
  ShieldCheck
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  Legend, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid 
} from 'recharts';
import { api, getMediaUrl } from '../services/api';

const CATEGORY_COLORS = {
  'Glioma': '#EF4444',
  'Meningioma': '#F59E0B',
  'Pituitary Tumor': '#8B5CF6',
  'No Tumor': '#10B981',
  'Pending / Unclassified': '#64748B'
};

export default function Dashboard({ setActiveTab, onSelectScan, onNewScan }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [diagnosticNote, setDiagnosticNote] = useState('');
  const [activeScoutSlice, setActiveScoutSlice] = useState(34);
  const [zoomLevel, setZoomLevel] = useState(100);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const handleAiNoteAssist = () => {
    setDiagnosticNote(
      "AI CADx Summary: Axial T1-CE sequence reveals focal hyperintensity consistent with high-grade glial neoplasia. Significant peritumoral T2/FLAIR vasogenic edema identified with 3.2mm subfalcine midline shift. Recommend urgent neuro-oncology MDT consultation."
    );
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[65vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-cyan-400/80 text-xs font-mono tracking-wider">INITIALIZING BRAINSIGHT AI WORKSTATION...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="p-5 rounded-xl bg-red-950/40 border border-red-800 text-red-300 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-sm">Station Connection Error</h3>
            <p className="text-xs text-red-400 mt-1">{error}</p>
            <button
              onClick={loadStats}
              className="mt-3 px-3 py-1.5 rounded bg-red-900/60 hover:bg-red-800 text-xs font-medium text-white transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  const categoryData = stats?.scans_by_category ? Object.keys(stats.scans_by_category)
    .filter(cat => stats.scans_by_category[cat] > 0 || ['Glioma', 'Meningioma', 'Pituitary Tumor', 'No Tumor'].includes(cat))
    .map(cat => ({
      name: cat,
      value: stats.scans_by_category[cat] || 0
    })) : [];

  const activityData = stats?.activity_data?.length > 0 
    ? stats.activity_data 
    : [
        { date: 'Initial', scans: stats?.total_scans || 0 }
      ];

  const recentScan = stats?.recent_scans?.[0];

  return (
    <div className="p-5 max-w-[1600px] mx-auto space-y-5">
      {/* 1. CLINICAL WORKSTATION MONITOR (MATCHING IMAGE 2) */}
      <div className="rounded-2xl bg-workstation-bg border border-navy-800 shadow-2xl overflow-hidden">
        {/* Workstation Monitor Top Bar */}
        <div className="px-5 py-2.5 bg-navy-900 border-b border-navy-800 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-3 font-mono text-[11px]">
            <span className="text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Crosshair className="w-3.5 h-3.5" />
              <span>KEY FUNCTION #1 • MULTI-PLANAR CADx MONITOR</span>
            </span>
          </div>

          <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-400">
            <span>Slice: <strong className="text-cyan-300">{activeScoutSlice}/96</strong></span>
            <span>•</span>
            <span>Zoom: <strong className="text-slate-200">{zoomLevel}%</strong></span>
          </div>
        </div>

        {/* Central Viewport & Scout Split (Image 2 style) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 bg-workstation-darkest">
          {/* Main Axial MRI Viewport */}
          <div className="lg:col-span-8 p-6 flex flex-col items-center justify-center relative min-h-[460px] border-b lg:border-b-0 lg:border-r border-navy-800/80">
            {/* Viewport Floating Controls */}
            <div className="absolute top-4 left-4 flex items-center space-x-2 bg-navy-950/80 backdrop-blur px-2.5 py-1.5 rounded-lg border border-navy-800 text-[11px] text-slate-300">
              <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
              <span>Axial T2-FLAIR</span>
              <span className="text-slate-600">|</span>
              <button 
                onClick={() => setZoomLevel(prev => Math.min(prev + 20, 200))}
                className="hover:text-cyan-300"
                title="Zoom In"
              >
                +
              </button>
              <button 
                onClick={() => setZoomLevel(prev => Math.max(prev - 20, 80))}
                className="hover:text-cyan-300"
                title="Zoom Out"
              >
                -
              </button>
            </div>

            {/* Central MRI with HUD crosshair reticle overlay */}
            <div className="relative group max-w-md w-full flex items-center justify-center">
              <div 
                className="relative rounded-2xl overflow-hidden border border-cyan-500/30 bg-black shadow-2xl transition-transform duration-200"
                style={{ transform: `scale(${zoomLevel / 100})` }}
              >
                <img
                  src={getMediaUrl('/sample_mris/sample_glioma.jpg')}
                  alt="Axial Brain MRI"
                  className="w-80 h-80 object-cover"
                />

                {/* Tactical HUD Reticle lines (from Image 2) */}
                <div className="absolute inset-0 pointer-events-none">
                  {/* Subtle target lines */}
                  <div className="absolute top-1/2 left-0 right-0 h-[1px] bg-cyan-400/20"></div>
                  <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-cyan-400/20"></div>
                  
                  {/* Reticle corner markers */}
                  <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-cyan-400"></div>
                  <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-cyan-400"></div>
                  <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-cyan-400"></div>
                  <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-cyan-400"></div>
                  
                  {/* Compass markers */}
                  <span className="absolute top-1 left-1/2 -translate-x-1/2 text-[9px] font-mono font-bold text-cyan-400">A</span>
                  <span className="absolute bottom-1 left-1/2 -translate-x-1/2 text-[9px] font-mono font-bold text-cyan-400">P</span>
                  <span className="absolute left-1 top-1/2 -translate-y-1/2 text-[9px] font-mono font-bold text-cyan-400">L</span>
                  <span className="absolute right-1 top-1/2 -translate-y-1/2 text-[9px] font-mono font-bold text-cyan-400">R</span>
                </div>
              </div>
            </div>

            {/* Quick Action Button below image */}
            <div className="mt-5 flex items-center space-x-3">
              <button
                onClick={() => onNewScan ? onNewScan() : setActiveTab('upload')}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-teal-400 hover:from-blue-500 hover:to-cyan-300 text-navy-950 font-bold text-xs shadow-lg shadow-cyan-500/20 flex items-center gap-2 transform hover:scale-[1.02] transition-all"
              >
                <span>Upload & Triage Scan</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-750 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center gap-2 transition-colors"
              >
                <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
                <span>Open Diagnostic Workstation</span>
              </button>
            </div>
          </div>

          {/* Right Scout Views & Vitals Panel (Matching Image 2) */}
          <div className="lg:col-span-4 p-5 bg-navy-950/60 flex flex-col justify-between space-y-4">
            {/* Inset Scout Views: Sagittal & Coronal (Image 2) */}
            <div className="space-y-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex justify-between">
                <span>Multi-Planar Scout Views</span>
                <span className="text-cyan-400">Ref Coordinates</span>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                {/* Sagittal Inset with Scout Line */}
                <div className="relative rounded-xl overflow-hidden border border-navy-800 bg-black p-1">
                  <img
                    src={getMediaUrl('/sample_mris/sample_pituitary_tumor.jpg')}
                    alt="Sagittal Scout"
                    className="w-full h-24 object-cover rounded opacity-80"
                  />
                  {/* Yellow scout positioning crossbar line */}
                  <div className="absolute top-[48%] left-1 right-1 h-[1.5px] bg-yellow-400 shadow-sm shadow-yellow-400"></div>
                  <span className="absolute bottom-1.5 left-2 text-[9px] font-mono text-white/90 bg-black/60 px-1 rounded">
                    Sagittal
                  </span>
                </div>

                {/* Coronal Inset with Scout Line */}
                <div className="relative rounded-xl overflow-hidden border border-navy-800 bg-black p-1">
                  <img
                    src={getMediaUrl('/sample_mris/sample_meningioma.jpg')}
                    alt="Coronal Scout"
                    className="w-full h-24 object-cover rounded opacity-80"
                  />
                  {/* Yellow scout line */}
                  <div className="absolute top-[42%] left-1 right-1 h-[1.5px] bg-yellow-400 shadow-sm shadow-yellow-400"></div>
                  <span className="absolute bottom-1.5 left-2 text-[9px] font-mono text-white/90 bg-black/60 px-1 rounded">
                    Coronal
                  </span>
                </div>
              </div>
            </div>

            {/* Circular Gauge & Vitals (Image 2) */}
            <div className="p-3.5 rounded-xl bg-navy-900 border border-navy-800/80 flex items-center justify-between">
              {/* Circular Gauge */}
              <div className="flex items-center space-x-3">
                <div className="relative w-14 h-14 rounded-full bg-cyan-950/60 border-2 border-cyan-400 flex flex-col items-center justify-center glow-cyan">
                  <span className="text-lg font-black text-white font-mono leading-none">90</span>
                  <span className="text-[8px] uppercase tracking-wider text-cyan-400 font-bold">Index</span>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-200 font-mono">216.4 / 90</div>
                  <div className="text-[10px] text-slate-400">ERP / Evoked Potentials</div>
                  <div className="text-[9px] text-emerald-400 font-mono mt-0.5">Normative Baseline</div>
                </div>
              </div>

              {/* Vertical Color Scale Bar */}
              <div className="flex flex-col items-center space-y-1">
                <span className="text-[8px] text-red-400 font-bold">100</span>
                <div className="w-2.5 h-12 rounded-full bg-gradient-to-t from-emerald-500 via-amber-400 to-red-500"></div>
                <span className="text-[8px] text-emerald-400 font-bold">0</span>
              </div>
            </div>

            {/* Pathology Risk Sliders (Image 2) */}
            <div className="p-3.5 rounded-xl bg-navy-900 border border-navy-800/80 space-y-2 text-xs">
              <div className="flex justify-between text-[10px] font-mono uppercase tracking-wider text-slate-400">
                <span>Diseases / Biomarkers</span>
                <span>Risk Stratification</span>
              </div>

              {/* Infiltration */}
              <div className="space-y-0.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-300">Infiltration Index</span>
                  <span className="text-cyan-400 font-mono">72%</span>
                </div>
                <div className="w-full h-1.5 bg-navy-800 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-emerald-400 to-amber-400 w-[72%]"></div>
                </div>
              </div>

              {/* Mass Effect */}
              <div className="space-y-0.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-300">Mass Effect / Herniation</span>
                  <span className="text-emerald-400 font-mono">18%</span>
                </div>
                <div className="w-full h-1.5 bg-navy-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-400 w-[18%]"></div>
                </div>
              </div>

              {/* Edema */}
              <div className="space-y-0.5">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-300">Peritumoral Edema</span>
                  <span className="text-red-400 font-mono">88%</span>
                </div>
                <div className="w-full h-1.5 bg-navy-800 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-amber-400 to-red-500 w-[88%]"></div>
                </div>
              </div>
            </div>

            {/* Diagnostic Notes Box (Image 2) */}
            <div className="p-3.5 rounded-xl bg-navy-900 border border-navy-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400">
                  DIAGNOSTIC NOTES
                </span>
                <button
                  onClick={handleAiNoteAssist}
                  className="text-[10px] text-cyan-300 hover:text-cyan-200 font-medium underline flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                  <span>Let AI Help You!</span>
                </button>
              </div>
              <textarea
                value={diagnosticNote}
                onChange={(e) => setDiagnosticNote(e.target.value)}
                placeholder="Write clinical findings or click 'Let AI Help You!'..."
                className="w-full h-16 p-2 rounded bg-navy-950 border border-navy-800 text-[11px] text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-400 font-mono resize-none"
              ></textarea>
            </div>
          </div>
        </div>
      </div>

      {/* 2. STATS & ANALYTICS CHARTS GRID */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Scans */}
        <div className="p-4 rounded-xl bg-navy-900 border border-navy-800/80 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Scans Ingested</span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-cyan-400 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-white font-mono">{stats?.total_scans || 0}</span>
            <span className="text-xs text-slate-500">studies</span>
          </div>
        </div>

        {/* Glioma */}
        <div className="p-4 rounded-xl bg-navy-900 border border-navy-800/80 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Glioma Positive</span>
            <div className="w-8 h-8 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center">
              <Brain className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-red-400 font-mono">
              {stats?.scans_by_category?.['Glioma'] || 0}
            </span>
            <span className="text-xs text-slate-500">cases</span>
          </div>
        </div>

        {/* Meningioma / Pituitary */}
        <div className="p-4 rounded-xl bg-navy-900 border border-navy-800/80 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Meningioma / Pituitary</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-amber-300 font-mono">
              {(stats?.scans_by_category?.['Meningioma'] || 0) + (stats?.scans_by_category?.['Pituitary Tumor'] || 0)}
            </span>
            <span className="text-xs text-slate-500">cases</span>
          </div>
        </div>

        {/* Healthy / No Tumor */}
        <div className="p-4 rounded-xl bg-navy-900 border border-navy-800/80 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">No Tumor (Healthy)</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-emerald-400 font-mono">
              {stats?.scans_by_category?.['No Tumor'] || 0}
            </span>
            <span className="text-xs text-slate-500">normal</span>
          </div>
        </div>
      </div>

      {/* 3. CHARTS ROW: CATEGORY DISTRIBUTION & INGESTION ACTIVITY */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Category Breakdown */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800/80 shadow-xl">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-3">
            Tumor Classification Distribution
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.name] || '#3B82F6'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#070E1A',
                    borderColor: '#15243E',
                    borderRadius: '8px',
                    color: '#F8FAFC',
                    fontSize: '12px'
                  }}
                />
                <Legend 
                  verticalAlign="bottom" 
                  height={32}
                  formatter={(val) => <span className="text-xs text-slate-300 font-medium">{val}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Timeline */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800/80 shadow-xl">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-3">
            MRI Ingestion Volume Activity
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activityData}>
                <defs>
                  <linearGradient id="scanGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00F2FE" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00F2FE" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#15243E" />
                <XAxis dataKey="date" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#070E1A',
                    borderColor: '#15243E',
                    borderRadius: '8px',
                    color: '#F8FAFC',
                    fontSize: '12px'
                  }}
                />
                <Area type="monotone" dataKey="scans" stroke="#00F2FE" strokeWidth={2} fill="url(#scanGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
