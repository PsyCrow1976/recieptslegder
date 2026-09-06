/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f3efe6",
        ink: "#1c1917",
        brand: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          500: "#0d9488",
          600: "#0f766e",
          700: "#115e59",
          900: "#134e4a",
        },
      },
      fontFamily: {
        sans: ["Figtree", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["Fraunces", "ui-serif", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};
