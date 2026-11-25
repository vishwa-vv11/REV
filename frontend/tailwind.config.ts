import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        garage: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          950: "#090d16",
        },
        revGreen: {
          light: "#ecfdf5",
          text: "#065f46",
          border: "#a7f3d0",
          darkBg: "rgba(6, 78, 59, 0.25)",
          darkText: "#6ee7b7",
          darkBorder: "#065f46",
        },
        revAmber: {
          light: "#fffbeb",
          text: "#92400e",
          border: "#fde68a",
          darkBg: "rgba(120, 53, 15, 0.25)",
          darkText: "#fcd34d",
          darkBorder: "#92400e",
        },
        revBlue: {
          light: "#eff6ff",
          text: "#1d4ed8",
          border: "#bfdbfe",
          darkBg: "rgba(30, 58, 138, 0.25)",
          darkText: "#93c5fd",
          darkBorder: "#1e40af",
        },
      },
    },
  },
  plugins: [],
};

export default config;
