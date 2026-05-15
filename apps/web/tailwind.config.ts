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
        // Màu chủ đạo lấy theo phong cách thiệp cưới VN: đỏ đô + vàng cát.
        primary: {
          50: "#fdf3f3",
          100: "#fbe5e5",
          500: "#c2412b",
          600: "#a83423",
          700: "#8B0000",
          800: "#6b1410",
        },
        accent: {
          50: "#fdf9f1",
          100: "#f9efd9",
          500: "#d9b89c",
          600: "#b3895d",
        },
      },
      fontFamily: {
        sans: ['"Be Vietnam Pro"', "Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
