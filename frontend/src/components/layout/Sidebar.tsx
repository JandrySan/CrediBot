import { Box, List, ListItemButton, ListItemIcon, ListItemText, Typography } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ChatIcon from "@mui/icons-material/Chat";
import AssessmentIcon from "@mui/icons-material/Assessment";
import SettingsIcon from "@mui/icons-material/Settings";

const menuItems = [
  { text: "Dashboard", icon: <DashboardIcon /> },
  { text: "Conversaciones", icon: <ChatIcon /> },
  { text: "Analítica", icon: <AssessmentIcon /> },
  { text: "Configuración", icon: <SettingsIcon /> },
];

export function Sidebar() {
  return (
    <Box
      sx={{
        width: 260,
        minHeight: "100vh",
        background: "#075E54",
        color: "white",
        p: 2,
      }}
    >
      <Typography variant="h5" fontWeight={700} sx={{ mb: 4 }}>
        CrediBot
      </Typography>

      <List>
        {menuItems.map((item) => (
          <ListItemButton
            key={item.text}
            sx={{
              borderRadius: 2,
              mb: 1,
              "&:hover": {
                backgroundColor: "rgba(255,255,255,0.12)",
              },
            }}
          >
            <ListItemIcon sx={{ color: "white" }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}