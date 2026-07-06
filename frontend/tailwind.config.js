/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'anthro-bg': '#FAF9F7',
        'anthro-surface': '#FDFCF6',
        'anthro-text-heading': '#1A1916',
        'anthro-text-body': '#4A4946',
        'anthro-text-muted': '#8A8886',
        'anthro-border': '#E5E3E0',
        'anthro-hover': '#F5F3F0',
        'anthro-accent': '#D97706',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Crimson Pro', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
