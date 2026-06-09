import React, { useContext } from 'react';
import { PortfolioContext } from '../context/PortfolioContext';

const ResearchDirection = () => {
  const { data } = useContext(PortfolioContext);
  if (!data || !data.researchNarrative || data.researchNarrative.enabled === false) return null;

  const { title, content } = data.researchNarrative;

  return (
    <section id="research-direction" className="py-20 px-6 bg-background border-t border-textPrimary/5">
      <div className="max-w-4xl mx-auto text-center py-10">
        {title && (
          <p className="font-mono text-[9px] uppercase tracking-[0.3em] text-accent mb-8">
            // {title}
          </p>
        )}
        <p className="text-2xl md:text-3xl font-serif text-textPrimary italic leading-relaxed font-light">
          "{content}"
        </p>
      </div>
    </section>
  );
};

export default ResearchDirection;
