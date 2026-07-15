import { useEffect, useState, type FormEvent } from "react";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import {
  Alert,
  Avatar,
  Box,
  Button,
  CircularProgress,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import { AuthService } from "../services/auth.service";

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    AuthService.getConfig()
      .then(({ enabled }) => {
        if (!enabled) navigate("/conversaciones", { replace: true });
      })
      .catch(() => setError("No se pudo consultar el estado de autenticacion."));
  }, [navigate]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await AuthService.login(username.trim(), password);
      navigate("/conversaciones", { replace: true });
    } catch {
      setError("Usuario o contrasena incorrectos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        p: 3,
        background: "linear-gradient(135deg, #0F766E 0%, #0F172A 100%)",
      }}
    >
      <Paper component="form" onSubmit={submit} elevation={12} sx={{ p: 4, width: "100%", maxWidth: 420 }}>
        <Avatar sx={{ mx: "auto", mb: 2, bgcolor: "primary.main" }}>
          <LockOutlinedIcon />
        </Avatar>
        <Typography variant="h4" align="center" sx={{ fontWeight: 800 }} gutterBottom>
          CrediBot
        </Typography>
        <Typography align="center" color="text.secondary" sx={{ mb: 3 }}>
          Acceso al panel operativo
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField
          label="Usuario"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          fullWidth
          required
          sx={{ mb: 2 }}
        />
        <TextField
          label="Contrasena"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          fullWidth
          required
          sx={{ mb: 3 }}
        />
        <Button type="submit" variant="contained" size="large" fullWidth disabled={loading}>
          {loading ? <CircularProgress size={24} color="inherit" /> : "Ingresar"}
        </Button>
      </Paper>
    </Box>
  );
}
