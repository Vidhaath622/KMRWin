import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "var(--font-sans)",
          "var(--font-deva)",
          "var(--font-guj)",
          "system-ui",
          "sans-serif",
        ],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        // "Indelible ink" violet: the mark every Indian voter carries home.
        ink: {
          50: "#F4F2FD",
          100: "#E9E5FB",
          200: "#D4CCF6",
          300: "#B5A7EF",
          400: "#907BE5",
          500: "#7056D9",
          600: "#5A3BCB",
          700: "#482BAF",
          800: "#3A238C",
          900: "#2C1D6B",
          950: "#1A1442",
        },
        canvas: "#F3F3F8",
        added: { DEFAULT: "#0E7A4F", soft: "#E3F4EC" },
        removed: { DEFAULT: "#B3261E", soft: "#FBE7E5" },
        moved: { DEFAULT: "#0B6A87", soft: "#E1F1F6" },
        corrected: { DEFAULT: "#9A6200", soft: "#FBF0D9" },
      },
      boxShadow: {
        sheet: "0 1px 0 rgba(26,20,66,0.04), 0 12px 32px -18px rgba(26,20,66,0.28)",
      },
    },
  },
  plugins: [],
};

export default config;
