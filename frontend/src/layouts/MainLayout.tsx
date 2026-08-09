import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import DashboardIcon from "@mui/icons-material/Dashboard";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import PeopleIcon from "@mui/icons-material/People";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import DescriptionIcon from "@mui/icons-material/Description";
import NotificationsIcon from "@mui/icons-material/Notifications";
import SettingsIcon from "@mui/icons-material/Settings";
import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useAuth } from "../hooks/useAuth";
import { usePermissions } from "../hooks/usePermissions";
import { GlobalSearch } from "../components/GlobalSearch";
import { NotificationBell } from "../components/NotificationBell";

const drawerWidth = 248;

const navItems = [
  { to: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { to: "/orders", label: "Orders", icon: <LocalShippingIcon /> },
  { to: "/drivers", label: "Drivers", icon: <PeopleIcon /> },
  { to: "/fleet", label: "Fleet", icon: <DirectionsCarIcon /> },
  { to: "/customers", label: "Customers", icon: <PeopleIcon /> },
  { to: "/documents", label: "Documents", icon: <DescriptionIcon /> },
  { to: "/notifications", label: "Notifications", icon: <NotificationsIcon /> },
  { to: "/settings", label: "Settings", icon: <SettingsIcon />, adminOnly: true },
];

export function MainLayout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const { canManageSettings } = usePermissions();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const drawer = (
    <List sx={{ pt: 1 }}>
      {navItems
        .filter((item) => !item.adminOnly || canManageSettings)
        .map((item) => (
          <ListItemButton
            key={item.to}
            component={NavLink}
            to={item.to}
            end={item.to === "/"}
            onClick={() => setMobileOpen(false)}
            sx={{
              "&.active": {
                bgcolor: "action.selected",
                borderRight: 3,
                borderColor: "primary.main",
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
    </List>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (t) => t.zIndex.drawer + 1,
          bgcolor: "background.paper",
          color: "text.primary",
          borderBottom: 1,
          borderColor: "divider",
        }}
      >
        <Toolbar sx={{ gap: 2 }}>
          {isMobile ? (
            <IconButton edge="start" onClick={() => setMobileOpen(true)}>
              <MenuIcon />
            </IconButton>
          ) : null}
          <Typography variant="h6" sx={{ fontWeight: 700, minWidth: 120 }}>
            ProDrive
          </Typography>
          {!isMobile ? <GlobalSearch /> : null}
          <Box sx={{ flex: 1 }} />
          <NotificationBell />
          <Typography variant="body2" color="text.secondary" sx={{ display: { xs: "none", sm: "block" } }}>
            {user?.first_name} {user?.last_name}
          </Typography>
          <IconButton onClick={handleLogout} aria-label="Logout">
            <LogoutIcon />
          </IconButton>
        </Toolbar>
        {isMobile ? (
          <Box sx={{ px: 2, pb: 2 }}>
            <GlobalSearch />
          </Box>
        ) : null}
      </AppBar>

      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          variant={isMobile ? "temporary" : "permanent"}
          open={isMobile ? mobileOpen : true}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            [`& .MuiDrawer-paper`]: {
              width: drawerWidth,
              boxSizing: "border-box",
              pt: { xs: 14, md: 8 },
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flex: 1,
          p: { xs: 2, md: 3 },
          pt: { xs: 18, md: 11 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
