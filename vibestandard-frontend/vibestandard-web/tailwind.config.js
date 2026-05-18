/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        accent: "rgba(98, 251, 152, 1)",
        "accent-dim": "rgba(98, 251, 152, 0.1)",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        mono: ["Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};
