const animate = require('tailwindcss-animate')

module.exports = {
  corePlugins: {
    filter: true,
  },
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  plugins: [
    animate,
  ],
}