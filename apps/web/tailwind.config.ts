import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#1B5E20", leaf: "#2E7D32" },
        accent: "#E65100",
        soil: "#5D4037",
        surface: "#F9FBF9",
        border: "#E0E0E0",
      },
      borderRadius: {
        card: "12px",
        button: "8px",
      },
      boxShadow: {
        card: "0 4px 12px rgba(0,0,0,0.08)",
        subtle: "0 2px 8px rgba(0,0,0,0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
