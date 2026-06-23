import React, { useEffect, useState, useContext } from 'react';
import { API_BASE_URL } from '../config';
import { motion, AnimatePresence } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const HeatmapSkeleton = () => {
  return (
    <div className="w-full max-w-[800px] animate-pulse">
      <div className="flex justify-between items-center mb-8">
        <div className="h-5 bg-textPrimary/10 w-1/3 rounded" />
        <div className="flex items-center gap-2">
          <div className="h-3 bg-textPrimary/5 w-8 rounded" />
          {[1, 2, 3, 4, 5].map((n) => (
            <div key={n} className="w-3 h-3 bg-textPrimary/10 rounded-[2px]" />
          ))}
          <div className="h-3 bg-textPrimary/5 w-8 rounded" />
        </div>
      </div>

      <div className="flex">
        <div className="flex flex-col gap-[9px] pr-4 pt-6">
          <div className="h-2.5 bg-textPrimary/5 w-6 rounded" />
          <div className="h-2.5 bg-textPrimary/5 w-6 rounded" />
          <div className="h-2.5 bg-textPrimary/5 w-6 rounded" />
        </div>
        
        <div className="flex-1">
          <div className="flex mb-3 justify-between">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="h-3 bg-textPrimary/5 rounded w-8" />
            ))}
          </div>
          
          <div className="flex gap-[3px] overflow-hidden">
            {[...Array(53)].map((_, wIdx) => (
              <div key={wIdx} className="flex flex-col gap-[3px]">
                {[...Array(7)].map((_, dIdx) => (
                  <div
                    key={dIdx}
                    className="w-[11px] h-[11px] rounded-[2px] bg-textPrimary/5 skeleton-shimmer"
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const ActivityHeatmap = () => {
  const { data: portfolioData } = useContext(PortfolioContext);
  const [contributions, setContributions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hoveredDay, setHoveredDay] = useState(null);

  useEffect(() => {
    // Fetch contributions immediately on mount (defaults to profile user on backend)
    fetch(`${API_BASE_URL}/api/platform/github/contributions/`)
      .then(res => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(data => {
        setContributions(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (!portfolioData || !portfolioData.sections_visibility?.activity) return null;

  const colors = {
    0: "#e8e0d0", 
    1: "#d4c9b0",
    2: "#b5a890",
    3: "#9a7a55",
    4: "#5a4a35"
  };

  const getColor = (count) => {
    if (count === 0) return colors[0];
    if (count <= 3) return colors[1];
    if (count <= 6) return colors[2];
    if (count <= 9) return colors[3];
    return colors[4];
  };

  const monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  return (
    <section id="activity" className="py-16 px-6 bg-ivory">
      <div className="max-w-6xl mx-auto">
        <div className="mb-16">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-warmBrown mb-4 text-center">Open Source Activity // 02</p>
          <h2 className="text-5xl md:text-6xl font-serif text-textPrimary text-center italic">Code Pulse</h2>
        </div>

        <div 
          className="bg-ivory p-4 md:p-8 overflow-hidden relative w-full flex justify-center border border-textPrimary/5"
        >
          {loading ? (
            <HeatmapSkeleton />
          ) : contributions?.weeks ? (
            <div className="w-full max-w-[800px]">
              <div className="flex justify-between items-center mb-8">
                <p className="font-mono text-xs text-textPrimary">
                  <span className="text-accent font-bold text-lg mr-2">{contributions.totalContributions}</span> 
                  contributions in the last year
                </p>
                <div className="flex items-center gap-2 text-[10px] font-mono text-warmBrown">
                  <span>Less</span>
                  {[0, 1, 4, 7, 10].map(v => (
                    <div key={v} className="w-3 h-3 rounded-[2px]" style={{ backgroundColor: getColor(v) }} />
                  ))}
                  <span>More</span>
                </div>
              </div>

              <div className="flex">
                <div className="flex flex-col gap-[7px] pr-4 pt-6 text-[9px] font-mono text-warmBrown">
                  <span>Mon</span>
                  <span>Wed</span>
                  <span>Fri</span>
                </div>
                
                <div className="flex-1">
                  <div className="flex mb-2 text-[9px] font-mono text-warmBrown justify-between">
                    {monthLabels.map((m, i) => (
                      <span key={i} className="w-8 text-center">{m}</span>
                    ))}
                  </div>
                  
                  <div className="flex gap-[3px] overflow-x-auto">
                    {contributions.weeks.map((week, wIdx) => (
                      <div key={wIdx} className="flex flex-col gap-[3px]">
                        {week.contributionDays.map((day, dIdx) => (
                          <div
                            key={dIdx}
                            className="w-[11px] h-[11px] rounded-[2px] cursor-crosshair transition-all duration-300 hover:scale-125"
                            style={{ backgroundColor: getColor(day.contributionCount) }}
                            onMouseEnter={(e) => setHoveredDay({ ...day, x: e.clientX, y: e.clientY })}
                            onMouseLeave={() => setHoveredDay(null)}
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
             <div className="h-40 flex items-center justify-center font-mono text-sm text-red-500">
              Unable to fetch contribution data.
            </div>
          )}

          <AnimatePresence>
            {hoveredDay && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                style={{ left: hoveredDay.x - 40, top: hoveredDay.y - 60 }}
                className="fixed z-50 pointer-events-none bg-warmBlack text-ivory text-[10px] font-mono py-2 px-3 rounded shadow-xl whitespace-nowrap"
              >
                {hoveredDay.contributionCount} contributions on {new Date(hoveredDay.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
};

export default ActivityHeatmap;
