/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#18212f",
        mist: "#f5f7fb",
        line: "#d9e0ea",
        action: "#0f9f8f",
      },
      boxShadow: {
        panel: "0 18px 55px rgba(24, 33, 47, 0.08)",
      },
    },
  },
  plugins: [],
};
