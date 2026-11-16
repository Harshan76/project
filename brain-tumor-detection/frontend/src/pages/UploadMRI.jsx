import React, { useState, useRef, useEffect } from 'react';
import { 
  UploadCloud, 
  FileCheck, 
  AlertCircle, 
  Image as ImageIcon, 
  Sparkles, 
  CheckCircle2, 
  Info,
  FolderOpen,
  X,
  ArrowRight,
  Clock,
  FileText,
  Activity,
  Layers,
  RefreshCw,
  Sliders,
  HelpCircle,
  Brain
} from 'lucide-react';
import { api, getMediaUrl } from '../services/api';

const MAX_FILE_SIZE_MB = 25;
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp'];

export default function UploadMRI({ onScanReady, setActiveTab }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dimensions, setDimensions] = useState('');
  const [fileSizeText, setFileSizeText] = useState('');
  const [patientId, setPatientId] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [sampleImages, setSampleImages] = useState([]);

  const fileInputRef = useRef(null);

  // Initialize new session ID on mount
  useEffect(() => {
    setPatientId(`P-${Math.floor(10000 + Math.random() * 89999)}`);

    // Load available sample images for presets
    async function loadSamples() {
      try {
        const data = await api.getSampleImages();
        if (data.samples) {
          setSampleImages(data.samples);
        }
      } catch (e) {
        console.error("Could not load sample images:", e);
      }
    }
    loadSamples();
  }, []);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // File validator & preview loader
  const validateAndSetFile = (file) => {
    setError(null);
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    const validExtensions = ['jpg', 'jpeg', 'png', 'bmp'];
    const isImageMime = file.type.startsWith('image/') || ALLOWED_TYPES.includes(file.type);

    if (!validExtensions.includes(ext) || (!isImageMime && file.type)) {
      setError('Invalid file format. Please upload a brain MRI scan in JPG, JPEG, or PNG format.');
      return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`File size exceeds maximum threshold of ${MAX_FILE_SIZE_MB}MB.`);
      return;
    }

    // Format file size
    const sizeStr = file.size > 1024 * 1024 
      ? `${(file.size / (1024 * 1024)).toFixed(2)} MB`
      : `${Math.round(file.size / 1024)} KB`;
    setFileSizeText(sizeStr);

    // Clean previous blob if any
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // Compute dimensions
    const img = new Image();
    img.onload = () => {
      setDimensions(`${img.naturalWidth} × ${img.naturalHeight} px`);
    };
    img.src = objectUrl;
  };

  // Drag and drop event handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  // Browse Files trigger
  const handleBrowseClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  // Select a preset sample MRI
  const handleSelectSample = async (sample) => {
    try {
      setLoading(true);
      setError(null);
      const targetUrl = getMediaUrl(sample.url);
      const response = await fetch(targetUrl);
      if (!response.ok) throw new Error('Preset image download failed');
      const blob = await response.blob();
      const file = new File([blob], sample.filename, { type: 'image/jpeg' });
      validateAndSetFile(file);
    } catch (err) {
      setError('Failed to load sample MRI image: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Remove selected image
  const handleClearScan = (e) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (previewUrl && previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setDimensions('');
    setFileSizeText('');
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Upload and proceed to Enhancement
  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) {
      setError('Please select or drop an MRI image first.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setUploadProgress(20);

      const progressTimer = setInterval(() => {
        setUploadProgress((prev) => (prev < 90 ? prev + 15 : prev));
      }, 100);

      const result = await api.uploadMRI(selectedFile, patientId);
      clearInterval(progressTimer);
      setUploadProgress(100);

      if (onScanReady) {
        onScanReady(result);
      }

      // Transition to Workflow Step 2: MRI Enhancement
      setTimeout(() => {
        if (typeof window !== 'undefined' && window.location.hash !== '#enhance') {
          window.location.hash = 'enhance';
        }
        setActiveTab('enhance');
      }, 350);

    } catch (err) {
      setError(err.message || 'MRI upload failed. Please verify the file and backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">
      {/* Title Breadcrumb & Preset Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-navy-800 pb-3 gap-3">
        <div>
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            <span className="text-cyan-400 font-mono">1.</span>
            <span>MRI Scan Ingestion & Triage Protocol</span>
          </h1>
          <p className="text-[11px] text-slate-400">
            Upload new cranial magnetic resonance imaging slice for automated pre-processing, CNN classification, and Grad-CAM interpretability.
          </p>
        </div>

        {/* 1-Click Samples Quick Switcher */}
        {sampleImages.length > 0 && (
          <div className="flex items-center space-x-1.5 bg-navy-900 p-1.5 rounded-xl border border-navy-800 shrink-0 self-start sm:self-auto">
            <span className="text-[10px] text-slate-400 font-mono px-1">Presets:</span>
            {sampleImages.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectSample(s)}
                className="px-2 py-0.5 rounded text-[10px] font-medium bg-navy-800 hover:bg-cyan-500/20 text-slate-300 hover:text-cyan-300 transition-colors"
                title={`Load ${s.label} preset`}
              >
                {s.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload Card */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-2xl bg-navy-900 border border-navy-800 shadow-2xl space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-cyan-400 font-bold text-xs uppercase tracking-wide">
                <UploadCloud className="w-4 h-4" />
                <span>Upload Brain MRI Scan</span>
              </div>
              <span className="font-mono text-[10px] text-slate-400">
                Session: <strong className="text-cyan-300">{patientId}</strong>
              </span>
            </div>

            {/* Drag & Drop / Preview Box */}
            <div 
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative rounded-2xl overflow-hidden border-2 transition-all duration-200 bg-black min-h-[290px] flex items-center justify-center p-3 ${
                dragActive 
                  ? 'border-cyan-400 bg-cyan-950/20 shadow-lg shadow-cyan-500/20 scale-[1.01]' 
                  : previewUrl 
                    ? 'border-navy-750' 
                    : 'border-dashed border-navy-700 hover:border-cyan-500/50 hover:bg-navy-950/40'
              }`}
            >
              {previewUrl ? (
                /* Preview State */
                <div className="relative group flex flex-col items-center justify-center w-full">
                  <img
                    src={previewUrl}
                    alt="Selected MRI Preview"
                    className="max-h-[260px] w-auto object-contain rounded-lg shadow-xl"
                  />
                  {/* Remove Button in Top Right */}
                  <button
                    onClick={handleClearScan}
                    className="absolute top-1 right-1 px-2.5 py-1 rounded-full bg-red-600/90 hover:bg-red-500 text-white text-[11px] font-semibold flex items-center gap-1 shadow-lg transition-transform hover:scale-105"
                    title="Remove selected image"
                  >
                    <X className="w-3.5 h-3.5 stroke-[2.5]" />
                    <span>Remove</span>
                  </button>
                </div>
              ) : (
                /* Empty Upload Zone */
                <div 
                  onClick={handleBrowseClick}
                  className="flex flex-col items-center justify-center text-center p-6 space-y-3 cursor-pointer w-full group"
                >
                  <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <UploadCloud className="w-7 h-7 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                      Drag & drop your brain MRI scan here
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      or click to browse from your computer
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-slate-400 bg-navy-850 px-2.5 py-1 rounded-full border border-navy-800">
                    <span>JPG</span>
                    <span>•</span>
                    <span>JPEG</span>
                    <span>•</span>
                    <span>PNG</span>
                    <span>•</span>
                    <span>Max 25MB</span>
                  </div>
                </div>
              )}

              {/* Native Accessible File Input (visually hidden via sr-only, interactive for OS dialogs) */}
              <input
                id="mri-file-input"
                ref={fileInputRef}
                type="file"
                accept=".jpg,.jpeg,.png,.bmp"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    validateAndSetFile(e.target.files[0]);
                  }
                  e.target.value = '';
                }}
                className="sr-only"
              />
            </div>

            {/* Selected File Details Bar (when preview is loaded) */}
            {previewUrl && (
              <div className="p-3 rounded-xl bg-navy-950 border border-navy-800 space-y-1 font-mono text-[11px]">
                <div className="flex justify-between items-center text-slate-300">
                  <span className="text-slate-400 truncate max-w-[200px]" title={selectedFile?.name}>
                    {selectedFile?.name || 'mri_scan.jpg'}
                  </span>
                  <span className="text-cyan-400 font-bold">{fileSizeText}</span>
                </div>
                {dimensions && (
                  <div className="flex justify-between items-center text-[10px] text-slate-400 pt-0.5 border-t border-navy-850">
                    <span>Dimensions:</span>
                    <span className="text-slate-200">{dimensions}</span>
                  </div>
                )}
              </div>
            )}

            {/* Upload Progress Bar */}
            {loading && (
              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between text-[10px] font-mono text-cyan-300">
                  <span>Uploading to Clinical Storage...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full h-1.5 bg-navy-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-150 rounded-full"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="space-y-2.5 pt-1">
              {/* Browse Files Button */}
              <button
                type="button"
                onClick={handleBrowseClick}
                className="w-full py-2 px-3 rounded-xl bg-navy-800 hover:bg-navy-750 text-slate-300 hover:text-white text-xs font-semibold border border-navy-700 hover:border-cyan-500/50 transition-colors flex items-center justify-center gap-2"
              >
                <FolderOpen className="w-4 h-4 text-cyan-400" />
                <span>{previewUrl ? 'Choose Different Scan' : 'Browse Files'}</span>
              </button>

              {/* Start Analysis Button */}
              <button
                type="button"
                onClick={handleUploadAndAnalyze}
                disabled={loading || !selectedFile}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-700 via-cyan-600 to-teal-500 hover:from-blue-600 hover:to-teal-400 text-white text-xs font-bold shadow-lg shadow-cyan-900/30 flex items-center justify-center gap-2 transition-all transform hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-cyan-300" />
                    <span>Processing Scan ({uploadProgress}%)...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-cyan-300" />
                    <span>Upload & Start Analysis</span>
                  </>
                )}
              </button>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* 3 Feature Pills Below */}
          <div className="grid grid-cols-3 gap-2.5">
            <div className="p-3 rounded-xl bg-navy-900/90 border border-navy-800 text-center space-y-1">
              <Brain className="w-4 h-4 mx-auto text-cyan-400" />
              <div className="text-[10px] font-bold text-slate-200">Brain MRI Only</div>
            </div>

            <div className="p-3 rounded-xl bg-navy-900/90 border border-navy-800 text-center space-y-1">
              <Clock className="w-4 h-4 mx-auto text-cyan-400" />
              <div className="text-[10px] font-bold text-slate-200">Fast Results</div>
            </div>

            <div className="p-3 rounded-xl bg-navy-900/90 border border-navy-800 text-center space-y-1">
              <FileText className="w-4 h-4 mx-auto text-cyan-400" />
              <div className="text-[10px] font-bold text-slate-200">Detailed Reports</div>
            </div>
          </div>
        </div>

        {/* Right Column: Clinical Assessment & Observations */}
        <div className="lg:col-span-7 space-y-4">
          {/* Disclaimer Banner */}
          <div className="p-3.5 rounded-xl bg-cyan-950/30 border border-cyan-500/25 text-xs text-cyan-200/90 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <p className="text-[11px] leading-relaxed">
              <strong>Disclaimer:</strong> This analysis is for workflow and educational support only and does not constitute medical diagnosis or advice.
            </p>
          </div>

          {/* Workflow Sequence Guide */}
          <div className="p-4 rounded-xl bg-navy-900 border border-navy-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-white">
              <div className="flex items-center gap-1.5 text-cyan-400">
                <Sliders className="w-4 h-4" />
                <span>Automated Workflow Pipeline</span>
              </div>
              <span className="text-[10px] font-mono text-slate-400">5-Step Process</span>
            </div>
            <div className="grid grid-cols-5 gap-1.5 pt-1 text-[10px] font-mono text-center">
              <div className="p-2 rounded bg-cyan-500/20 border border-cyan-400 text-cyan-300 font-bold">
                1. Upload
              </div>
              <div className="p-2 rounded bg-navy-850 border border-navy-750 text-slate-400">
                2. Enhance
              </div>
              <div className="p-2 rounded bg-navy-850 border border-navy-750 text-slate-400">
                3. Classify
              </div>
              <div className="p-2 rounded bg-navy-850 border border-navy-750 text-slate-400">
                4. Grad-CAM
              </div>
              <div className="p-2 rounded bg-navy-850 border border-navy-750 text-slate-400">
                5. Report
              </div>
            </div>
          </div>

          {/* Workflow Priority Card */}
          <div className="p-4 rounded-xl bg-red-950/25 border border-red-500/30 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-red-400 font-bold text-xs">
                <Activity className="w-4 h-4" />
                <span>Workflow Priority</span>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-600 text-white tracking-wide">
                High
              </span>
            </div>
            <p className="text-[11px] text-red-200/90 leading-relaxed">
              The presence of a large, space-occupying feature with contrast enhancement and evident mass effect on adjacent brain structures warrants immediate review.
            </p>
          </div>

          {/* Image Quality Assessment Card */}
          <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-3.5 shadow-xl">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-xs">
              <CheckCircle2 className="w-4 h-4" />
              <span>Image Quality Assessment</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
              {/* Scan Clarity */}
              <div className="p-3.5 rounded-xl bg-navy-850 border border-navy-750 space-y-1">
                <span className="font-semibold text-white text-[11px] block">Scan Clarity</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Clear — The image provides sharp delineation of gray and white matter, as well as the observed anomaly.
                </p>
              </div>

              {/* Contrast */}
              <div className="p-3.5 rounded-xl bg-navy-850 border border-navy-750 space-y-1">
                <span className="font-semibold text-white text-[11px] block">Contrast</span>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Post-contrast T1-weighted image demonstrating robust signal enhancement with clean tissue differentiation.
                </p>
              </div>
            </div>

            {/* Limitations Box */}
            <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/25 space-y-1 text-xs">
              <span className="font-semibold text-amber-300 text-[11px] block">Radiological Limitations</span>
              <ul className="text-[10px] text-amber-200/80 space-y-1 list-disc list-inside">
                <li>This is a single 2D slice; a full multi-sequence 3D volume is recommended for formal volumetric assessment.</li>
                <li>Absence of coregistered DWI/ADC maps limits cellularity estimation.</li>
              </ul>
            </div>
          </div>

          {/* Structural Observations Card */}
          <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-2.5 shadow-xl">
            <div className="flex items-center space-x-2 text-cyan-400 font-bold text-xs">
              <Layers className="w-4 h-4" />
              <span>Structural Observations</span>
            </div>

            <div className="text-xs text-slate-300 space-y-1.5 leading-relaxed">
              <p>
                <strong className="text-white">Asymmetries:</strong> A hyperintense space-occupying lesion is apparent in the cerebral hemisphere with effacement of adjacent sulci and focal mass effect on the ipsilateral lateral ventricle.
              </p>
              <p className="text-slate-400 text-[11px]">
                Preservation of contralateral parenchyma, basal cisterns, and posterior fossa structures observed.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
