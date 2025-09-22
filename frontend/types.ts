export type MessageSender = 'bot' | 'user';

export interface Message {
  id: number;
  text: string;
  sender: MessageSender;
  timestamp: string;
}

export interface InventoryItem {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
  thumbnailUrl?: string;
}

export interface Bin {
  name: string;
  lastUpdated: string;
}