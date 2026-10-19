import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// host: true -> serwer deweloperski jest dostępny z innych urządzeń w
// sieci domowej (np. z telefonu pod adresem http://<IP-komputera>:5173).
export default defineConfig({
  plugins: [react()],
  server: { host: true, port: 5173 },
  preview: { host: true, port: 5173 },
});