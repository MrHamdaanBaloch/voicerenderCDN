import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import DashboardLayout from "./components/Layout/DashboardLayout";
import Dashboard from "./components/Dashboard/Dashboard";
import AgentList from "./components/Agents/AgentList";
import AgentForm from "./components/Agents/AgentForm";
import LandingPage from "./components/Landing/LandingPage";
import LoginPage from "./components/Auth/LoginPage";
import RegisterPage from "./components/Auth/RegisterPage";
import CallList from "./components/Calls/CallList"; // Import CallList
import CallDetails from "./components/Calls/CallDetails"; // Import CallDetails
import Reports from "./components/Reports/Reports";
import Teams from "./components/Settings/Teams";
import Settings from "./components/Settings/Settings";
import PhoneNumbers from "./components/PhoneNumbers/PhoneNumbers";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/toaster"; // Assuming you have a Toaster component

// A wrapper for <Route> that redirects to the login screen if you're not yet authenticated.
function PrivateRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading authentication...</div>; // Or a spinner component
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/landing" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Redirect root to landing or login based on auth status */}
            <Route path="/" element={<AuthRedirect />} />

            {/* Authenticated routes */}
            <Route element={<PrivateRoute />}>
              <Route path="/" element={<DashboardLayout />}>
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="agents" element={<AgentList />} />
                <Route path="agents/new" element={<AgentForm />} />
                <Route path="agents/:id" element={<AgentForm />} />
                {/* Call Management Routes */}
                <Route path="calls" element={<CallList />} />
                <Route path="calls/:id" element={<CallDetails />} />
                {/* Implemented routes */}
                <Route path="reports" element={<Reports />} />
                <Route path="settings/users" element={<Teams />} />
                {/* Placeholder routes - to be implemented */}
                <Route path="phone-numbers" element={<PhoneNumbers />} />
                <Route path="settings/api-keys" element={<div className="p-6"><h1 className="text-2xl font-bold">API Keys (Coming Soon)</h1><p className="text-gray-600 mt-2">Generate and manage API keys for integration.</p></div>} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Route>
          </Routes>
          <Toaster />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

// Component to handle root path redirection based on authentication
function AuthRedirect() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>; // Or a spinner
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/landing" replace />;
}

export default App;
