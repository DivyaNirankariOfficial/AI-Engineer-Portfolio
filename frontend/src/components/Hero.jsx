import React, { useContext, useState, useEffect, Suspense, lazy } from 'react';
import { API_BASE_URL } from '../config';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';
import { GithubIcon, LinkedinIcon, Download } from 'lucide-react';
import { useTypewriter } from '../hooks/useTypewriter';

const HeroCanvas = lazy(() => import('./HeroCanvas'));


const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 1.2, ease: [0.33, 1, 0.68, 1] }
  }
};

const Hero = () => {
  const { data } = useContext(PortfolioContext);
  const [downloadState, setDownloadState] = useState('idle'); // 'idle' | 'preparing'
  const titles = data?.profile?.titles || [
    "Artificial Intelligence",
    "NeuroAI",
    "Healthcare AI",
    "Robotics",
    "Intelligent Systems"
  ];
  const typewriterText = useTypewriter(titles);

  const downloadUrl = `${API_BASE_URL}/api/resume/download?download=true`;

  const handleDownload = async (e) => {
    e.preventDefault();
    if (downloadState !== 'idle') return;
    setDownloadState('preparing');
    try {
      const response = await fetch(downloadUrl);
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Determine file name from Content-Disposition if possible
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'divya_nirankari_resume.pdf';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/) || contentDisposition.match(/filename="?([^;"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = decodeURIComponent(filenameMatch[1]);
        }
      }
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download resume. Please try again.');
    } finally {
      setDownloadState('idle');
    }
  };

  if (!data) return <div className="min-h-[80vh] flex items-center justify-center">Loading...</div>;
  const { profile } = data;


  return (
    <section className="min-h-screen flex flex-col pt-[20vh] relative overflow-hidden bg-background px-6" id="hero">
      {/* Structural Editorial Lines - Removed to avoid visual collisions */}

      {/* 3D Background */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
        {data.settings?.hero3d !== false && (
          <Suspense fallback={null}>
            <HeroCanvas />
          </Suspense>
        )}
      </div>

      <motion.div
        className="max-w-5xl mx-auto relative z-10 w-full"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div variants={itemVariants} className="mb-10">
          <div className="flex items-center gap-4">
            <span className="w-12 h-px bg-textPrimary/10"></span>
            <div className="flex items-center gap-3 bg-emerald-500/5 px-4 py-1.5 border border-emerald-500/10">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <p className="font-mono text-emerald-700/80 uppercase tracking-[0.3em] text-[10px] font-medium">
                Active: {data.experience?.find(e => e.endDate === "Present")?.role || "Synthesizing Systems"}
              </p>
            </div>
          </div>
        </motion.div>

        <h1 className="text-[12vw] md:text-[8vw] font-serif font-medium text-textPrimary leading-[1] tracking-tighter mb-8 italic">
          {profile.name}
        </h1>

        <div className="grid md:grid-cols-2 gap-12 items-baseline border-t border-textPrimary/5 pt-12">
          <motion.div variants={itemVariants} className="flex flex-col gap-6">
            <div className="w-24 h-px bg-accent/30" />
            <h2 className="text-3xl md:text-5xl font-serif text-textPrimary leading-tight min-h-[3.6rem] md:min-h-[6rem]">
              - {typewriterText}
            </h2>
          </motion.div>

          <motion.div variants={itemVariants} className="flex flex-col gap-8">
            <div className="w-full h-px bg-textPrimary/5" />
            <p className="text-xl md:text-2xl font-sans text-textPrimary opacity-80 leading-relaxed font-light">
               {profile.bio}
            </p>

            <div className="flex flex-col lg:flex-row lg:items-center gap-8 pt-4 w-full">
              <a href="#projects" className="group flex items-center gap-4 font-mono text-xs uppercase tracking-[0.2em] text-textPrimary whitespace-nowrap">
                <span className="w-12 h-px bg-textPrimary transition-all duration-500"></span>
                Explore Work
              </a>

                <div className="flex items-center gap-4">
                  {(data.connections || [])
                    .filter(c => c.visible !== false && c.platform !== 'Email')
                    .slice(0, 4) // Show top 4 signals in Hero
                    .map((conn, idx) => {
                      const Icon = {
                        'github': GithubIcon,
                        'linkedin': LinkedinIcon,
                        'youtube': (props) => (
                          <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-youtube">
                            <path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 2-2h15a2 2 0 0 1 2 2 24.12 24.12 0 0 1 0 10 2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2Z"/><path d="m10 15 5-3-5-3z"/>
                          </svg>
                        ),
                        'instagram': (props) => (
                          <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-instagram">
                            <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" x2="17.51" y1="6.5" y2="6.51"/>
                          </svg>
                        )
                      }[conn.platform.toLowerCase()] || GithubIcon; // Fallback to Github icon or similar

                      return (
                        <a 
                          key={idx} 
                          href={conn.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          title={conn.platform}
                          className="text-textPrimary/60 hover:text-textPrimary transition-all duration-300 hover:-translate-y-1"
                        >
                          <Icon size={18} />
                        </a>
                      );
                    })}
                </div>
                {/* Auto-Detecting Resume Download */}
                  <button
                    onClick={handleDownload}
                    disabled={downloadState !== 'idle'}
                    className="flex items-center gap-4 bg-textPrimary text-white px-8 py-5 hover:bg-accent transition-all duration-500 group whitespace-nowrap rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {downloadState === 'idle' ? (
                      <>
                        <Download size={16} />
                        <span className="font-mono text-xs uppercase tracking-[0.2em]">Resume</span>
                      </>
                    ) : (
                      <>
                        <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span className="font-mono text-xs uppercase tracking-[0.2em]">Preparing Resume...</span>
                      </>
                    )}
                  </button>
              </div>
          </motion.div>
        </div>
      </motion.div>

      {/* Signature Bobbing Anchor - Removed to prevent collisions with UI elements */}
    </section>
  );
};

export default Hero;
