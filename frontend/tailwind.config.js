/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 美食主题暖色调
        'food-primary': '#ff6b35',      // 橙红色
        'food-secondary': '#f7c59f',    // 浅橙色
        'food-accent': '#d62828',       // 深红色
        'food-bg': '#fef5f0',          // 米白色背景
        'food-text': '#2d2d2d',        // 深灰色文字
      },
      fontFamily: {
        'food': ['PingFang SC', 'Microsoft YaHei', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
