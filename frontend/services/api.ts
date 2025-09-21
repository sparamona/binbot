/**
 * BinBot API Client Service
 * Centralized service for all backend API communication
 */

export interface ChatResponse {
  success: boolean;
  response: string;
  current_bin?: string;
}

export interface SessionResponse {
  success: boolean;
  session_id: string;
}

export interface ImageUploadResponse {
  success: boolean;
  response: string;
  current_bin?: string;
  image_id?: string;
  analyzed_items?: Array<{
    name: string;
    description?: string;
  }>;
}

export interface InventoryItem {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  image_id?: string;
}

export interface BinContentsResponse {
  success: boolean;
  items: InventoryItem[];
  bin_id: string;
}

class ApiClient {
  private baseUrl: string;
  private sessionId: string | null = null;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  /**
   * Get session ID from cookie or create new session
   */
  private async ensureSession(): Promise<string> {
    if (this.sessionId) {
      return this.sessionId;
    }

    // Try to get session from cookie
    const cookies = document.cookie.split(';');
    const sessionCookie = cookies.find(cookie => 
      cookie.trim().startsWith('session_id=')
    );

    if (sessionCookie) {
      this.sessionId = sessionCookie.split('=')[1];
      return this.sessionId;
    }

    // Create new session
    const response = await fetch(`${this.baseUrl}/api/session`, {
      method: 'POST',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.status}`);
    }

    const data: SessionResponse = await response.json();
    this.sessionId = data.session_id;
    return this.sessionId;
  }

  /**
   * Send chat message to backend
   */
  async sendChatMessage(message: string): Promise<ChatResponse> {
    await this.ensureSession();

    const response = await fetch(`${this.baseUrl}/api/chat/command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Upload image to backend
   */
  async uploadImage(file: File): Promise<ImageUploadResponse> {
    await this.ensureSession();

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/chat/image`, {
      method: 'POST',
      credentials: 'include',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Image upload failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get bin contents
   */
  async getBinContents(binId: string): Promise<BinContentsResponse> {
    await this.ensureSession();

    const response = await fetch(`${this.baseUrl}/api/inventory/bin/${binId}`, {
      method: 'GET',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Failed to get bin contents: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get image URL for display
   */
  getImageUrl(imageId: string): string {
    return `${this.baseUrl}/api/images/${imageId}`;
  }

  /**
   * Check if API is available
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get current session ID
   */
  getCurrentSessionId(): string | null {
    return this.sessionId;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export types for use in components
export type { InventoryItem, ChatResponse, ImageUploadResponse, BinContentsResponse };
