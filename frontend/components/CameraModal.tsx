import React from 'react';
import Button from './Button';
import { CameraIcon, UploadIcon } from './icons';

interface CameraModalProps {
    onClose: () => void;
}

const CameraModal: React.FC<CameraModalProps> = ({ onClose }) => {
    return (
        <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            aria-labelledby="camera-modal-title"
            role="dialog"
            aria-modal="true"
            onClick={onClose}
        >
            <div 
                className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6"
                onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
            >
                <h2 id="camera-modal-title" className="text-xl font-semibold mb-4">Add Image</h2>
                
                <div className="w-full aspect-video bg-slate-200 rounded-md flex items-center justify-center mb-4">
                    <CameraIcon className="w-16 h-16 text-slate-400" />
                    <p className="sr-only">Camera preview</p>
                </div>
                
                <div className="flex justify-end space-x-3">
                    <Button variant="outline" onClick={onClose} className="px-4 py-2">
                        Cancel
                    </Button>
                    <Button variant="secondary" className="px-4 py-2">
                        <UploadIcon className="w-4 h-4 mr-2" />
                        Upload
                    </Button>
                    <Button variant="primary" className="px-4 py-2">
                        <CameraIcon className="w-4 h-4 mr-2" />
                        Capture
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default CameraModal;