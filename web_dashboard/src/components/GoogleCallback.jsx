import React, { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

const GoogleCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { googleLogin } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        toast.error('Google authentication failed');
        navigate('/login');
        return;
      }

    if (code) {
        try {
      // Exchange code for user info via backend (respect CRA proxy or env base URL)
      const base = process.env.REACT_APP_API_URL || '';
      const response = await fetch(`${base}/api/auth/google/callback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
          });

          const data = await response.json();
          
          if (response.ok) {
            if (data.status === 'offline') {
              toast.error('Google OAuth not configured for local dev');
              navigate('/login');
              return;
            }
            const result = await googleLogin({
              email: data.email,
              name: data.name,
              id: data.id
            });
            
            if (result.success) {
              // Close popup if opened from popup
              if (window.opener) {
                window.opener.postMessage({
                  type: 'GOOGLE_OAUTH_SUCCESS',
                  email: data.email,
                  name: data.name,
                  id: data.id
                }, window.location.origin);
                window.close();
              } else {
                navigate('/');
              }
            }
          } else {
            throw new Error(data.message || 'Authentication failed');
          }
        } catch (error) {
          toast.error('Authentication failed');
          navigate('/login');
        }
      }
    };

    handleCallback();
  }, [searchParams, navigate, googleLogin]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing authentication...</p>
      </div>
    </div>
  );
};

export default GoogleCallback;
