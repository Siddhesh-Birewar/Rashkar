"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import type { Farm } from "./api/types";
import { farmsApi } from "./api/client";
import { useAuth } from "./auth-context";

interface FarmContextType {
  farms: Farm[];
  selectedFarm: Farm | null;
  selectedFarmId: string | null;
  loading: boolean;
  error: string | null;
  setSelectedFarmId: (id: string | null) => void;
  refreshFarms: () => Promise<void>;
}

const FarmContext = createContext<FarmContextType>({
  farms: [],
  selectedFarm: null,
  selectedFarmId: null,
  loading: true,
  error: null,
  setSelectedFarmId: () => {},
  refreshFarms: async () => {},
});

export function FarmProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [farms, setFarms] = useState<Farm[]>([]);
  const [selectedFarmId, setSelectedFarmIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshFarms = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await farmsApi.list();
      setFarms(data);

      // Restore previously selected farm if still valid
      const stored = localStorage.getItem("cropnet_selected_farm_id");
      if (stored && data.some((f) => f.id === stored)) {
        setSelectedFarmIdState(stored);
      } else if (data.length > 0) {
        setSelectedFarmIdState(data[0].id);
        localStorage.setItem("cropnet_selected_farm_id", data[0].id);
      } else {
        setSelectedFarmIdState(null);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load farms");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      refreshFarms();
    } else {
      setFarms([]);
      setSelectedFarmIdState(null);
      setLoading(false);
    }
  }, [user?.id]);

  const setSelectedFarmId = (id: string | null) => {
    setSelectedFarmIdState(id);
    if (id) {
      localStorage.setItem("cropnet_selected_farm_id", id);
    } else {
      localStorage.removeItem("cropnet_selected_farm_id");
    }
  };

  const selectedFarm = farms.find((f) => f.id === selectedFarmId) || null;

  return (
    <FarmContext.Provider
      value={{
        farms,
        selectedFarm,
        selectedFarmId,
        loading,
        error,
        setSelectedFarmId,
        refreshFarms,
      }}
    >
      {children}
    </FarmContext.Provider>
  );
}

export function useFarm() {
  return useContext(FarmContext);
}
