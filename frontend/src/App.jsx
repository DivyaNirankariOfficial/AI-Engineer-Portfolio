import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Home from './pages/Home.jsx';
import SubmitTestimonial from './pages/SubmitTestimonial.jsx';
import CanvasParticles from './components/CanvasParticles.jsx';
import CustomCursor from './components/CustomCursor.jsx';
import ScrollToTop from './components/ScrollToTop.jsx';
import Loader from './components/Loader.jsx';
import NotFound from './pages/NotFound.jsx';

const Admin = lazy(() => import('./pages/Admin.jsx'));


function App() {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const hasShownLoader = sessionStorage.getItem('intro_shown');
    if (!hasShownLoader) {
      setLoading(true);
      sessionStorage.setItem('intro_shown', 'true');
    }
  }, []);

  return (
    <>
      <AnimatePresence>
        {loading && <Loader onComplete={() => setLoading(false)} />}
      </AnimatePresence>
      
      {!loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <CustomCursor />
          <ScrollToTop />
          <CanvasParticles />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/admin" element={
              <Suspense fallback={<div className="h-screen flex items-center justify-center font-mono text-xs uppercase tracking-widest opacity-30">Loading Secure Core...</div>}>
                <Admin />
              </Suspense>
            } />
            <Route path="/submit-testimonial" element={<SubmitTestimonial />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </motion.div>
      )}
    </>
  );
}

export default App;
