import React, { useState, useRef, useEffect } from 'react';
import Button from './Button';
import { CameraIcon, UploadIcon, XIcon, SwitchCameraIcon } from './icons';

interface CameraModalProps {
    onClose: () => void;
    onImageCapture?: (file: File) => void;
}

const CameraModal: React.FC<CameraModalProps> = ({ onClose, onImageCapture }) => {
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
    const [currentDeviceId, setCurrentDeviceId] = useState<string>('');
    const [hasPermission, setHasPermission] = useState(false);
    const [error, setError] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);

    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Initialize camera when modal mounts
    useEffect(() => {
        initializeCamera();

        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const initializeCamera = async () => {
        try {
            setIsLoading(true);
            setError('');

            // Check if camera is supported
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera not supported in this browser');
            }

            // Request permission and start stream
            await requestPermission();
            await enumerateDevices();
            await startStream();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to initialize camera');
        } finally {
            setIsLoading(false);
        }
    };

    const requestPermission = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            setHasPermission(true);
            // Stop the permission test stream
            stream.getTracks().forEach(track => track.stop());
        } catch (err) {
            setHasPermission(false);
            throw new Error('Camera permission denied');
        }
    };

    const enumerateDevices = async () => {
        try {
            const deviceList = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = deviceList.filter(device => device.kind === 'videoinput');
            setDevices(videoDevices);

            if (videoDevices.length > 0 && !currentDeviceId) {
                setCurrentDeviceId(videoDevices[0].deviceId);
            }
        } catch (err) {
            console.warn('Failed to enumerate devices:', err);
        }
    };

    const startStream = async (deviceId?: string) => {
        try {
            const constraints = {
                video: {
                    deviceId: deviceId || currentDeviceId ?
                        { exact: deviceId || currentDeviceId } : true,
                    width: { ideal: 1280, max: 1920 },
                    height: { ideal: 720, max: 1080 },
                    facingMode: 'environment' // Prefer back camera
                },
                audio: false
            };

            const newStream = await navigator.mediaDevices.getUserMedia(constraints);

            setStream(newStream);

            // Wait for video element to be available
            const assignStreamToVideo = () => {
                if (videoRef.current) {
                    const video = videoRef.current;


                    // Stop any existing stream first
                    if (video.srcObject) {
                        const existingStream = video.srcObject as MediaStream;
                        existingStream.getTracks().forEach(track => track.stop());
                    }

                    // Set properties before assigning stream
                    video.muted = true;
                    video.playsInline = true;
                    video.autoplay = true;

                    // Set up event handlers before assigning stream
                    video.onloadedmetadata = () => {
                        video.play().catch(error => {
                            console.error('Video play failed:', error);
                        });
                    };



                    video.onerror = (error) => {
                        console.error('Video error:', error);
                    };



                    // Assign the stream
                    video.srcObject = newStream;
                } else {
                    setTimeout(assignStreamToVideo, 100);
                }
            };

            assignStreamToVideo();
        } catch (err) {
            console.error('Camera stream error:', err);
            throw new Error(`Failed to start camera stream: ${err instanceof Error ? err.message : 'Unknown error'}`);
        }
    };

    const stopStream = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

    const switchCamera = async () => {
        if (devices.length <= 1) return;

        const currentIndex = devices.findIndex(device => device.deviceId === currentDeviceId);
        const nextIndex = (currentIndex + 1) % devices.length;
        const nextDeviceId = devices[nextIndex].deviceId;

        stopStream();
        setCurrentDeviceId(nextDeviceId);
        await startStream(nextDeviceId);
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');

        if (!context) return;

        // Set canvas size to video size
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw video frame to canvas
        context.drawImage(video, 0, 0);

        // Convert to blob and create file
        canvas.toBlob((blob) => {
            if (blob && onImageCapture) {
                const file = new File([blob], `camera-${Date.now()}.jpg`, { type: 'image/jpeg' });
                onImageCapture(file);
                onClose();
            }
        }, 'image/jpeg', 0.9);
    };

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && onImageCapture) {
            onImageCapture(file);
            onClose();
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
            aria-labelledby="camera-modal-title"
            role="dialog"
            aria-modal="true"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b">
                    <h2 id="camera-modal-title" className="text-xl font-semibold">Add Image</h2>
                    <Button variant="ghost" onClick={onClose} className="p-2">
                        <XIcon className="w-5 h-5" />
                    </Button>
                </div>

                {/* Camera Preview */}
                <div className="relative bg-black">
                    {isLoading && (
                        <div className="aspect-video flex items-center justify-center">
                            <div className="text-white">Loading camera...</div>
                        </div>
                    )}

                    {error && (
                        <div className="aspect-video flex items-center justify-center bg-slate-100">
                            <div className="text-center p-4">
                                <CameraIcon className="w-16 h-16 text-slate-400 mx-auto mb-2" />
                                <p className="text-slate-600">{error}</p>
                            </div>
                        </div>
                    )}

                    {stream && !error && (
                        <>
                            <video
                                ref={videoRef}
                                className="w-full aspect-video object-cover bg-gray-900"
                                autoPlay
                                playsInline
                                muted
                                style={{ transform: 'scaleX(-1)' }} // Mirror the video like a selfie
                            />

                            {/* Camera controls overlay */}
                            {devices.length > 1 && (
                                <Button
                                    variant="ghost"
                                    onClick={switchCamera}
                                    className="absolute top-4 right-4 p-2 bg-black bg-opacity-50 text-white hover:bg-opacity-75"
                                >
                                    <SwitchCameraIcon className="w-5 h-5" />
                                </Button>
                            )}
                        </>
                    )}
                </div>

                {/* Controls */}
                <div className="flex justify-center space-x-4 p-4 bg-slate-50">
                    <Button
                        variant="secondary"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <UploadIcon className="w-4 h-4 mr-2" />
                        Upload File
                    </Button>

                    <Button
                        variant="primary"
                        onClick={capturePhoto}
                        disabled={!stream || !!error}
                    >
                        <CameraIcon className="w-4 h-4 mr-2" />
                        Capture
                    </Button>
                </div>

                {/* Hidden elements */}
                <canvas ref={canvasRef} className="hidden" />
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                />
            </div>
        </div>
    );
};

export default CameraModal;