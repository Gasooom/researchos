/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#18212F",
          soft: "#344054",
        },

        slate: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
        },

        paper: "#F4F6F8",
        signal: {
          DEFAULT: "#167C80",
          soft: "#EFF9F8",
          line: "#B9DDDE",
          dark: "#0F666A",
        },

        review: {
          DEFAULT: "#B7791F",
          soft: "#FFF9EF",
          line: "#E9D3A8",
          dark: "#8A5D14",
        },

        danger: {
          DEFAULT: "#B42318",
          soft: "#FEF3F2",
        },
      },

      fontFamily: {
        sans: [
          "DM Sans",
          "ui-sans-serif",
          "system-ui",
          "sans-serif",
        ],
        prose: [
          "Fraunces",
          "Georgia",
          "serif",
        ],
        mono: [
          "IBM Plex Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Consolas",
          "monospace",
        ],
      },

      boxShadow: {
        subtle:
          "0 1px 2px rgba(15, 23, 42, 0.03)",
      },

      borderRadius: {
        panel: "14px",
        control: "10px",
      },
    },
  },
  plugins: [],
};