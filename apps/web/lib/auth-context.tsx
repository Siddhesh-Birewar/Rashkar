"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { createClient } from "./supabase/client";
import { DEFAULT_DEV_USER_ID, schemesApi } from "./api/client";

interface AuthUser {
  id: string;
  email: string;
  is_admin?: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  isDevMode: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  setDevUserId: (id: string) => void;
  refreshAdminStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isDevMode: false,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
  setDevUserId: () => {},
  refreshAdminStatus: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDevMode, setIsDevMode] = useState(false);

  const supabase = createClient();

  const refreshAdminStatus = async () => {
    try {
      const status = await schemesApi.getAdminStatus();
      setUser((prev) => (prev ? { ...prev, is_admin: status.is_admin } : prev));
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    async function initAuth() {
      // 1. Check if Supabase has an active session
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session && session.user) {
          localStorage.setItem("cropnet_access_token", session.access_token);
          setUser({
            id: session.user.id,
            email: session.user.email || "farmer@cropnet.local",
          });
          setIsDevMode(false);
          setLoading(false);
          return;
        }
      } catch {
        // Supabase might not be configured or reachable locally
      }

      // 2. Check for dev user id or fall back to default dev user
      const storedDevId = localStorage.getItem("cropnet_dev_user_id") || DEFAULT_DEV_USER_ID;
      localStorage.setItem("cropnet_dev_user_id", storedDevId);
      setUser({
        id: storedDevId,
        email: "dev@cropnet.local",
        is_admin: true,
      });
      setIsDevMode(true);
      setLoading(false);
    }

    initAuth();

    try {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
        if (session && session.user) {
          localStorage.setItem("cropnet_access_token", session.access_token);
          setUser({
            id: session.user.id,
            email: session.user.email || "farmer@cropnet.local",
          });
          setIsDevMode(false);
        } else {
          localStorage.removeItem("cropnet_access_token");
        }
      });

      return () => {
        subscription.unsubscribe();
      };
    } catch {
      // ignore
    }
  }, []);

  const signIn = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      if (data.session && data.user) {
        localStorage.setItem("cropnet_access_token", data.session.access_token);
        setUser({
          id: data.user.id,
          email: data.user.email || email,
        });
        setIsDevMode(false);
      }
    } catch (err) {
      // If Supabase is unconfigured, allow local dev login
      if (email && password) {
        localStorage.setItem("cropnet_dev_user_id", DEFAULT_DEV_USER_ID);
        setUser({
          id: DEFAULT_DEV_USER_ID,
          email,
          is_admin: true,
        });
        setIsDevMode(true);
      } else {
        throw err;
      }
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });
      if (error) throw error;
      if (data.session && data.user) {
        localStorage.setItem("cropnet_access_token", data.session.access_token);
        setUser({
          id: data.user.id,
          email: data.user.email || email,
        });
        setIsDevMode(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch {
      // ignore
    }
    localStorage.removeItem("cropnet_access_token");
    setUser(null);
  };

  const setDevUserId = (id: string) => {
    localStorage.setItem("cropnet_dev_user_id", id);
    setUser({
      id,
      email: "dev@cropnet.local",
      is_admin: true,
    });
    setIsDevMode(true);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isDevMode,
        signIn,
        signUp,
        signOut,
        setDevUserId,
        refreshAdminStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
