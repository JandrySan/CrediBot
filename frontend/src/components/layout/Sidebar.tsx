import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";

import DashboardIcon from "@mui/icons-material/Dashboard";
import ChatIcon from "@mui/icons-material/Chat";
import AssessmentIcon from "@mui/icons-material/Assessment";
import SettingsIcon from "@mui/icons-material/Settings";

const menuItems = [
  { text: "Panel", icon: <DashboardIcon /> },
  { text: "Conversaciones", icon: <ChatIcon /> },
  { text: "Analítica", icon: <AssessmentIcon /> },
  { text: "Configuración", icon: <SettingsIcon /> },
];

export function Sidebar() {
  return (
    <Box
      sx={{
        width: 250,
        minHeight: "100vh",
        background: "linear-gradient(180deg, #0F766E 0%, #134E4A 100%)",
        color: "white",
        p: 2.5,
      }}
    >
      <Typography variant="h5" sx={{ fontWeight: 900, mb: 1 }}>
        CrediBot
      </Typography>

      <Typography variant="body2" sx={{ opacity: 0.75, mb: 4 }}>
        CRM Financiero
      </Typography>

      <List>
        {menuItems.map((item, index) => (
          <ListItemButton
            key={item.text}
            sx={{
              borderRadius: 3,
              mb: 1,
              px: 2,
              backgroundColor:
                index === 0 ? "rgba(255,255,255,0.16)" : "transparent",
              "&:hover": {
                backgroundColor: "rgba(255,255,255,0.18)",
              },
            }}
          >
            <ListItemIcon sx={{ color: "white", minWidth: 38 }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText
              primary={item.text}
              slotProps={{ primary: { sx: { fontWeight: 700 } } }}
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}