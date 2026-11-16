import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Download, 
  RefreshCw, 
  Activity, 
  Sparkles, 
  Eye, 
  RotateCcw, 
  CheckCircle2, 
  Layers, 
  Maximize2,
  AlertCircle
} from 'lucide-react';
import { api, getMediaUrl } from '../services/api';

export default function MRIEnhancement({ currentScan, onEnhancedReady, setActiveTab }) {
  const [params, setParams] = useState({
    clahe_clip_limit: 2.5,
    clahe_grid_size: 8,
    denoise_method: 'bilateral',
    denoise_strength: 7,
    sharpen_strength: 1.2,
    brightness: 5,
    apply_normalization: true
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [enhancedResult, setEnhancedResult] = useState(null);
  const [activeView, setActiveView] = useState('split'); // 'split' | 'enhanced' | 'original' | 'delta'

  useEffect(() => {
    if (currentScan?.enhanced_url) {
      setEnhancedResult({
        enhanced_url: currentScan.enhanced_url,
        comparison_url: currentScan.gradcam_url || currentScan.enhanced_url, // fallback
      });
      if (currentScan.enhancement_params) {
        setParams(prev => ({ ...prev, ...currentScan.enhancement_params }));
      }
    } else {
      setEnhancedResult(null);
      resetParams();
      setError(null);
    }
  }, [currentScan?.scan_id, currentScan?.enhanced_url]);

  const handleApplyEnhancement = async () => {
    if (!currentScan?.scan_id) {
      setError('Please select or upload an MRI scan first.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.enhanceMRI(currentScan.scan_id, params);
      setEnhancedResult(res);
      if (onEnhancedReady) {
        onEnhancedReady(res);
      }
    } catch (err) {
      setError(err.message || 'Enhancement processing failed');
    } finally {
      setLoading(false);
    }
  };

  const resetParams = () => {
    setParams({
      clahe_clip_limit: 2.5,
      clahe_grid_size: 8,
      denoise_method: 'bilateral',
      denoise_strength: 7,
      sharpen_strength: 1.2,
      brightness: 5,
      apply_normalization: true
    });
  };

  if (!currentScan) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center space-y-4">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center">
          <Sliders className="w-8 h-8" />
        </div>
        <h2 className="text-lg font-bold text-white">No MRI Scan Ingested</h2>
        <p className="text-xs text-slate-400 leading-relaxed">
          Please upload a brain MRI scan or select a previous study from history to apply OpenCV digital enhancement.
        </p>
        <button
          onClick={() => setActiveTab('upload')}
          className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-navy-950 font-bold text-xs shadow-md transition-all"
        >
          Go to Upload MRI
        </button>
      </div>
    );
  }

  const originalImageUrl = getMediaUrl(currentScan.file_url || currentScan.original_url);
  const enhancedImageUrl = getMediaUrl(enhancedResult?.enhanced_url);
  const comparisonImageUrl = getMediaUrl(enhancedResult?.comparison_url);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-navy-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            <span>OpenCV MRI Enhancement & Preprocessing Engine</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Active Study: <span className="font-mono text-cyan-300 font-semibold">{currentScan.scan_id}</span> ({currentScan.filename})
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {enhancedImageUrl && (
            <a
              href={enhancedImageUrl}
              download={`${currentScan.scan_id}_enhanced.png`}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-750 text-slate-200 text-xs font-medium border border-navy-700 transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              <span>Download Enhanced</span>
            </a>
          )}
          <button
            onClick={() => setActiveTab('results')}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-navy-950 font-bold text-xs shadow-md transition-all"
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Proceed to AI Classification</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Controls Left, Visualizations Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders and Controls Column */}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-5 shadow-xl">
            <div className="flex items-center justify-between border-b border-navy-800 pb-3">
              <span className="text-xs font-semibold text-white uppercase tracking-wider">
                Filter Parameters
              </span>
              <button
                onClick={resetParams}
                className="text-[11px] text-slate-400 hover:text-cyan-400 flex items-center gap-1 transition-colors"
                title="Reset to default radiological values"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset Defaults</span>
              </button>
            </div>

            {/* CLAHE Clip Limit */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">CLAHE Clip Limit</span>
                <span className="font-mono text-cyan-400 font-semibold">{params.clahe_clip_limit}</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="6.0"
                step="0.1"
                value={params.clahe_clip_limit}
                onChange={(e) => setParams({ ...params, clahe_clip_limit: parseFloat(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-navy-800 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>Gentle (0.5)</span>
                <span>Aggressive (6.0)</span>
              </div>
            </div>

            {/* CLAHE Grid Size */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Adaptive Tile Grid Size</span>
                <span className="font-mono text-cyan-400 font-semibold">{params.clahe_grid_size} × {params.clahe_grid_size}</span>
              </div>
              <input
                type="range"
                min="4"
                max="16"
                step="2"
                value={params.clahe_grid_size}
                onChange={(e) => setParams({ ...params, clahe_grid_size: parseInt(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-navy-800 rounded-lg"
              />
              <div className="flex justify-between text-[10px] text-slate-500">
                <span>Broad (4x4)</span>
                <span>Fine Localized (16x16)</span>
              </div>
            </div>

            {/* Denoising Method */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Noise Filtering Method</label>
              <select
                value={params.denoise_method}
                onChange={(e) => setParams({ ...params, denoise_method: e.target.value })}
                className="w-full px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-700 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-medium"
              >
                <option value="bilateral">Bilateral Filter (Edge-Preserving)</option>
                <option value="nlm">Fast Non-Local Means (Texture-Preserving)</option>
                <option value="gaussian">Gaussian Smoothing</option>
              </select>
            </div>

            {/* Denoising Strength */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Denoising Strength (h / sigma)</span>
                <span className="font-mono text-cyan-400 font-semibold">{params.denoise_strength}</span>
              </div>
              <input
                type="range"
                min="0"
                max="15"
                step="1"
                value={params.denoise_strength}
                onChange={(e) => setParams({ ...params, denoise_strength: parseInt(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-navy-800 rounded-lg"
              />
            </div>

            {/* Sharpening Strength */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Unsharp Mask Sharpening</span>
                <span className="font-mono text-cyan-400 font-semibold">{params.sharpen_strength}x</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="3.0"
                step="0.1"
                value={params.sharpen_strength}
                onChange={(e) => setParams({ ...params, sharpen_strength: parseFloat(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-navy-800 rounded-lg"
              />
            </div>

            {/* Brightness Offset */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 font-medium">Brightness Offset (Beta)</span>
                <span className="font-mono text-cyan-400 font-semibold">{params.brightness > 0 ? `+${params.brightness}` : params.brightness}</span>
              </div>
              <input
                type="range"
                min="-40"
                max="40"
                step="5"
                value={params.brightness}
                onChange={(e) => setParams({ ...params, brightness: parseInt(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer h-1.5 bg-navy-800 rounded-lg"
              />
            </div>

            {/* Normalization Toggle */}
            <div className="pt-2 border-t border-navy-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-slate-200 block">Min-Max Dynamic Range Normalization</span>
                <span className="text-[10px] text-slate-400">Scale intensity strictly to [0, 255]</span>
              </div>
              <input
                type="checkbox"
                checked={params.apply_normalization}
                onChange={(e) => setParams({ ...params, apply_normalization: e.target.checked })}
                className="w-4 h-4 accent-cyan-400 rounded cursor-pointer"
              />
            </div>

            {/* Error Notice */}
            {error && (
              <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Execute Button */}
            <button
              onClick={handleApplyEnhancement}
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-cyan-500 to-cyan-400 hover:from-blue-500 hover:to-cyan-300 disabled:opacity-50 text-navy-950 text-xs font-bold shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all transform hover:scale-[1.01] active:scale-[0.99]"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Computing OpenCV Pipeline...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Execute MRI Enhancement</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Visual Inspection Column (3-Panel Display) */}
        <div className="lg:col-span-8 space-y-4">
          <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-4 shadow-xl">
            {/* View Switcher Tabs */}
            <div className="flex items-center justify-between border-b border-navy-800 pb-3">
              <span className="text-xs font-semibold text-white flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                <span>Radiological Visual Comparison</span>
              </span>

              <div className="flex items-center space-x-1 bg-navy-850 p-1 rounded-lg border border-navy-750 text-xs">
                <button
                  onClick={() => setActiveView('split')}
                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                    activeView === 'split' ? 'bg-cyan-500 text-navy-950 font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  3-Panel Comparison
                </button>
                <button
                  onClick={() => setActiveView('enhanced')}
                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                    activeView === 'enhanced' ? 'bg-cyan-500 text-navy-950 font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Enhanced Only
                </button>
                <button
                  onClick={() => setActiveView('original')}
                  className={`px-2.5 py-1 rounded font-medium transition-colors ${
                    activeView === 'original' ? 'bg-cyan-500 text-navy-950 font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Original Only
                </button>
              </div>
            </div>

            {/* Visualization Rendering Area */}
            {activeView === 'split' ? (
              <div className="space-y-3">
                {/* 3 Images Side by Side */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Panel 1: Original */}
                  <div className="rounded-xl overflow-hidden bg-black border border-navy-800 flex flex-col">
                    <div className="bg-navy-850 px-3 py-1.5 text-[11px] font-semibold text-slate-300 border-b border-navy-800 flex justify-between">
                      <span>1. Original MRI</span>
                      <span className="text-slate-500 font-mono">Raw</span>
                    </div>
                    <div className="p-2 flex items-center justify-center min-h-[220px]">
                      {originalImageUrl ? (
                        <img
                          src={originalImageUrl}
                          alt="Original MRI"
                          className="max-h-[220px] object-contain rounded"
                        />
                      ) : (
                        <span className="text-xs text-slate-600">No original image</span>
                      )}
                    </div>
                  </div>

                  {/* Panel 2: Enhanced */}
                  <div className="rounded-xl overflow-hidden bg-black border border-cyan-500/30 flex flex-col shadow-lg shadow-cyan-950/20">
                    <div className="bg-navy-850 px-3 py-1.5 text-[11px] font-semibold text-cyan-300 border-b border-navy-800 flex justify-between">
                      <span>2. Enhanced MRI</span>
                      <span className="text-cyan-400 font-mono">CLAHE+Denoised</span>
                    </div>
                    <div className="p-2 flex items-center justify-center min-h-[220px]">
                      {enhancedImageUrl ? (
                        <img
                          src={enhancedImageUrl}
                          alt="Enhanced MRI"
                          className="max-h-[220px] object-contain rounded"
                        />
                      ) : (
                        <div className="text-center p-4">
                          <p className="text-xs text-slate-500">Not enhanced yet.</p>
                          <p className="text-[10px] text-cyan-400 mt-1">Click 'Execute MRI Enhancement'</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Panel 3: Comparison / Delta */}
                  <div className="rounded-xl overflow-hidden bg-black border border-navy-800 flex flex-col">
                    <div className="bg-navy-850 px-3 py-1.5 text-[11px] font-semibold text-amber-300 border-b border-navy-800 flex justify-between">
                      <span>3. Contrast Delta</span>
                      <span className="text-amber-400 font-mono">Magma Map</span>
                    </div>
                    <div className="p-2 flex items-center justify-center min-h-[220px]">
                      {comparisonImageUrl ? (
                        <img
                          src={comparisonImageUrl}
                          alt="Comparison MRI"
                          className="max-h-[220px] object-contain rounded"
                        />
                      ) : (
                        <div className="text-center p-4 text-xs text-slate-500">
                          Delta difference map will appear upon execution.
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-navy-850 border border-navy-800 text-[11px] text-slate-400 leading-relaxed flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                  <span>
                    Contrast-Limited Adaptive Histogram Equalization (CLAHE) sharpens subtle boundary contrasts across tissue interfaces without amplifying scanner background noise.
                  </span>
                </div>
              </div>
            ) : activeView === 'enhanced' ? (
              <div className="rounded-xl overflow-hidden bg-black border border-navy-800 p-4 flex flex-col items-center justify-center min-h-[360px]">
                {enhancedImageUrl ? (
                  <img
                    src={enhancedImageUrl}
                    alt="Enhanced High-Res MRI"
                    className="max-h-[380px] object-contain rounded-lg shadow-2xl"
                  />
                ) : (
                  <p className="text-xs text-slate-500">Enhancement not computed yet.</p>
                )}
              </div>
            ) : (
              <div className="rounded-xl overflow-hidden bg-black border border-navy-800 p-4 flex flex-col items-center justify-center min-h-[360px]">
                {originalImageUrl ? (
                  <img
                    src={originalImageUrl}
                    alt="Original High-Res MRI"
                    className="max-h-[380px] object-contain rounded-lg shadow-2xl"
                  />
                ) : (
                  <p className="text-xs text-slate-500">Original image not available.</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
