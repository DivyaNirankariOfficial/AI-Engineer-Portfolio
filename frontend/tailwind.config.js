/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: '#f0ebe0',
        ivoryDeep: '#e8e0d0',
        ivoryDark: '#ddd4c0',
        warmBrown: '#4a433d',
        warmMid: '#756e67',
        warmLight: '#9e9790',
        accent: '#5c4b78',
        accentDeep: '#70506f',
        background: '#f0ebe0',
        textPrimary: '#2b2927', 
        textSecondary: '#5c5956', 
        skillsBg: '#e8e0d0',
        contactBg: '#2b2927', 
        gridLine: 'rgba(0, 0, 0, 0.04)', 
      },
      fontFamily: {
        sans: ['"Cormorant Garamond"', 'serif'], // Primary UI font
        serif: ['"Cormorant Garamond"', 'serif'], // Large Headers
        mono: ['"DM Mono"', 'monospace'], // Code and Badges
        body: ['"Cormorant Garamond"', 'serif'] 
      },
      backgroundImage: {
        'blueprint': 'linear-gradient(to right, rgba(0,0,0,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.03) 1px, transparent 1px)'
      }
    },
  },
  plugins: [],
}
