import React from 'react';
import type { InventoryItem } from '../types';

interface InventoryItemCardProps {
  item: InventoryItem;
  onImageSelect: (url: string) => void;
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

const InventoryItemCard: React.FC<InventoryItemCardProps> = ({ item, onImageSelect }) => {
  return (
    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex items-center justify-between gap-4">
      <div className="flex-grow">
        <h3 className="font-medium text-slate-800">{item.name}</h3>
        {item.description && <p className="text-sm text-slate-500 mt-1">{item.description}</p>}
        <div className="flex items-center gap-4 text-xs text-slate-400 mt-2">
           <span>Created: {formatDate(item.createdAt)}</span>
        </div>
      </div>
      
      <div className="flex-shrink-0 w-16 h-16 rounded-md">
        {item.thumbnailUrl && (
          <img 
            src={item.thumbnailUrl} 
            alt={item.name} 
            className="w-full h-full object-cover rounded-md cursor-pointer transition-transform duration-200 hover:scale-105"
            onClick={() => onImageSelect(item.thumbnailUrl!)}
           />
        )}
      </div>
    </div>
  );
};

export default InventoryItemCard;