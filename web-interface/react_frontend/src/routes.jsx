import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Welcome from './pages/Welcome';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import DashboardHome from './pages/DashboardHome';
import MonitoringSimple from './pages/MonitoringSimple';
import NetworkManagement from './pages/NetworkManagement';
import ProtectedRoute from './components/common/ProtectedRoute';

// Import des composants modernes
import SecurityModern from './pages/SecurityModern';
import QoSModern from './pages/QoSModern';
import NetworkSimple from './pages/NetworkSimple';
import ReportingModern from './pages/ReportingModern';

// Import des pages API
import ApiClients from './pages/ApiClients';
import ApiViews from './pages/ApiViews';
import ApiTestPage from './pages/ApiTestPage';

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Routes protégées avec layout Dashboard */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <Dashboard>
            <DashboardHome />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/monitoring" element={
        <ProtectedRoute>
          <Dashboard>
            <MonitoringSimple />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/network" element={
        <ProtectedRoute>
          <Dashboard>
            <NetworkSimple />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/security" element={
        <ProtectedRoute>
          <Dashboard>
            <SecurityModern />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/qos" element={
        <ProtectedRoute>
          <Dashboard>
            <QoSModern />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/reports" element={
        <ProtectedRoute>
          <Dashboard>
            <ReportingModern />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      {/* Modules backend - pages modernes avec Tailwind */}
      <Route path="/api-clients" element={
        <ProtectedRoute>
          <Dashboard>
            <ApiClients />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/api-views" element={
        <ProtectedRoute>
          <Dashboard>
            <ApiViews />
          </Dashboard>
        </ProtectedRoute>
      } />
      
      <Route path="/api-test" element={
        <ProtectedRoute>
          <Dashboard>
            <ApiTestPage />
          </Dashboard>
        </ProtectedRoute>
      } />
    </Routes>
  );
};

export default AppRoutes;
