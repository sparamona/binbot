
import React from 'react';
import { RobotIcon } from './icons';
import Button from './Button';

interface SidebarProps {
  isTTSEnabled: boolean;
  onTTSToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isTTSEnabled, onTTSToggle }) => {
  return (
    <div className="hidden md:flex flex-col items-center w-16 bg-white py-4 border-r border-slate-200 space-y-4">
      {/* App Logo */}
      <div className="p-2 bg-slate-100 rounded-lg">
        <RobotIcon className="w-6 h-6 text-slate-600" />
      </div>

      {/* TTS Toggle */}
      <Button
        type="button"
        variant="ghost"
        className={`p-2 rounded-lg ${isTTSEnabled ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'}`}
        onClick={onTTSToggle}
        title={isTTSEnabled ? "Turn off voice responses" : "Turn on voice responses"}
        aria-label={isTTSEnabled ? "Turn off voice responses" : "Turn on voice responses"}
      >
        🔊
      </Button>
    </div>
  );
};

export default Sidebar;