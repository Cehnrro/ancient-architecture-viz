/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 国风暗色主题色板
        'ink': '#0d1117',
        'ink-light': '#161b22',
        'gold': '#c9a84c',
        'gold-light': '#e8c96d',
        'cyan-glow': '#00d4ff',
        'red-ancient': '#8b1a1a',
        'jade': '#2d6a4f',
      },
      fontFamily: {
        'serif-cn': ['Noto Serif SC', 'serif'],
      }
    },
  },
  plugins: [],
}
