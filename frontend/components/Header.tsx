"use client";

import React, { useState } from "react";
import { Wrench, Cpu, Moon, Sun, Edit2, Check } from "lucide-react";

interface HeaderProps {
  vehicle: string;
  onVehicleChange: (newVehicle: string) => void;
  theme: "light" | "dark";
  onThemeToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  vehicle,
  onVehicleChange,
  theme,
  onThemeToggle,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [vehicleInput, setVehicleInput] = useState(vehicle);

  const handleSave = () => {
    if (vehicleInput.trim()) {
      onVehicleChange(vehicleInput.trim());
    }
    setIsEditing(false);
  };

  return (
    <header className="sticky top-0 z-20 w-full border-b border-garage-200 dark:border-garage-800 bg-white/95 dark:bg-garage-950/95 backdrop-blur px-3 py-2.5 sm:px-4">
      <div className="flex items-center justify-between gap-2 max-w-full">
        {/* Brand */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-garage-900 dark:bg-garage-100 text-white dark:text-garage-900 flex items-center justify-center font-bold text-sm tracking-tight">
            REV
          </div>
          <span className="font-semibold text-sm tracking-tight text-garage-900 dark:text-garage-100 hidden sm:inline">
            Diagnostics
          </span>
        </div>

        {/* Chips & Controls */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          {/* Editable Vehicle Chip */}
          {isEditing ? (
            <div className="flex items-center gap-1 bg-garage-100 dark:bg-garage-900 border border-garage-300 dark:border-garage-700 rounded-full px-2 py-1 text-xs">
              <input
                type="text"
                value={vehicleInput}
                onChange={(e) => setVehicleInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                className="bg-transparent border-none outline-none text-garage-800 dark:text-garage-200 w-28 sm:w-36 text-xs"
                autoFocus
                aria-label="Edit vehicle name"
              />
              <button
                onClick={handleSave}
                className="p-1 text-garage-600 hover:text-garage-900 dark:text-garage-400 dark:hover:text-garage-100 rounded focus:ring-2 focus:ring-garage-500"
                aria-label="Save vehicle"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="flex items-center gap-1.5 bg-garage-100 dark:bg-garage-900 hover:bg-garage-200 dark:hover:bg-garage-800 border border-garage-200 dark:border-garage-700 rounded-full px-2.5 py-1 text-xs text-garage-700 dark:text-garage-300 transition-colors focus:ring-2 focus:ring-garage-400 min-h-[36px]"
              title="Click to edit vehicle"
              aria-label={`Vehicle: ${vehicle}. Click to edit`}
            >
              <Wrench className="w-3 h-3 text-garage-500" />
              <span className="truncate max-w-[120px] sm:max-w-[160px] font-medium">
                {vehicle}
              </span>
              <Edit2 className="w-2.5 h-2.5 text-garage-400" />
            </button>
          )}

          {/* Local Model Chip */}
          <div
            className="flex items-center gap-1 bg-garage-100 dark:bg-garage-900 border border-garage-200 dark:border-garage-700 rounded-full px-2 py-1 text-xs text-garage-600 dark:text-garage-400 min-h-[36px]"
            title="Running on local Ollama GPU"
          >
            <Cpu className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
            <span className="hidden xs:inline">Local model</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={onThemeToggle}
            className="p-2 rounded-full border border-garage-200 dark:border-garage-700 hover:bg-garage-100 dark:hover:bg-garage-800 text-garage-700 dark:text-garage-300 transition-colors focus:ring-2 focus:ring-garage-400 min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
          >
            {theme === "light" ? (
              <Moon className="w-4 h-4" />
            ) : (
              <Sun className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
