import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import axios from 'axios';

// Components
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Profile from './components/Profile';
import Analytics from './components/Analytics';
import Settings from './components/Settings';
import EyeTracker from './components/EyeTracker';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import GoogleCallback from './components/GoogleCallback';

// Context
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Styles
import './App.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

// Configure axios defaults (strip any trailing /api to avoid duplication when components prefix /api)
const RAW_API = (process.env.REACT_APP_API_URL || '').replace(/\/+$/, '');
const API_HOST = RAW_API.replace(/\/api$/i, '');
axios.defaults.baseURL = API_HOST || 'http://localhost:5000';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// App layout component
const AppLayout = ({ children }) => {
  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100 dark:bg-gray-900">
          {children}
        </main>
      </div>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10B981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#EF4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
          
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/auth/callback" element={<GoogleCallback />} />
            
            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Dashboard />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Analytics />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Profile />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <Settings />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/eye-tracker"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <EyeTracker />
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/eye-health"
              element={
                <ProtectedRoute>
                  <AppLayout>
                    <div className="max-w-7xl mx-auto p-6">
                      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Eye Health</h1>
                      <p className="text-gray-600 dark:text-gray-400">Monitor your eye health and wellness metrics</p>
                    </div>
                  </AppLayout>
                </ProtectedRoute>
              }
            />
            
            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
