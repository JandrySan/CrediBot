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
import QuizIcon from "@mui/icons-material/Quiz";
import { useLocation, useNavigate } from "react-router-dom";

const menuItems = [
  { text: "Panel", icon: <DashboardIcon />, path: "/panel" },
  { text: "Conversaciones", icon: <ChatIcon />, path: "/conversaciones" },
  { text: "FAQs", icon: <QuizIcon />, path: "/faqs" },
  { text: "Analitica", icon: <AssessmentIcon />, path: "/analitica" },
  { text: "Configuracion", icon: <SettingsIcon />, path: "/configuracion" },
];

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

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
        {menuItems.map((item) => {
          const selected = location.pathname === item.path;

          return (
            <ListItemButton
              key={item.text}
              selected={selected}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 3,
                mb: 1,
                px: 2,
                backgroundColor: selected
                  ? "rgba(255,255,255,0.16)"
                  : "transparent",
                "&:hover": {
                  backgroundColor: "rgba(255,255,255,0.18)",
                },
                "&.Mui-selected": {
                  backgroundColor: "rgba(255,255,255,0.16)",
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
          );
        })}
      </List>
    </Box>
  );
}
