import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import DashboardIcon from "@mui/icons-material/Dashboard";
import LocalShippingIcon from "@mui/icons-material/LocalShipping";
import PeopleIcon from "@mui/icons-material/People";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import DescriptionIcon from "@mui/icons-material/Description";
import NotificationsIcon from "@mui/icons-material/Notifications";
import ViewKanbanIcon from "@mui/icons-material/ViewKanban";
import SettingsIcon from "@mui/icons-material/Settings";
import LogoutIcon from "@mui/icons-material/Logout";
import MenuIcon from "@mui/icons-material/Menu";
import BusinessIcon from "@mui/icons-material/Business";
import {
  AppBar,
  Box,
  Divider,
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
import { alpha } from "@mui/material/styles";
import { useAuth } from "../hooks/useAuth";
import { usePermissions } from "../hooks/usePermissions";
import { GlobalSearch } from "../components/GlobalSearch";
import { NotificationBell } from "../components/NotificationBell";
import { ConnectionStatus } from "../components/ConnectionStatus";
import { layout } from "../design-system/tokens";

const drawerWidth = layout.sidebarWidth;

const navItems = [
  { to: "/", label: "Dashboard", icon: <DashboardIcon fontSize="small" /> },
  { to: "/orders", label: "Orders", icon: <LocalShippingIcon fontSize="small" /> },
  { to: "/drivers", label: "Drivers", icon: <PeopleIcon fontSize="small" /> },
  { to: "/fleet", label: "Fleet", icon: <DirectionsCarIcon fontSize="small" /> },
  { to: "/customers", label: "Customers", icon: <BusinessIcon fontSize="small" /> },
  { to: "/planning", label: "Planning", icon: <ViewKanbanIcon fontSize="small" /> },
  { to: "/documents", label: "Documents", icon: <DescriptionIcon fontSize="small" /> },
  { to: "/notifications", label: "Notifications", icon: <NotificationsIcon fontSize="small" /> },
  { to: "/settings", label: "Settings", icon: <SettingsIcon fontSize="small" />, adminOnly: true },
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
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box sx={{ px: 2.5, py: 2.5 }}>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            letterSpacing: "0.06em",
            color: "common.white",
          }}
        >
          PRODRIVE
        </Typography>
        <Typography variant="caption" sx={{ color: alpha("#FFFFFF", 0.55), letterSpacing: "0.04em" }}>
          Dispatcher Operations
        </Typography>
      </Box>
      <Divider sx={{ borderColor: alpha("#FFFFFF", 0.08) }} />
      <List sx={{ pt: 1.5, pb: 2, flex: 1 }}>
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
                color: alpha("#FFFFFF", 0.72),
                "& .MuiListItemIcon-root": { color: alpha("#FFFFFF", 0.55), minWidth: 38 },
                "&:hover": {
                  bgcolor: alpha("#FFFFFF", 0.06),
                  color: "common.white",
                  "& .MuiListItemIcon-root": { color: "accent.main" },
                },
                "&.active": {
                  bgcolor: alpha("#FFFFFF", 0.1),
                  color: "common.white",
                  borderLeft: 3,
                  borderColor: "accent.main",
                  pl: "13px",
                  "& .MuiListItemIcon-root": { color: "accent.main" },
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontSize: "0.875rem", fontWeight: 500 }}
              />
            </ListItemButton>
          ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (t) => t.zIndex.drawer + 1,
          bgcolor: "background.paper",
          color: "text.primary",
          borderBottom: 1,
          borderColor: "divider",
          boxShadow: 1,
        }}
      >
        <Toolbar sx={{ gap: 2, minHeight: `${layout.topBarHeight}px !important` }}>
          {isMobile ? (
            <IconButton edge="start" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <MenuIcon />
            </IconButton>
          ) : null}
          {!isMobile ? (
            <Typography variant="subtitle1" color="text.secondary" sx={{ minWidth: 140 }}>
              Operations Console
            </Typography>
          ) : (
            <Typography variant="subtitle1" fontWeight={700} color="primary.dark">
              ProDrive
            </Typography>
          )}
          {!isMobile ? <GlobalSearch /> : null}
          <Box sx={{ flex: 1 }} />
          <ConnectionStatus />
          <NotificationBell />
          <Divider orientation="vertical" flexItem sx={{ mx: 0.5, display: { xs: "none", sm: "block" } }} />
          <Typography variant="body2" color="text.secondary" sx={{ display: { xs: "none", sm: "block" } }}>
            {user?.first_name} {user?.last_name}
          </Typography>
          <IconButton onClick={handleLogout} aria-label="Logout" size="small">
            <LogoutIcon fontSize="small" />
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
              pt: { xs: 14, md: `${layout.topBarHeight}px` },
              bgcolor: "primary.dark",
              backgroundImage: "none",
              borderRight: "none",
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
          pt: { xs: 18, md: `${layout.topBarHeight + 24}px` },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          maxWidth: layout.contentMaxWidth,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
