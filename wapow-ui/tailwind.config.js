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
        sans: ['Archivo', 'sans-serif'],
        franklin: ['Archivo', 'sans-serif'],
        archivo: ['Archivo', 'sans-serif'],
        postoni: ['Saira Extra Condensed', 'sans-serif'],
        'postoni-display': ['Saira Extra Condensed', 'sans-serif'],
        'postoni-titling': ['Saira Extra Condensed', 'sans-serif'],
        display: ['Saira Extra Condensed', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/aspect-ratio'),
  ],
} 