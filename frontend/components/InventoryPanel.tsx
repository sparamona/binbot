import React from 'react';
import type { InventoryItem, Bin } from '../types';
import InventoryItemCard from './InventoryItemCard';

interface InventoryPanelProps {
  items: InventoryItem[];
  bin: Bin;
  onImageSelect: (url: string) => void;
}

const InventoryPanel: React.FC<InventoryPanelProps> = ({ items, bin, onImageSelect }) => {
  return (
    <div className="flex flex-col h-full bg-slate-50/50">
      <header className="p-4 border-b border-slate-200">
        <h2 className="text-lg font-semibold">{bin.name}</h2>
        <p className="text-sm text-slate-500">Last Updated: {bin.lastUpdated}</p>
      </header>
      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-3">
          {items.map(item => (
            <InventoryItemCard key={item.id} item={item} onImageSelect={onImageSelect} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default InventoryPanel;