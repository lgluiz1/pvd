/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        darkBg: '#0f172a',
        darkCard: '#1e293b',
        accentBlue: '#3b82f6',
        accentGreen: '#10b981',
        accentRed: '#ef4444',
      }
    }
  },
  plugins: [],
}
