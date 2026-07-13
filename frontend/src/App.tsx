import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { theme } from "./theme/theme";
import { MainLayout } from "./components/layout/MainLayout";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FaqAdminPage } from "./pages/FaqAdminPage";
import { OverviewPage } from "./pages/OverviewPage";
import { SettingsPage } from "./pages/SettingsPage";

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
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
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
