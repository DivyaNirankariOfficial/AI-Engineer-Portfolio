import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const CurrentlyExploring = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.exploring) return null;

  const explorations = (data.currentlyExploring || []).filter(item => item.visible !== false);

  return (
    <section id="exploring" className="py-20 px-6 bg-background border-t border-textPrimary/5">
      <div className="max-w-5xl mx-auto">
        <div className="mb-20">
          <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic">Currently Exploring</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-12">
          {explorations.length > 0 ? explorations.map((item, idx) => (
            <motion.div
              key={item.id || idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 1, ease: [0.33, 1, 0.68, 1], delay: idx * 0.1 }}
              className="flex flex-col gap-3 group"
            >
              <h3 className="text-2xl font-serif text-textPrimary group-hover:text-accent transition-colors duration-500">{item.theme}</h3>
              <p className="text-lg font-sans text-textPrimary/70 leading-relaxed font-light">
                {item.description}
              </p>
            </motion.div>
          )) : (
            <p className="font-mono text-sm text-textPrimary/30 italic">Exploring new horizons...</p>
          )}
        </div>
      </div>
    </section>
  );
};

export default CurrentlyExploring;
