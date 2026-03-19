/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html", // Uygulama içindeki şablonlar için
    "./static/src/**/*.js" // Varsa JavaScript dosyaları için
  ],
  theme: {
    extend: {},
  },
  plugins: [],
} 