import React, { createContext, useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

export const PortfolioContext = createContext();

export const PortfolioProvider = ({ children }) => {
  const [data, setData] = useState({
    profile: {
      name: "Divya Nirankari",
      role: "Software Engineer & AI/ML Engineer",
      email: "dvnirankari@gmail.com",
      phone: "+91 9265768306",
      alternate_phone: "",
      location: "Surat, Gujarat, India",
      summary: "",
      bio: "Python and AI/ML Engineer specializing in Healthcare AI and biomedical signal processing.",
      personal: {
        dob: "1998-01-05",
        gender: "female",
        nationality: "India",
        marital_status: "Single",
        military_service: "No",
        japanese_era_dates: false,
        name_furigana: "ディヴィア・ニランカリ",
        nationality_ja: "インド",
        address_furigana: "インド グジャラート州 スーラト",
        commute_time: "",
        dependents_count: 0,
        has_spouse: false,
        spouse_dependency: false,
        self_pr_ja: "",
        self_pr_ja_detailed: "",
        career_summary_ja: "",
        desired_conditions_ja: "貴社の規定に従います。"
      },
      visa_info: {
        visaType: "",
        visaIssueDate: "",
        visaExpiryDate: ""
      },
      visa: {
        JP: "Requires Engineer / Specialist in Humanities / International Services visa sponsorship",
        KR: "Requires E-7 Specially Designated Activities visa sponsorship",
        CN: "需要工作签证（Z签证），需由用人单位协助办理。",
        CN_EN: "Requires Z-visa sponsorship for employment in China.",
        US: "Requires H-1B visa sponsorship",
        UK: "Requires Skilled Worker visa sponsorship",
        DE: "Eligible for EU Blue Card; requires employer sponsorship",
        AE: "Requires employer-sponsored employment visa",
        IN: "Indian citizen — no visa required",
        GLOBAL: "Relocation sponsorship required"
      },
      github: "https://github.com/DivyaNirankariOfficial",
      github_username: "DivyaNirankariOfficial"
    },
    connections: [],
    about: [],
    stats: {
      card_1_value: "12+",
      card_1_label: "Systems Built",
      card_2_value: "94%",
      card_2_label: "ECG F1-Score",
      card_3_value: "Healthcare AI",
      card_3_label: "Biomedical Signal Processing",
      card_4_value: "AI + Backend",
      card_4_label: "Research to Production"
    },
    skills: [],
    skillCategories: [],
    sections_visibility: {
      about: true,
      skills: true,
      projects: true,
      contact: true,
      experience: true,
      achievements: false,
      activity: false,
      timeline: true,
      exploring: true,
      research: false,
      testimonials: false,
      blog: false
    },
    project_visibility: {},
    currentlyExploring: [],
    experience: [],
    education: [],
    certifications: [],
    achievements: [],
    languages: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Dark mode state removed to stay in Antigravity light theme
  const isDarkMode = false;
  const toggleDarkMode = () => { };

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      // In production, configure API base URL properly (.env)
      const res = await fetch(`${API_BASE_URL}/api/portfolio/`);
      if (!res.ok) throw new Error('Failed to fetch portfolio data');
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      console.error(err);
      setError(err.message);
      // Optional: Add Fallback Data here if backend is completely down
      setData({
        profile: {
          name: "Divya Nirankari",
          role: "Software Engineer & AI/ML Engineer",
          bio: "I build scalable web applications and intelligent machine learning models.",
          github: "https://github.com/DivyaNirankariOfficial",
          linkedin: "https://linkedin.com/in/divya-nirankari",
          email: "dvnirankari@gmail.com"
        },
        about: ["Fallback about section"],
        stats: {
          card_1_value: "12+",
          card_1_label: "Systems Built",
          card_2_value: "94%",
          card_2_label: "ECG F1-Score",
          card_3_value: "Healthcare AI",
          card_3_label: "Biomedical Signal Processing",
          card_4_value: "AI + Backend",
          card_4_label: "Research to Production"
        },
        skills: ["React", "Python", "FastAPI"],
        sections_visibility: { about: true, skills: true, projects: true, contact: true },
        project_visibility: {}
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const updatePortfolio = async (newData) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/portfolio/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newData)
      });
      if (res.ok) {
        setData(newData);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Update failed', err);
      return false;
    }
  };

  return (
    <PortfolioContext.Provider value={{ data, loading, error, setData, updatePortfolio, fetchPortfolio, isDarkMode, toggleDarkMode }}>
      {children}
    </PortfolioContext.Provider>
  );
};
