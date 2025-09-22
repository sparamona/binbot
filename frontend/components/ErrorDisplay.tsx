import React from 'react';
import { AlertTriangleIcon, CloseIcon } from './icons';

interface ErrorDisplayProps {
    message: string;
    onClose: () => void;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message, onClose }) => {
    return (
        <div 
            className="absolute top-0 left-0 right-0 z-10 bg-red-500 text-white p-3 flex items-center justify-between shadow-lg"
            role="alert"
        >
            <div className="flex items-center">
                <AlertTriangleIcon className="w-5 h-5 mr-3 flex-shrink-0" />
                <p className="text-sm font-medium">{message}</p>
            </div>
            <button 
                onClick={onClose} 
                className="p-1 rounded-full hover:bg-red-600 transition-colors focus:outline-none focus:ring-2 focus:ring-white"
                aria-label="Dismiss error message"
            >
                <CloseIcon className="w-5 h-5" />
            </button>
        </div>
    );
};

export default ErrorDisplay;