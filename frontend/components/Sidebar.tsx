
import React from 'react';
import { RobotIcon } from './icons';

const Sidebar: React.FC = () => {
  return (
    <div className="hidden md:flex flex-col items-center w-16 bg-white py-4 border-r border-slate-200">
      <div className="p-2 bg-slate-100 rounded-lg">
        <RobotIcon className="w-6 h-6 text-slate-600" />
      </div>
    </div>
  );
};

export default Sidebar;