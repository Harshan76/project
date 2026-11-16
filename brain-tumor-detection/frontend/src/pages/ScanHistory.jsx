import React, { useState, useEffect } from 'react';
import { 
  History, 
  Search, 
  Filter, 
  Trash2, 
  ExternalLink, 
  FileText, 
  Download, 
  RefreshCw, 
  AlertCircle,
  CheckCircle2,
  Calendar,
  Layers,
  Brain
} from 'lucide-react';
import { api, getMediaUrl } from '../services/api';

const CATEGORIES = ['All', 'Glioma', 'Meningioma', 'Pituitary Tumor', 'No Tumor'];

export default function ScanHistory({ onSelectScan, setActiveTab }) {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [deleteModalScan, setDeleteModalScan] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getHistory(selectedCategory, search);
      setScans(data.scans || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch scan history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [selectedCategory]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadHistory();
  };

  const confirmDelete = async () => {
    if (!deleteModalScan) return;
    try {
      setDeleting(true);
      await api.deleteScan(deleteModalScan.scan_id);
      setScans(scans.filter(s => s.scan_id !== deleteModalScan.scan_id));
      setDeleteModalScan(null);
    } catch (err) {
      alert('Delete failed: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-navy-800 pb-5">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-cyan-400" />
            <span>Brain MRI Scan Archival Registry</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete database of past MRI studies, enhancement parameters, classifications, and clinical reports.
          </p>
        </div>

        <button
          onClick={loadHistory}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-navy-850 hover:bg-navy-800 text-slate-300 text-xs font-medium border border-navy-750 transition-colors self-start md:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Database</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-xl bg-navy-900 border border-navy-800 flex flex-col md:flex-row items-center justify-between gap-4 shadow-md">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Scan ID or Subject..."
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-navy-800 border border-navy-700 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono transition-colors"
          />
        </form>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
          <Filter className="w-3.5 h-3.5 text-slate-500 mr-1 hidden sm:inline" />
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-cyan-500 text-navy-950 font-bold shadow-md'
                  : 'bg-navy-800 text-slate-400 hover:text-slate-200 hover:bg-navy-750'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Scans Table */}
      <div className="p-5 rounded-2xl bg-navy-900 border border-navy-800 shadow-xl overflow-hidden">
        {loading ? (
          <div className="py-16 text-center space-y-3">
            <RefreshCw className="w-7 h-7 text-cyan-400 animate-spin mx-auto" />
            <p className="text-xs text-slate-400 font-medium">Querying SQLite records...</p>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : scans.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-navy-800 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-3">Thumbnail</th>
                  <th className="py-3 px-3">Scan Reference</th>
                  <th className="py-3 px-3">Patient ID</th>
                  <th className="py-3 px-3">Classification</th>
                  <th className="py-3 px-3">Confidence</th>
                  <th className="py-3 px-3">Date</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800 text-xs">
                {scans.map((scan) => (
                  <tr key={scan.scan_id} className="hover:bg-navy-850/60 transition-colors">
                    {/* Thumbnail */}
                    <td className="py-2.5 px-3">
                      <div className="w-12 h-12 rounded-lg bg-black border border-navy-700 overflow-hidden flex items-center justify-center">
                        {scan.original_url ? (
                          <img
                            src={getMediaUrl(scan.enhanced_url || scan.original_url)}
                            alt="Scan Thumbnail"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <Brain className="w-5 h-5 text-slate-600" />
                        )}
                      </div>
                    </td>

                    {/* Scan ID & Filename */}
                    <td className="py-2.5 px-3">
                      <div className="font-mono font-semibold text-cyan-300">{scan.scan_id}</div>
                      <div className="text-[11px] text-slate-400 truncate max-w-[170px]" title={scan.filename}>
                        {scan.filename}
                      </div>
                    </td>

                    {/* Patient ID */}
                    <td className="py-2.5 px-3 font-mono text-slate-300">
                      {scan.patient_id || 'ANON'}
                    </td>

                    {/* Classification */}
                    <td className="py-2.5 px-3">
                      {scan.predicted_category ? (
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${
                          scan.predicted_category === 'Glioma' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                          scan.predicted_category === 'Meningioma' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          scan.predicted_category === 'Pituitary Tumor' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                          'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        }`}>
                          {scan.predicted_category}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic text-[11px]">Unclassified</span>
                      )}
                    </td>

                    {/* Confidence */}
                    <td className="py-2.5 px-3 font-mono">
                      {scan.confidence_score ? (
                        <span className="font-bold text-slate-200">{scan.confidence_score}%</span>
                      ) : (
                        <span className="text-slate-500">-</span>
                      )}
                    </td>

                    {/* Date */}
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {scan.created_at ? scan.created_at.slice(0, 16).replace('T', ' ') : 'N/A'}
                    </td>

                    {/* Actions */}
                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Open Analysis */}
                        <button
                          onClick={() => onSelectScan(scan.scan_id)}
                          className="p-1.5 rounded-lg bg-navy-800 hover:bg-cyan-500/20 hover:text-cyan-300 text-slate-300 transition-colors"
                          title="Open Analysis View"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </button>

                        {/* PDF Download */}
                        {scan.pdf_url && (
                          <a
                            href={getMediaUrl(scan.pdf_url)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 rounded-lg bg-navy-800 hover:bg-blue-500/20 hover:text-blue-300 text-slate-300 transition-colors"
                            title="Download Clinical PDF Report"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                        )}

                        {/* Delete */}
                        <button
                          onClick={() => setDeleteModalScan(scan)}
                          className="p-1.5 rounded-lg bg-navy-800 hover:bg-red-500/20 hover:text-red-400 text-slate-400 transition-colors"
                          title="Delete Record"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-16 text-center space-y-3">
            <Brain className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-xs text-slate-400 font-medium">No records found matching current query.</p>
            <button
              onClick={() => setActiveTab('upload')}
              className="text-xs text-cyan-400 hover:underline"
            >
              Upload and analyze a new MRI
            </button>
          </div>
        )}
      </div>

      {/* Confirmation Modal for Deletion */}
      {deleteModalScan && (
        <div className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-navy-900 border border-navy-750 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-3 text-red-400">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <Trash2 className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base">Confirm Permanent Deletion</h3>
            </div>
            
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to permanently delete scan{' '}
              <span className="font-mono text-cyan-300 font-bold">{deleteModalScan.scan_id}</span>? 
              This will remove the SQLite database entry and purge all associated files (uploaded MRI, enhanced image, Grad-CAM heatmap, and PDF report).
            </p>

            <div className="flex justify-end space-x-3 pt-3 border-t border-navy-800">
              <button
                onClick={() => setDeleteModalScan(null)}
                disabled={deleting}
                className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-750 text-slate-300 text-xs font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold shadow-md shadow-red-900/30 transition-colors flex items-center gap-2"
              >
                {deleting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : null}
                <span>Delete Permanently</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
