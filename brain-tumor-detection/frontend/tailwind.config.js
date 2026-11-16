/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#050914',
          900: '#070E1A',
          850: '#0B1528',
          800: '#0E1B33',
          750: '#132342',
          700: '#1A2F56',
          600: '#2A467A',
          500: '#41639E',
        },
        workstation: {
          darkest: '#04070F',
          bg: '#060B14',
          panel: '#091220',
          card: '#0D172A',
          border: '#15243E',
          cyan: '#00F2FE',
          teal: '#00D2D3',
          neon: '#00FF9D',
          edema: '#10B981',
          tumor: '#06B6D4',
          ventricle: '#3B82F6',
          purple: '#A855F7',
          magenta: '#EC4899',
          amber: '#F59E0B',
          red: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace']
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'eeg': 'eegScroll 4s linear infinite',
      },
      keyframes: {
        eegScroll: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        }
      }
    },
  },
  plugins: [],
}
