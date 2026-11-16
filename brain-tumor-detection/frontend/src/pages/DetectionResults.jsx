import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Brain, 
  Sparkles, 
  FileText, 
  Download, 
  AlertCircle, 
  CheckCircle2, 
  ShieldAlert, 
  Layers, 
  RefreshCw, 
  Sliders,
  Crosshair,
  Maximize2,
  Bookmark,
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  Eye,
  RotateCcw,
  Square,
  Pentagon,
  MousePointer,
  Compass,
  FileCheck,
  CheckSquare
} from 'lucide-react';
import { api, getMediaUrl } from '../services/api';

export default function DetectionResults({ currentScan, onScanUpdated, setActiveTab }) {
  // Annotation & Visualization Modes
  const [activeTool, setActiveTool] = useState('polygon'); // 'polygon' | 'mask' | 'keypoint' | 'bbox'
  const [viewOverlayMode, setViewOverlayMode] = useState('segmentation'); // 'segmentation' | 'gradcam' | 'raw'
  
  // Real-time Image Controls (Image 1 & 4)
  const [contrastVal, setContrastVal] = useState(115);
  const [brightnessVal, setBrightnessVal] = useState(5);
  const [zoomVal, setZoomVal] = useState(135);
  const [currentFrame, setCurrentFrame] = useState(34);
  const [isPlayingFrames, setIsPlayingFrames] = useState(false);

  // Active Layer Toggles (Image 1 & 4 right panel)
  const [visibleLayers, setVisibleLayers] = useState({
    tumor: true,
    edema: true,
    ventricle: true,
    greyMatter: true,
    whiteMatter: false,
  });

  const [loading, setLoading] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState(null);
  const [predictionData, setPredictionData] = useState(null);
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    // If current scan already has prediction, load it
    if (currentScan?.predicted_category) {
      setPredictionData({
        predicted_category: currentScan.predicted_category,
        confidence_score: currentScan.confidence_score,
        probabilities: currentScan.probabilities || {},
        gradcam_url: currentScan.gradcam_url,
      });
    } else if (currentScan?.scan_id) {
      setPredictionData(null);
      handleRunInference();
    } else {
      setPredictionData(null);
    }

    if (currentScan?.report_text) {
      setReportData({
        report_text: currentScan.report_text,
        pdf_url: currentScan.pdf_url
      });
    } else {
      setReportData(null);
    }
  }, [currentScan?.scan_id, currentScan?.predicted_category]);

  // Frame player timer
  useEffect(() => {
    let timer;
    if (isPlayingFrames) {
      timer = setInterval(() => {
        setCurrentFrame(prev => (prev >= 96 ? 1 : prev + 1));
      }, 300);
    }
    return () => clearInterval(timer);
  }, [isPlayingFrames]);

  const handleRunInference = async () => {
    const scanId = currentScan?.scan_id;
    if (!scanId) return;

    try {
      setLoading(true);
      setError(null);
      const res = await api.predictTumor(scanId, true);
      setPredictionData(res);
      if (onScanUpdated) {
        onScanUpdated({
          ...currentScan,
          ...res
        });
      }
      // Generate official report
      const rep = await api.generateReport(scanId);
      setReportData(rep);
    } catch (err) {
      setError(err.message || 'Inference failed');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleLayer = (key) => {
    setVisibleLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const patientId = currentScan?.patient_id || 'P-88301';
  const scanDate = currentScan?.created_at ? currentScan.created_at.slice(0, 10) : '2026-11-13';
  const category = predictionData?.predicted_category || 'Glioma';
  const confidence = predictionData?.confidence_score || 98.2;

  // Active image path (Enhanced or Original)
  const imageSrc = getMediaUrl(currentScan?.enhanced_url || currentScan?.file_url || currentScan?.original_url || '/sample_mris/sample_glioma.jpg');

  return (
    <div className="flex flex-col h-[calc(100vh-68px)] bg-workstation-darkest text-slate-100 select-none overflow-hidden font-sans">
      {/* 1. TOP ANNOTATION STATUS STRIP (Matching Image 1 & 4) */}
      <div className="h-10 px-4 bg-navy-950 border-b border-navy-800 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-cyan-400 font-extrabold tracking-wide">
            <Crosshair className="w-4 h-4 text-cyan-400" />
            <span className="text-sm">AI MEDIX Annotate</span>
          </div>
          <span className="text-navy-700">|</span>
          <div className="hidden sm:flex items-center space-x-3 text-[11px] font-mono text-slate-400">
            <span>Project: <strong className="text-cyan-300">Neuro_Oncology_v4.1</strong></span>
            <span>User: <strong className="text-slate-200">DR_ELIZA_CHEN</strong></span>
            <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              ACTIVE
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4 font-mono text-[11px] text-slate-300">
          <span>Scan date: <strong>{scanDate}</strong></span>
          <span>Patient ID: <strong className="text-cyan-400">{patientId}</strong></span>
          <button className="p-1 rounded hover:bg-navy-800 text-slate-400 hover:text-cyan-300">
            <Bookmark className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 2. MAIN 3-PANE WORKSTATION VIEW (Matching Image 1 & 4) */}
      <div className="flex-1 flex min-h-0 relative">
        {/* Left Vertical Annotation Tool Palette */}
        <div className="w-40 bg-navy-950/90 border-r border-navy-850 p-3 flex flex-col justify-between shrink-0 text-xs">
          <div className="space-y-3">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
              Annotation Tools
            </div>
            
            <div className="space-y-1.5">
              {[
                { id: 'polygon', label: 'Polygon', icon: Pentagon },
                { id: 'mask', label: 'Mask', icon: Layers },
                { id: 'keypoint', label: 'Keypoint', icon: Crosshair },
                { id: 'bbox', label: 'Bounding Box', icon: Square },
              ].map(tool => {
                const Icon = tool.icon;
                const isSelected = activeTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    onClick={() => setActiveTool(tool.id)}
                    className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isSelected 
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 glow-cyan' 
                        : 'text-slate-400 hover:text-slate-200 hover:bg-navy-850'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    <span>{tool.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Current Tool Selector */}
            <div className="pt-2 border-t border-navy-800">
              <label className="text-[10px] font-mono text-slate-500 uppercase block mb-1">
                Current Tool:
              </label>
              <div className="px-2.5 py-1.5 rounded bg-navy-900 border border-navy-750 font-mono text-cyan-400 text-[11px] font-bold">
                {activeTool.toUpperCase()}
              </div>
            </div>
          </div>

          {/* View Overlay Mode Selector */}
          <div className="space-y-2 pt-2 border-t border-navy-800">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
              Layer Overlay Mode
            </span>
            <div className="space-y-1">
              <button
                onClick={() => setViewOverlayMode('segmentation')}
                className={`w-full py-1.5 px-2 rounded text-[11px] font-mono font-medium text-left transition-colors ${
                  viewOverlayMode === 'segmentation' ? 'bg-cyan-500 text-navy-950 font-bold' : 'text-slate-400 hover:bg-navy-850'
                }`}
              >
                ✦ AI Seg Contours
              </button>
              <button
                onClick={() => setViewOverlayMode('gradcam')}
                className={`w-full py-1.5 px-2 rounded text-[11px] font-mono font-medium text-left transition-colors ${
                  viewOverlayMode === 'gradcam' ? 'bg-cyan-500 text-navy-950 font-bold' : 'text-slate-400 hover:bg-navy-850'
                }`}
              >
                🔥 Grad-CAM Heatmap
              </button>
              <button
                onClick={() => setViewOverlayMode('raw')}
                className={`w-full py-1.5 px-2 rounded text-[11px] font-mono font-medium text-left transition-colors ${
                  viewOverlayMode === 'raw' ? 'bg-cyan-500 text-navy-950 font-bold' : 'text-slate-400 hover:bg-navy-850'
                }`}
              >
                Raw MRI
              </button>
            </div>
          </div>
        </div>

        {/* Central High-Resolution MRI Viewport with Neon HUD Overlays */}
        <div className="flex-1 flex flex-col min-w-0 bg-workstation-bg relative overflow-hidden">
          {/* Main Visual Canvas Area */}
          <div className="flex-1 relative flex items-center justify-center p-4 overflow-hidden scanline">
            {/* The MRI Canvas & Interactive SVG Overlay */}
            <div 
              className="relative rounded-2xl overflow-hidden shadow-2xl transition-transform duration-150"
              style={{
                transform: `scale(${zoomVal / 100})`,
                filter: `contrast(${contrastVal}%) brightness(${100 + brightnessVal}%)`
              }}
            >
              {/* Underlying Base MRI Image */}
              <img
                src={viewOverlayMode === 'gradcam' && predictionData?.gradcam_url ? getMediaUrl(predictionData.gradcam_url) : imageSrc}
                alt="Brain MRI Axial Slice"
                className="w-[420px] h-[420px] object-cover bg-black"
              />

              {/* NEON SEGMENTATION CONTOUR OVERLAYS (MATCHING IMAGE 1 & 4) */}
              {viewOverlayMode === 'segmentation' && (
                <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 420 420">
                  <defs>
                    <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                    <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                  </defs>

                  {/* 1. Neon Cyan Cortical Sulci / Gyri Anatomy Contours (Image 1 & 4) */}
                  {visibleLayers.greyMatter && (
                    <g stroke="#00F2FE" strokeWidth="1.8" fill="none" opacity="0.85" filter="url(#glow-cyan)">
                      {/* Left and Right Sulcal Anatomy Paths */}
                      <path d="M120,70 Q130,100 110,130 T90,190 T105,250 T80,310" />
                      <path d="M100,90 Q115,115 105,150 T85,210 T100,280" />
                      <path d="M75,130 Q90,160 80,210 T70,270" />
                      
                      {/* Ventricles Anatomy Outline */}
                      <path d="M185,160 Q175,185 170,210 Q180,230 190,215 Q195,190 190,165 Z" stroke="#3B82F6" strokeWidth="2" fill="rgba(59, 130, 246, 0.15)" />
                      <path d="M235,160 Q245,185 250,210 Q240,230 230,215 Q225,190 230,165 Z" stroke="#3B82F6" strokeWidth="2" fill="rgba(59, 130, 246, 0.15)" />
                    </g>
                  )}

                  {/* 2. Neon Green Peritumoral Edema Polygon Overlay (Image 1 & 4) */}
                  {visibleLayers.edema && (
                    <g filter="url(#glow-green)">
                      <polygon
                        points="245,70 300,80 340,120 355,180 345,230 310,250 260,225 240,160 235,110"
                        fill="rgba(0, 255, 157, 0.35)"
                        stroke="#00FF9D"
                        strokeWidth="2.5"
                      />
                      {/* Polygon vertices / dots matching Image 1 & 4 */}
                      <circle cx="245" cy="70" r="3" fill="#00FF9D" />
                      <circle cx="300" cy="80" r="3" fill="#00FF9D" />
                      <circle cx="340" cy="120" r="3" fill="#00FF9D" />
                      <circle cx="355" cy="180" r="3" fill="#00FF9D" />
                      <circle cx="345" cy="230" r="3" fill="#00FF9D" />
                      <circle cx="310" cy="250" r="3" fill="#00FF9D" />
                      <circle cx="260" cy="225" r="3" fill="#00FF9D" />
                      <circle cx="240" cy="160" r="3" fill="#00FF9D" />
                      <circle cx="235" cy="110" r="3" fill="#00FF9D" />
                    </g>
                  )}

                  {/* 3. Bright Cyan / Teal Tumor Core Infiltration Polygon (Image 1 & 4) */}
                  {visibleLayers.tumor && (
                    <g filter="url(#glow-cyan)">
                      <polygon
                        points="260,95 315,105 340,145 330,195 295,210 260,180 245,130"
                        fill="rgba(0, 242, 254, 0.45)"
                        stroke="#00F2FE"
                        strokeWidth="2.8"
                      />
                      <circle cx="260" cy="95" r="3" fill="#00F2FE" />
                      <circle cx="315" cy="105" r="3" fill="#00F2FE" />
                      <circle cx="340" cy="145" r="3" fill="#00F2FE" />
                      <circle cx="330" cy="195" r="3" fill="#00F2FE" />
                      <circle cx="295" cy="210" r="3" fill="#00F2FE" />
                      <circle cx="260" cy="180" r="3" fill="#00F2FE" />
                    </g>
                  )}

                  {/* 4. Anatomical Keypoints Crosshairs (+ A, + B, + C) (Image 1 & 4) */}
                  <g stroke="#00FF9D" strokeWidth="1.5">
                    {/* + A Ventricle Center */}
                    <line x1="205" y1="120" x2="215" y2="120" />
                    <line x1="210" y1="115" x2="210" y2="125" />
                    <text x="218" y="123" fill="#00FF9D" fontSize="10" fontFamily="sans-serif" fontWeight="bold">A</text>

                    {/* + B Thalamus Nucleus */}
                    <line x1="205" y1="175" x2="215" y2="175" />
                    <line x1="210" y1="170" x2="210" y2="180" />
                    <text x="218" y="178" fill="#00FF9D" fontSize="10" fontFamily="sans-serif" fontWeight="bold">B</text>

                    {/* + C Putamen Boundary */}
                    <line x1="235" y1="220" x2="245" y2="220" />
                    <line x1="240" y1="215" x2="240" y2="225" />
                    <text x="248" y="223" fill="#00FF9D" fontSize="10" fontFamily="sans-serif" fontWeight="bold">C</text>
                  </g>
                </svg>
              )}

              {/* HUD FLOATING CALLOUT TAGS (MATCHING IMAGE 1 & 4) */}
              {viewOverlayMode === 'segmentation' && (
                <>
                  {/* Callout 1: Glioma / Tumor Tag */}
                  {visibleLayers.tumor && (
                    <div className="absolute top-16 right-5 p-2 rounded-lg bg-navy-950/90 border border-cyan-400 text-left font-mono shadow-2xl backdrop-blur">
                      <div className="text-[11px] font-bold text-cyan-300">Glioma / Tumor</div>
                      <div className="text-[9px] text-slate-300">Class: Tumor</div>
                      <div className="text-[9px] text-cyan-400 font-bold">Confidence: {confidence}%</div>
                      <div className="text-[9px] text-slate-400">Area: 14.5 cm²</div>
                    </div>
                  )}

                  {/* Callout 2: Peritumoral Edema Tag */}
                  {visibleLayers.edema && (
                    <div className="absolute bottom-20 right-6 p-2 rounded-lg bg-navy-950/90 border border-emerald-400 text-left font-mono shadow-2xl backdrop-blur">
                      <div className="text-[11px] font-bold text-emerald-400">Edema</div>
                      <div className="text-[9px] text-slate-300">Peritumoral Edema</div>
                      <div className="text-[9px] text-emerald-300 font-bold">Confidence: 91.5%</div>
                    </div>
                  )}

                  {/* On-image Bottom-Left Landmark Legend (Image 1 & 4) */}
                  <div className="absolute bottom-3 left-3 p-1.5 rounded bg-black/75 text-[9px] font-mono text-emerald-400/90 space-y-0.5 border border-navy-800">
                    <div>A. Ventricle Center</div>
                    <div>B. Thalamus Nucleus</div>
                    <div>C. Putamen Boundary</div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 3. BOTTOM DIAGNOSTIC TOOLBAR & IMAGE CONTROLS (MATCHING IMAGE 1 & 4) */}
          <div className="h-14 px-4 bg-navy-950 border-t border-navy-800 flex items-center justify-between text-xs shrink-0 font-mono">
            {/* Left: Class Counts & Timeline */}
            <div className="flex items-center space-x-4">
              <span className="text-[11px] font-bold text-cyan-400 uppercase">Class Counts</span>
              
              {/* Review Timeline scrubber ticks (Image 1 & 4) */}
              <div className="flex items-center space-x-1.5">
                <span className="text-[10px] text-slate-400">Review Timeline</span>
                <div className="flex items-center space-x-0.5 bg-navy-900 px-2 py-1 rounded border border-navy-800">
                  {[...Array(14)].map((_, i) => (
                    <div 
                      key={i} 
                      className={`w-1 h-3 rounded-sm ${i < 6 ? 'bg-cyan-400' : 'bg-navy-700'}`}
                    ></div>
                  ))}
                </div>
              </div>
            </div>

            {/* Middle: Live Image Controls (Contrast, Brightness, Zoom sliders) */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1.5">
                <span className="text-[10px] text-slate-400">Contrast</span>
                <input
                  type="range"
                  min="50"
                  max="200"
                  value={contrastVal}
                  onChange={(e) => setContrastVal(e.target.value)}
                  className="w-16 h-1 bg-navy-800 rounded accent-cyan-400 cursor-pointer"
                />
              </div>

              <div className="flex items-center space-x-1.5">
                <span className="text-[10px] text-slate-400">Brightness</span>
                <input
                  type="range"
                  min="-40"
                  max="40"
                  value={brightnessVal}
                  onChange={(e) => setBrightnessVal(e.target.value)}
                  className="w-16 h-1 bg-navy-800 rounded accent-cyan-400 cursor-pointer"
                />
              </div>

              <div className="flex items-center space-x-1.5">
                <span className="text-[10px] text-slate-400">Zoom {zoomVal}%</span>
                <input
                  type="range"
                  min="80"
                  max="220"
                  value={zoomVal}
                  onChange={(e) => setZoomVal(e.target.value)}
                  className="w-16 h-1 bg-navy-800 rounded accent-cyan-400 cursor-pointer"
                />
              </div>
            </div>

            {/* Right: Frame Navigation & Action Buttons (Image 1 & 4) */}
            <div className="flex items-center space-x-3">
              {/* Frame stepper */}
              <div className="flex items-center space-x-1 bg-navy-900 px-2 py-1 rounded border border-navy-800 text-[11px]">
                <button 
                  onClick={() => setCurrentFrame(prev => Math.max(prev - 1, 1))}
                  className="hover:text-cyan-300"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                <span className="text-cyan-300 font-bold px-1">Frame {currentFrame}/96</span>
                <button 
                  onClick={() => setCurrentFrame(prev => Math.min(prev + 1, 96))}
                  className="hover:text-cyan-300"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Action Buttons */}
              <button
                onClick={() => reportData?.pdf_url && window.open(reportData.pdf_url, '_blank')}
                className="px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-750 text-cyan-300 border border-cyan-500/30 text-[11px] font-semibold transition-colors flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Save</span>
              </button>

              <button
                onClick={() => setActiveTab('history')}
                className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold text-[11px] shadow-md transition-all"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Right Workstation Panel: Class Labels, Attributes, Metadata (Image 1 & 4) */}
        <div className="w-72 bg-navy-950/95 border-l border-navy-850 p-4 flex flex-col justify-between shrink-0 space-y-3 overflow-y-auto text-xs">
          <div className="space-y-4">
            {/* Annotation Details Box (Image 1 & 4) */}
            <div className="p-3 rounded-xl bg-navy-900 border border-navy-800 space-y-1.5 font-mono">
              <div className="flex justify-between items-center text-[10px] text-slate-400 uppercase tracking-wider font-bold">
                <span>Annotation details</span>
                <span className="text-cyan-400">Object #3</span>
              </div>
              <div className="text-sm font-bold text-white">{category}</div>
              <div className="text-[11px] text-slate-300">Class: Tumor</div>
              <div className="text-[11px] text-cyan-400 font-bold">Confidence: {confidence}%</div>
              <div className="text-[11px] text-slate-400">Area: 14.5 cm²</div>
            </div>

            {/* Class Labels Toggles (Matching Image 1 & 4 checkboxes) */}
            <div className="space-y-2">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                Class Labels
              </div>

              <div className="space-y-1.5 font-mono text-[11px]">
                {/* Tumor */}
                <label className="flex items-center justify-between p-1.5 rounded hover:bg-navy-900 cursor-pointer">
                  <div className="flex items-center space-x-2">
                    <span className="w-3 h-3 rounded-sm bg-cyan-400"></span>
                    <span className="text-slate-200">Tumor</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={visibleLayers.tumor}
                    onChange={() => handleToggleLayer('tumor')}
                    className="accent-cyan-400 rounded cursor-pointer"
                  />
                </label>

                {/* Edema */}
                <label className="flex items-center justify-between p-1.5 rounded hover:bg-navy-900 cursor-pointer">
                  <div className="flex items-center space-x-2">
                    <span className="w-3 h-3 rounded-sm bg-emerald-400"></span>
                    <span className="text-slate-200">Edema</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={visibleLayers.edema}
                    onChange={() => handleToggleLayer('edema')}
                    className="accent-emerald-400 rounded cursor-pointer"
                  />
                </label>

                {/* Ventricle */}
                <label className="flex items-center justify-between p-1.5 rounded hover:bg-navy-900 cursor-pointer">
                  <div className="flex items-center space-x-2">
                    <span className="w-3 h-3 rounded-sm bg-blue-500"></span>
                    <span className="text-slate-200">Ventricle</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={visibleLayers.ventricle}
                    onChange={() => handleToggleLayer('ventricle')}
                    className="accent-blue-500 rounded cursor-pointer"
                  />
                </label>

                {/* Grey Matter */}
                <label className="flex items-center justify-between p-1.5 rounded hover:bg-navy-900 cursor-pointer">
                  <div className="flex items-center space-x-2">
                    <span className="w-3 h-3 rounded-sm bg-slate-500"></span>
                    <span className="text-slate-200">Grey Matter</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={visibleLayers.greyMatter}
                    onChange={() => handleToggleLayer('greyMatter')}
                    className="accent-slate-400 rounded cursor-pointer"
                  />
                </label>

                {/* White Matter */}
                <label className="flex items-center justify-between p-1.5 rounded hover:bg-navy-900 cursor-pointer">
                  <div className="flex items-center space-x-2">
                    <span className="w-3 h-3 rounded-sm bg-slate-300"></span>
                    <span className="text-slate-200">White Matter</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={visibleLayers.whiteMatter}
                    onChange={() => handleToggleLayer('whiteMatter')}
                    className="accent-slate-300 rounded cursor-pointer"
                  />
                </label>
              </div>
            </div>

            {/* Attributes Histogram Visualizer (Image 1 & 4) */}
            <div className="space-y-1.5">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                Tissue Density Attributes
              </div>
              <div className="h-12 bg-navy-900 p-2 rounded-lg border border-navy-800 flex items-end justify-between gap-1">
                {[20, 35, 60, 45, 80, 95, 70, 85, 40, 60, 50, 75, 30].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-cyan-400/80 rounded-t-sm"
                    style={{ height: `${h}%` }}
                  ></div>
                ))}
              </div>
            </div>

            {/* Metadata (Image 1 & 4) */}
            <div className="p-3 rounded-xl bg-navy-900 border border-navy-800 font-mono text-[11px] space-y-1 text-slate-300">
              <div className="text-[10px] uppercase text-slate-500 font-bold">Metadata</div>
              <div className="flex justify-between">
                <span className="text-slate-400">Scan Type:</span>
                <span className="text-white">MRI Axial T1-CE</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Resolution:</span>
                <span className="text-cyan-400">512×512</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Voxel:</span>
                <span className="text-white">0.9mm</span>
              </div>
            </div>

            {/* Summary Counts (Image 1 & 4) */}
            <div className="grid grid-cols-3 gap-2 font-mono text-center">
              <div className="p-2 rounded bg-navy-900 border border-cyan-500/30">
                <div className="text-[9px] text-slate-400">Tumor</div>
                <div className="text-sm font-bold text-cyan-400">1</div>
              </div>
              <div className="p-2 rounded bg-navy-900 border border-emerald-500/30">
                <div className="text-[9px] text-slate-400">Edema</div>
                <div className="text-sm font-bold text-emerald-400">1</div>
              </div>
              <div className="p-2 rounded bg-navy-900 border border-navy-800">
                <div className="text-[9px] text-slate-400">Healthy</div>
                <div className="text-sm font-bold text-slate-400">0</div>
              </div>
            </div>
          </div>

          {/* Official PDF Export Button */}
          {reportData?.pdf_url && (
            <a
              href={getMediaUrl(reportData.pdf_url)}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-teal-400 hover:from-blue-500 hover:to-teal-300 text-navy-950 font-bold text-xs shadow-lg shadow-cyan-950/40 flex items-center justify-center gap-2 transition-all transform hover:scale-[1.01]"
            >
              <Download className="w-4 h-4" />
              <span>Export Official Clinical PDF</span>
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
