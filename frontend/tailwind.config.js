/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cricket': {
          50: '#fef7ee',
          100: '#fdead7',
          200: '#fbd2ae',
          300: '#f8b17a',
          400: '#f48844',
          500: '#f16820',
          600: '#e25016',
          700: '#bb3a15',
          800: '#952f18',
          900: '#792917',
        },
        'ipl': {
          blue: '#1e40af',
          orange: '#ea580c'
        }
      },
      animation: {
        'bounce-slow': 'bounce 2s infinite',
        'pulse-slow': 'pulse 3s infinite',
      }
    },
  },
  plugins: [],
}