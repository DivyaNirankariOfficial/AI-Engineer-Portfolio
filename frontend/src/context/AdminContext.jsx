import React, { createContext, useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

export const AdminContext = createContext();

export const AdminProvider = ({ children }) => {
  const [token, setToken] = useState(() => sessionStorage.getItem('admin_token'));

  const login = async (password) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      
      const data = await res.json();
      if (res.ok && data.token) {
        setToken(data.token);
        try {
          sessionStorage.setItem('admin_token', data.token);
        } catch (storageErr) {
          console.warn('sessionStorage is disabled in this environment:', storageErr);
        }
        return true;
      }
      return false;
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    sessionStorage.removeItem('admin_token');
  };

  return (
    <AdminContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AdminContext.Provider>
  );
};
