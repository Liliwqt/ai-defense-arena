import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { App } from "./App";
import { PaymentTestPage } from "./payments/PaymentTestPage";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {new URLSearchParams(location.search).get("payments") === "test" ? <PaymentTestPage /> : <App />}
  </StrictMode>
);
