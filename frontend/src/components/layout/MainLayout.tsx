import { Box } from "@mui/material";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

type MainLayoutProps = {
  children: React.ReactNode;
};

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh", background: "#F4F6F8" }}>
      <Sidebar />

      <Box sx={{ flex: 1 }}>
        <TopBar />

        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}