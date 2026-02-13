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
        sans: ['Franklin ITC Pro', 'sans-serif'],
        franklin: ['Franklin ITC Pro', 'sans-serif'],
        postoni: ['Postoni', 'serif'],
        'postoni-display': ['Postoni Display', 'serif'],
        'postoni-titling': ['Postoni Titling', 'serif'],
      },
    },
  },
  plugins: [
    require('@tailwindcss/aspect-ratio'),
  ],
} 