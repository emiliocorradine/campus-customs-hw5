import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend (Problem 7) allows http://localhost:5173, so keep the dev server on that exact port.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true },
});
