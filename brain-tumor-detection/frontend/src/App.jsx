import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import UploadMRI from './pages/UploadMRI';
import MRIEnhancement from './pages/MRIEnhancement';
import DetectionResults from './pages/DetectionResults';
import ScanHistory from './pages/ScanHistory';
import AboutProject from './pages/AboutProject';
import { api } from './services/api';

const VALID_TABS = ['dashboard', 'upload', 'enhance', 'results', 'history', 'about'];

export default function App() {
  const getInitialTab = () => {
    if (typeof window !== 'undefined' && window.location.hash) {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (VALID_TABS.includes(hash)) return hash;
    }
    return 'dashboard';
  };

  const [activeTab, setActiveTabState] = useState(getInitialTab);
  const [currentScan, setCurrentScan] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [backendHealth, setBackendHealth] = useState({ online: false, checking: true });
  const [newScanKey, setNewScanKey] = useState(0);

  const setActiveTab = (tab) => {
    setActiveTabState(tab);
    if (typeof window !== 'undefined' && window.location.hash !== `#${tab}`) {
      window.location.hash = tab;
    }
  };

  // Keep activeTab in sync with browser back/forward buttons and hash navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (VALID_TABS.includes(hash) && hash !== activeTab) {
        setActiveTabState(hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [activeTab]);

  const checkHealthAndStatus = async () => {
    try {
      const health = await api.getHealth();
      setBackendHealth({ online: health?.status === 'success', checking: false });
    } catch (e) {
      setBackendHealth({ online: false, checking: false });
    }

    try {
      const status = await api.getModelStatus();
      setModelStatus(status);
    } catch (err) {
      console.error("Error checking model status:", err);
    }
  };

  // Load model status, backend health, and initial scan on mount
  useEffect(() => {
    async function initStation() {
      await checkHealthAndStatus();

      try {
        const historyData = await api.getHistory();
        const currentHash = window.location.hash.replace('#', '').toLowerCase();
        // Only set initial sample scan if user is NOT on the upload page
        if (currentHash !== 'upload' && historyData?.scans?.length > 0) {
          setCurrentScan(historyData.scans[0]);
        }
      } catch (err) {
        console.error("Error loading initial scan history:", err);
      }
    }
    initStation();

    const timer = setInterval(checkHealthAndStatus, 15000);
    return () => clearInterval(timer);
  }, []);

  const handleScanReady = (scanData) => {
    setCurrentScan(scanData);
  };

  const handleEnhancedReady = (enhancedData) => {
    setCurrentScan(prev => ({
      ...prev,
      ...enhancedData
    }));
  };

  const handleScanUpdated = (updatedScan) => {
    setCurrentScan(updatedScan);
  };

  const handleSelectScan = async (scanId) => {
    try {
      const res = await api.getScanDetails(scanId);
      if (res.scan) {
        setCurrentScan(res.scan);
        setActiveTab('results');
      }
    } catch (err) {
      console.error("Failed to load scan details:", err);
    }
  };

  const handleNewScan = () => {
    setCurrentScan(null);
    setNewScanKey(prev => prev + 1);
    setActiveTab('upload');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-navy-950 text-slate-100 font-sans selection:bg-cyan-400 selection:text-navy-950">
      {/* Left Navigation Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        currentScan={currentScan}
        onNewScan={handleNewScan}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header with Live EEG/ECG Rhythm strip */}
        <Header 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
          modelStatus={modelStatus} 
          backendHealth={backendHealth}
          onNewAnalysis={handleNewScan}
          currentScan={currentScan}
        />

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto workstation-grid">
          {activeTab === 'dashboard' && (
            <Dashboard 
              setActiveTab={setActiveTab} 
              onSelectScan={handleSelectScan} 
              onNewScan={handleNewScan}
            />
          )}

          {activeTab === 'upload' && (
            <UploadMRI 
              key={newScanKey}
              onScanReady={handleScanReady} 
              setActiveTab={setActiveTab} 
            />
          )}

          {activeTab === 'enhance' && (
            <MRIEnhancement 
              currentScan={currentScan} 
              onEnhancedReady={handleEnhancedReady} 
              setActiveTab={setActiveTab} 
            />
          )}

          {activeTab === 'results' && (
            <DetectionResults 
              currentScan={currentScan} 
              onScanUpdated={handleScanUpdated} 
              setActiveTab={setActiveTab} 
            />
          )}

          {activeTab === 'history' && (
            <ScanHistory 
              onSelectScan={handleSelectScan} 
              setActiveTab={setActiveTab} 
            />
          )}

          {activeTab === 'about' && (
            <AboutProject />
          )}
        </main>
      </div>
    </div>
  );
}
