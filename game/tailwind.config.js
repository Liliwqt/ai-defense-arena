/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "arena-bg": "#091322",
        "arena-surface": "#0c1b2d",
        "arena-border": "#2b4663",
        "arena-accent": "#50b6ee",
      },
    },
  },
  plugins: [],
};
