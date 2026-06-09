import React, { useContext } from 'react';
import { motion } from 'framer-motion';
import { PortfolioContext } from '../context/PortfolioContext';

const Research = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.sections_visibility?.research) return null;

  const interests = data.researchInterests?.filter(i => i.visible !== false) || [];

  return (
    <section id="research" className="py-20 px-6 bg-background">
      <div className="max-w-5xl mx-auto">
        <div className="mb-20">
          <p className="font-mono text-[10px] uppercase tracking-[0.4em] text-textPrimary/40 mb-4">Focus Areas // 02</p>
          <h2 className="text-6xl md:text-7xl font-serif text-textPrimary italic">Research Interests</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-x-16 gap-y-12 border-t border-textPrimary/5 pt-12">
          {interests.length > 0 ? interests.map((item, idx) => (
            <motion.div
              key={item.id || idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 1, ease: [0.33, 1, 0.68, 1], delay: idx * 0.1 }}
              className="flex flex-col gap-3 group"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-[10px] text-accent tracking-widest">0{idx + 1} //</span>
                <h3 className="text-2xl font-serif text-textPrimary group-hover:text-accent transition-colors duration-500">{item.topic}</h3>
              </div>
              <p className="text-lg font-sans text-textPrimary/70 leading-relaxed font-light pl-6">
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

export default Research;
