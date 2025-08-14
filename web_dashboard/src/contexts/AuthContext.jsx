import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

// Base URL logic handled in App.jsx (host only). Always prefix /api.
const buildEndpoint = (path) => {
  if (!path.startsWith('/')) path = '/' + path;
  return '/api' + path;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('auth_token'));

  const isAuthenticated = !!user;

  // Configure axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(buildEndpoint('/user/profile'));
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error?.response?.status, error?.response?.data);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  // Login function
  const login = async (email, password) => {
    try {
      const response = await axios.post(buildEndpoint('/auth/login'), {
        email,
        password
      });

      const { token: authToken, user: userData } = response.data;
      setToken(authToken);
      setUser(userData);
      localStorage.setItem('auth_token', authToken);
      toast.success('Login successful!');
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Google login function
  const googleLogin = async (userData) => {
    try {
      const response = await axios.post(buildEndpoint('/auth/google'), {
        email: userData.email,
        name: userData.name,
        id: userData.id
      });
      const { token: authToken, user: userInfo } = response.data;
      setToken(authToken);
      setUser(userInfo);
      localStorage.setItem('auth_token', authToken);
      toast.success('Google login successful!');
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Google login failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      const response = await axios.post(buildEndpoint('/auth/register'), userData);
      const { token: authToken, user: newUser } = response.data;
      setToken(authToken);
      setUser(newUser);
      localStorage.setItem('auth_token', authToken);
      toast.success('Registration successful!');
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Logout function
  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('auth_token');
    delete axios.defaults.headers.common['Authorization'];
    toast.success('Logged out successfully');
  };

  // Submit blink data
  const submitBlinkData = async (blinkData) => {
    try {
      const response = await axios.post(buildEndpoint('/blink-data'), blinkData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to submit blink data:', error);
      return { success: false, error: error.response?.data?.message || 'Failed to submit data' };
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    googleLogin,
    register,
    logout,
    submitBlinkData,
    setToken,
    setUser
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
