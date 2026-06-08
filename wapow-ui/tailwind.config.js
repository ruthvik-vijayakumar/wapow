/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#000000',
        secondary: '#121212',
        accent: '#166dfc'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        franklin: ['Inter', 'sans-serif'],
        archivo: ['Inter', 'sans-serif'],
        postoni: ['Spectral', 'serif'],
        'postoni-display': ['Spectral', 'serif'],
        'postoni-titling': ['Spectral', 'serif'],
        display: ['Spectral', 'serif'],
        spectral: ['Spectral', 'serif'],
        playfair: ['Spectral', 'serif'],
        'playfair-display': ['Spectral', 'serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/aspect-ratio'),
  ],
} 