import React from 'react';
import { CloseIcon } from './icons';

interface ImageModalProps {
    imageUrl: string;
    onClose: () => void;
}

const ImageModal: React.FC<ImageModalProps> = ({ imageUrl, onClose }) => {
    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 transition-opacity duration-300"
            onClick={onClose}
            role="dialog"
            aria-modal="true"
            aria-label="Image viewer"
        >
            <div
                className="relative max-w-4xl max-h-[90vh] p-4"
                onClick={(e) => e.stopPropagation()}
            >
                <img src={imageUrl} alt="Full size view" className="object-contain max-w-full max-h-full rounded-lg shadow-2xl" />
                <button
                    onClick={onClose}
                    className="absolute -top-2 -right-2 p-1.5 bg-white/80 backdrop-blur-sm rounded-full text-slate-800 hover:bg-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 transition-colors"
                    aria-label="Close image viewer"
                >
                    <CloseIcon className="w-6 h-6" />
                </button>
            </div>
        </div>
    );
};

export default ImageModal;
