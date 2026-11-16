import React from 'react';
import { 
  Info, 
  Brain, 
  Sliders, 
  Activity, 
  ShieldCheck, 
  Code2, 
  Database, 
  CheckCircle2,
  Terminal,
  Cpu,
  Layers,
  Sparkles
} from 'lucide-react';

export default function AboutProject() {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Title Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-navy-900 via-navy-850 to-navy-900 border border-navy-800 shadow-xl space-y-3">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-[11px] font-medium">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Academic Project Demonstration</span>
        </div>
        <h1 className="text-2xl font-black text-white tracking-tight">
          Generative AI-Assisted Brain Tumor Detection with MRI Enhancement
        </h1>
        <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
          An end-to-end full-stack medical intelligence system that synergizes computer vision (OpenCV) 
          and deep convolutional neural networks (TensorFlow/Keras) with Grad-CAM explainability to assist 
          in cranial MRI contrast enhancement, differential tumor categorization, and automated diagnostic reporting.
        </p>
      </div>

      {/* 3 Core Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Pillar 1 */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-3 shadow-md">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
            <Sliders className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white">1. OpenCV Enhancement</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Genuine image-processing pipeline applying Contrast Limited Adaptive Histogram Equalization (CLAHE) in LAB space, 
            edge-preserving bilateral noise reduction, and unsharp masking to amplify soft tissue demarcation.
          </p>
        </div>

        {/* Pillar 2 */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-3 shadow-md">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <Brain className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white">2. CNN Classification</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Deep Convolutional Neural Network trained on the benchmark Kaggle Brain Tumor MRI dataset to classify scans into 4 canonical categories: 
            Glioma, Meningioma, Pituitary Tumor, and No Tumor (Healthy).
          </p>
        </div>

        {/* Pillar 3 */}
        <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 space-y-3 shadow-md">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Activity className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-white">3. Explainable AI (Grad-CAM)</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Gradient-weighted Class Activation Mapping calculates the gradients of the target class score relative to final convolutional feature maps, 
            generating an attention heatmap to expose regions driving the model's prediction.
          </p>
        </div>
      </div>

      {/* Technical Specifications Table */}
      <div className="p-6 rounded-2xl bg-navy-900 border border-navy-800 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-navy-800 pb-3">
          <Code2 className="w-4 h-4 text-cyan-400" />
          <span>System Architecture & Technologies</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-navy-850 border border-navy-800 space-y-2">
            <span className="font-semibold text-cyan-300 block">Frontend Technologies</span>
            <ul className="space-y-1.5 text-slate-300">
              <li>• <strong>Framework:</strong> React.js 18 with Vite bundling</li>
              <li>• <strong>Styling:</strong> Tailwind CSS (Dark Navy & Medical Cyan theme)</li>
              <li>• <strong>Visualizations:</strong> Recharts (Interactive Area, Bar, and Donut charts)</li>
              <li>• <strong>Icons:</strong> Lucide React</li>
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-navy-850 border border-navy-800 space-y-2">
            <span className="font-semibold text-cyan-300 block">Backend & ML Infrastructure</span>
            <ul className="space-y-1.5 text-slate-300">
              <li>• <strong>Server:</strong> Python Flask REST APIs with CORS</li>
              <li>• <strong>Deep Learning:</strong> TensorFlow 2.x & Keras (MobileNetV2 / Conv2D)</li>
              <li>• <strong>Computer Vision:</strong> OpenCV (cv2) & NumPy</li>
              <li>• <strong>Database:</strong> SQLite with indexed metadata persistence</li>
              <li>• <strong>Report Engine:</strong> ReportLab vector PDF compilation</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Dataset & Classification Details */}
      <div className="p-6 rounded-2xl bg-navy-900 border border-navy-800 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-navy-800 pb-3">
          <Database className="w-4 h-4 text-cyan-400" />
          <span>Target Pathologies & Dataset Structure</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-navy-850 border border-red-500/20 space-y-1">
            <div className="font-bold text-red-400">Glioma</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Intra-axial infiltrative glial tumor. Often shows heterogeneous signal and peritumoral edema on T2/FLAIR.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850 border border-amber-500/20 space-y-1">
            <div className="font-bold text-amber-400">Meningioma</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Extra-axial dural-based mass originating from arachnoid cap cells. Exhibits uniform enhancement & dural tail sign.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850 border border-purple-500/20 space-y-1">
            <div className="font-bold text-purple-400">Pituitary Tumor</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Sellar and suprasellar adenoma. Causes remodeling of sella turcica and potential chiasmatic compression.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-navy-850 border border-emerald-500/20 space-y-1">
            <div className="font-bold text-emerald-400">No Tumor</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Normal cranial parenchyma with symmetric cortical architecture, baseline ventricles, and no space-occupying lesion.
            </p>
          </div>
        </div>
      </div>

      {/* College Project Instructions Banner */}
      <div className="p-5 rounded-2xl bg-navy-850 border border-navy-750 space-y-3">
        <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span>Execution Commands for Demonstration</span>
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-[11px]">
          <div className="p-3 rounded-lg bg-navy-950 border border-navy-800 text-slate-300 space-y-1">
            <span className="text-slate-500 block text-[10px]">Backend Server (Port 5000):</span>
            <span className="text-cyan-300">cd brain-tumor-detection/backend</span><br/>
            <span className="text-cyan-300">python app.py</span>
          </div>
          <div className="p-3 rounded-lg bg-navy-950 border border-navy-800 text-slate-300 space-y-1">
            <span className="text-slate-500 block text-[10px]">Frontend UI (Port 3000):</span>
            <span className="text-cyan-300">cd brain-tumor-detection/frontend</span><br/>
            <span className="text-cyan-300">npm run dev</span>
          </div>
        </div>
      </div>

      {/* Statutory Clinical Disclaimer */}
      <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 text-[11px] text-red-200/90 leading-relaxed flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        <div>
          <strong>Statutory Academic Notice:</strong> This software is engineered as a demonstration and research prototype.
          It is not cleared by FDA, CE-MDR, or equivalent medical device authorities.
          Predictions and Grad-CAM activations are intended for investigational support and must never replace clinical judgment by certified radiologists.
        </div>
      </div>
    </div>
  );
}
