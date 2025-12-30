const API_Base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Connection {
    id: string;
    platform: string;
    profile_name?: string;
    is_active: boolean;
}

export interface ShareResponse {
    status: string;
    platform_response: any;
}

export const socialApi = {
    /**
     * List all connected platforms for a user
     */
    listConnections: async (userId: string): Promise<Connection[]> => {
        try {
            const url = new URL(`${API_Base}/v1/social/connections`);
            url.searchParams.append('user_id', userId);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to list connections", error);
            throw error;
        }
    },

    /**
     * Connect LinkedIn using a manual access token
     */
    connectLinkedIn: async (userId: string, accessToken: string) => {
        try {
            const url = new URL(`${API_Base}/v1/social/connections/linkedin`);
            url.searchParams.append('user_id', userId);

            const response = await fetch(url.toString(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ access_token: accessToken })
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to connect LinkedIn", error);
            throw error;
        }
    },

    /**
     * Disconnect a platform
     */
    disconnect: async (userId: string, platform: string) => {
        try {
            const url = new URL(`${API_Base}/v1/social/connections/${platform}`);
            url.searchParams.append('user_id', userId);

            const response = await fetch(url.toString(), {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`Failed to disconnect ${platform}`, error);
            throw error;
        }
    },

    /**
     * Get LinkedIn OAuth Authorization URL
     */
    getLinkedInAuthUrl: async (userId: string, redirectUri: string) => {
        try {
            const url = new URL(`${API_Base}/v1/social/login/linkedin`);
            url.searchParams.append('user_id', userId);
            url.searchParams.append('redirect_uri', redirectUri);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to get LinkedIn auth URL", error);
            throw error;
        }
    },

    /**
     * Exchange OAuth code for token
     */
    exchangeLinkedInCode: async (code: string, state: string, redirectUri: string) => {
        try {
            const url = new URL(`${API_Base}/v1/social/callback/linkedin`);
            url.searchParams.append('code', code);
            url.searchParams.append('state', state);
            url.searchParams.append('redirect_uri', redirectUri);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to exchange LinkedIn code", error);
            throw error;
        }
    },

    /**
     * Share content to LinkedIn
     */
    /**
     * Get available LinkedIn targets (Profile + Organizations)
     */
    getLinkedInTargets: async (userId: string): Promise<{ urn: string; name: string; type: string; image?: string }[]> => {
        try {
            const url = new URL(`${API_Base}/v1/social/linkedin/targets`);
            url.searchParams.append('user_id', userId);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to get LinkedIn targets", error);
            throw error;
        }
    },

    /**
     * Share content to LinkedIn
     */
    /**
     * Share content to a Social Platform
     */
    shareContent: async (
        userId: string,
        platform: 'linkedin' | 'twitter',
        content: string,
        url?: string,
        title?: string,
        targetUrn?: string
    ): Promise<ShareResponse> => {
        try {
            const apiUrl = new URL(`${API_Base}/v1/social/share`);
            apiUrl.searchParams.append('user_id', userId);

            const response = await fetch(apiUrl.toString(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    platform,
                    content,
                    url,
                    title,
                    target_urn: targetUrn
                })
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`Failed to share to ${platform}`, error);
            throw error;
        }
    },

    /**
     * Get Twitter OAuth Authorization URL
     */
    getTwitterAuthUrl: async (userId: string, redirectUri: string) => {
        try {
            const url = new URL(`${API_Base}/v1/social/login/twitter`);
            url.searchParams.append('user_id', userId);
            url.searchParams.append('redirect_uri', redirectUri);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to get Twitter auth URL", error);
            throw error;
        }
    },

    /**
     * Exchange Twitter OAuth code for token
     */
    exchangeTwitterCode: async (code: string, state: string, redirectUri: string, codeVerifier: string) => {
        try {
            const url = new URL(`${API_Base}/v1/social/callback/twitter`);
            url.searchParams.append('code', code);
            url.searchParams.append('state', state);
            url.searchParams.append('redirect_uri', redirectUri);
            url.searchParams.append('code_verifier', codeVerifier);

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error(`Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error("Failed to exchange Twitter code", error);
            throw error;
        }
    }
};
