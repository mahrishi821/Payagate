/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f8ff',
          100: '#dbeefe',
          200: '#bfe0fd',
          300: '#93cafa',
          400: '#61adf6',
          500: '#3a8fed',
          600: '#256fdf',
          700: '#1e57be',
          800: '#1d4a99',
          900: '#1d3d79'
        }
      }
    }
  },
  plugins: []
}




