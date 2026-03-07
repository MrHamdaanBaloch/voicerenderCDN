import React, { createContext, useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const refreshUser = async () => {
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                const response = await api.auth.getMe();
                setUser(response.data);
            } catch (error) {
                console.error("Failed to fetch user data:", error);
                localStorage.removeItem('access_token');
                setUser(null);
            }
        }
        setLoading(false);
    };

    useEffect(() => {
        refreshUser();
    }, []);

    const login = async (email, password) => {
        try {
            const response = await api.auth.login(email, password);
            localStorage.setItem('access_token', response.data.access_token);
            const userResponse = await api.auth.getMe();
            setUser(userResponse.data);
            navigate('/dashboard');
            return true;
        } catch (error) {
            console.error("Login failed:", error);
            throw error; // Re-throw for component to handle
        }
    };

    const register = async (userData) => {
        try {
            const response = await api.auth.register(userData);
            // After successful registration, automatically log in the user
            await login(userData.email, userData.password);
            return response.data;
        } catch (error) {
            console.error("Registration failed:", error);
            throw error;
        }
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        setUser(null);
        navigate('/login');
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, login, register, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    return useContext(AuthContext);
};
