import { lazy, Suspense } from "react";
import { Box, CircularProgress } from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { theme } from "./theme/theme";
import { MainLayout } from "./components/layout/MainLayout";
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage").then((module) => ({ default: module.AnalyticsPage })));
const DashboardPage = lazy(() => import("./pages/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const FaqAdminPage = lazy(() => import("./pages/FaqAdminPage").then((module) => ({ default: module.FaqAdminPage })));
const OverviewPage = lazy(() => import("./pages/OverviewPage").then((module) => ({ default: module.OverviewPage })));
const SettingsPage = lazy(() => import("./pages/SettingsPage").then((module) => ({ default: module.SettingsPage })));
const LoginPage = lazy(() => import("./pages/LoginPage").then((module) => ({ default: module.LoginPage })));

function PageFallback() {
  return <Box sx={{ display: "grid", placeItems: "center", minHeight: 320 }}><CircularProgress /></Box>;
}

function DashboardRoutes() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/conversaciones" replace />} />
        <Route path="/panel" element={<OverviewPage />} />
        <Route path="/conversaciones" element={<DashboardPage />} />
        <Route path="/faqs" element={<FaqAdminPage />} />
        <Route path="/analitica" element={<AnalyticsPage />} />
        <Route path="/configuracion" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/conversaciones" replace />} />
      </Routes>
    </MainLayout>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<DashboardRoutes />} />
        </Routes>
      </Suspense>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
