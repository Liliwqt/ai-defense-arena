/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Mirrors game/src/index.css. The old arena-* palette was unused and
      // misdocumented the real colors.
      colors: {
        "arena-base": "#e9e7e2",
        "arena-deep": "#dcd9d2",
        "arena-ink": "#232220",
        "arena-muted": "#56534e",
        "arena-subtle": "#5f5b54",
        "arena-accent": "#545a8c",
      },
    },
  },
  plugins: [],
};
