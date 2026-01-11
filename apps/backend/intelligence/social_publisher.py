import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SocialPublisher:
    """Handles publishing content to external platforms."""
    
    LINKEDIN_API_URL = "https://api.linkedin.com/v2"
    
    LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

    def __init__(self):
        from core.config import settings
        self.client_id = settings.LINKEDIN_CLIENT_ID
        self.client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.twitter_client_id = settings.TWITTER_CLIENT_ID
        self.twitter_client_secret = settings.TWITTER_CLIENT_SECRET
        
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Generate the LinkedIn OAuth authorization URL."""
        if not self.client_id:
            logger.error("LinkedIn Client ID is MISSING in settings!")
            raise Exception("LinkedIn Client ID not configured")
            
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "w_member_social profile openid email" 
        }
        
        # DEBUG LOGGING
        masked_id = f"{self.client_id[:4]}...{self.client_id[-4:]}" if self.client_id else "None"
        print(f"\n[DEBUG] Generating LinkedIn Auth URL")
        print(f"[DEBUG] Client ID: {masked_id}")
        masked_secret = f"{self.client_secret[:4]}...{self.client_secret[-4:]}" if self.client_secret else "None"
        print(f"[DEBUG] Client Secret: {masked_secret}")
        print(f"[DEBUG] Redirect URI: '{redirect_uri}'")
        print(f"[DEBUG] Scopes: '{params['scope']}'")
        
        # Manually construct to avoid encoding issues or use a library
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        return f"{self.LINKEDIN_AUTH_URL}?{query_string}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for an access token."""
        if not self.client_id or not self.client_secret:
            raise Exception("LinkedIn credentials not configured")
            
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        # Headers - let requests set Content-Type from data dict for safety
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # DEBUG LOGGING
        print(f"\n[DEBUG] Exchanging LinkedIn Code for Token")
        masked_id = f"{self.client_id[:4]}...{self.client_id[-4:]}" if self.client_id else "None"
        print(f"[DEBUG] Client ID: {masked_id}")
        print(f"[DEBUG] Redirect URI: '{redirect_uri}'")
        print(f"[DEBUG] Code: {code[:10]}...")

        # FORCE IPv4 WORKAROUND for ConnectionResetError(10054)
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]
            
        try:
            socket.getaddrinfo = new_getaddrinfo
            # Request with timeout and verify=False
            response = requests.post(
                self.LINKEDIN_TOKEN_URL, 
                data=payload, 
                headers=headers, 
                verify=False,
                timeout=30
            )
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Token Exchange Failed: {response.text}")
            raise Exception(f"Failed to exchange token: {response.text}")
        
    def get_linkedin_profile(self, access_token: str):
        """
        Fetch basic profile info from LinkedIn using OIDC endpoint.
        Returns dict with 'sub' (URN), 'name', 'picture', etc.
        """
        # Endpoint for 'openid' scope
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Apply IPv4 force + verify=False (Robustness)
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.get(url, headers=headers, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch LinkedIn profile: {response.status_code} {response.text}")

    def get_user_organizations(self, access_token: str):
        """
        Fetch list of organizations the user administers.
        """
        url = "https://api.linkedin.com/v2/organizationalEntityAcls?q=roleAssignee&role=ADMINISTRATOR&state=APPROVED&projection=(elements*(organizationalTarget~(localizedName)))"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.get(url, headers=headers, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            data = response.json()
            orgs = []
            for element in data.get("elements", []):
                urn = element.get("organizationalTarget")
                # The projection (organizationalTarget~(localizedName)) populates 'organizationalTarget~'
                org_details = element.get("organizationalTarget~", {})
                name = org_details.get("localizedName", "Unknown Organization")
                
                if urn:
                    orgs.append({"urn": urn, "name": name, "type": "organization"})
            return orgs
        else:
            print(f"Failed to fetch orgs: {response.text}")
            return []

    # --- Twitter Integration ---
    TWITTER_AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TWITTER_TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    TWITTER_API_URL = "https://api.twitter.com/2"

    def get_twitter_auth_url(self, redirect_uri: str, state: str, code_verifier: str) -> str:
        """
        Generate Twitter OAuth 2.0 (PKCE) authorization URL.
        Note: `code_challenge` must be S256 of `code_verifier`.
        """
        if not self.twitter_client_id:
             raise Exception("Twitter Client ID not configured")

        import hashlib
        import base64

        # Generate Code Challenge (S256)
        # challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
        sha256_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('ascii').rstrip('=')

        params = {
            "response_type": "code",
            "client_id": self.twitter_client_id,
            "redirect_uri": redirect_uri,
            "scope": "tweet.read tweet.write users.read offline.access",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        import urllib.parse
        return f"{self.TWITTER_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_twitter_code(self, code: str, redirect_uri: str, code_verifier: str) -> dict:
        """Exchange Twitter authorization code for access token."""
        if not self.twitter_client_id or not self.twitter_client_secret:
             raise Exception("Twitter credentials not configured")

        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
            "client_id": self.twitter_client_id
        }
        
        # Twitter requires Basic Auth with Client ID and Secret for confidential clients
        auth = requests.auth.HTTPBasicAuth(self.twitter_client_id, self.twitter_client_secret)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.post(self.TWITTER_TOKEN_URL, data=data, headers=headers, auth=auth, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            return response.json()
        else:
             raise Exception(f"Failed to exchange Twitter token: {response.status_code} {response.text}")

    def get_twitter_user(self, access_token: str):
        """Fetch Twitter user details."""
        url = f"{self.TWITTER_API_URL}/users/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Request profile image and username
        params = {"user.fields": "profile_image_url,username"}
        
        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.get(url, headers=headers, params=params, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            return response.json().get("data")
        else:
            raise Exception(f"Failed to fetch Twitter user: {response.text}")

    def upload_twitter_media(self, access_token: str, image_data: bytes) -> str:
        """
        Upload media to Twitter and get media_id.
        
        Args:
            access_token: Twitter OAuth 2.0 token
            image_data: Binary image data
            
        Returns:
            str: media_id_string
        """
        # Twitter media upload uses v1.1 API
        url = "https://upload.twitter.com/1.1/media/upload.json"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        files = {"media": image_data}
        
        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.post(url, headers=headers, files=files, verify=False, timeout=120)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            data = response.json()
            return data["media_id_string"]
        else:
            raise Exception(f"Failed to upload Twitter media: {response.status_code} {response.text}")

    def post_tweet(self, access_token: str, text: str, image_data: bytes = None):
        """Post a tweet with optional image."""
        
        # Upload media first if provided
        media_id = None
        if image_data:
            try:
                print("[Twitter] Uploading media...")
                media_id = self.upload_twitter_media(access_token, image_data)
                print(f"[Twitter] Media uploaded: {media_id}")
            except Exception as e:
                print(f"[Twitter] Media upload failed: {e}")
                # Continue without image
        
        url = f"{self.TWITTER_API_URL}/tweets"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json" 
        }
        
        # Twitter has 280 character limit - truncate if needed
        if len(text) > 280:
            text = text[:277] + '...'
        
        payload = {"text": text}
        
        # Add media if uploaded
        if media_id:
            payload["media"] = {"media_ids": [media_id]}
        
        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to post tweet: {response.status_code} {response.text}")

    def register_image_upload(self, access_token: str, user_urn: str) -> dict:
        """
        Register an image upload with LinkedIn and get upload URL.
        
        Returns:
            dict with 'uploadUrl' and 'asset' (asset URN)
        """
        url = f"{self.LINKEDIN_API_URL}/assets?action=registerUpload"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": user_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        
        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 200:
            data = response.json()
            return {
                "uploadUrl": data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"],
                "asset": data["value"]["asset"]
            }
        else:
            raise Exception(f"Failed to register image upload: {response.status_code} {response.text}")
    
    def upload_image_binary(self, upload_url: str, access_token: str, image_data: bytes) -> None:
        """
        Upload image binary to LinkedIn's upload URL.
        
        Args:
            upload_url: Upload URL from register_image_upload
            access_token: LinkedIn OAuth token
            image_data: Binary image data
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        
        # Apply IPv4 workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.put(upload_url, headers=headers, data=image_data, verify=False, timeout=120)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload image: {response.status_code} {response.text}")

    def publish_to_linkedin(self, access_token: str, user_urn: str, text: str, url: str = None, title: str = None, image_data: bytes = None):
        """
        Publish a post to LinkedIn (Person or Organization).
        
        Args:
            access_token: LinkedIn OAuth 2.0 access token
            user_urn: LinkedIn Member URN (urn:li:person:...) OR Organization URN (urn:li:organization:...)
            text: The commentary/text of the post
            url: (Optional) URL to share
            title: (Optional) Title of the shared article
            image_data: (Optional) Binary image data to attach
            
        Returns:
            dict: Response from LinkedIn API
        """
        # LinkedIn has 3000 character limit - truncate if needed
        if len(text) > 3000:
            text = text[:2997] + '...'
        
        # Handle image upload first if provided
        asset_urn = None
        if image_data:
            try:
                print("[LinkedIn] Uploading image...")
                upload_info = self.register_image_upload(access_token, user_urn)
                self.upload_image_binary(upload_info["uploadUrl"], access_token, image_data)
                asset_urn = upload_info["asset"]
                print(f"[LinkedIn] Image uploaded successfully: {asset_urn}")
            except Exception as e:
                print(f"[LinkedIn] Image upload failed: {e}")
                # Continue without image
            
        post_url = f"{self.LINKEDIN_API_URL}/ugcPosts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        
        # Construct payload
        payload = {
            "author": user_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text 
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Priority: Image > URL > Text only
        if asset_urn:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "media": asset_urn,
                    "title": {
                        "text": title or "Image from Genesis"
                    }
                }
            ]
        elif url:
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {
                        "text": text[:200]  # Short description
                    },
                    "originalUrl": url,
                    "title": {
                        "text": title or "Shared from Genesis"
                    }
                }
            ]
            
        # Apply IPv4 force + verify=False workaround
        import socket
        old_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            res = old_getaddrinfo(*args, **kwargs)
            return [r for r in res if r[0] == socket.AF_INET]

        try:
            socket.getaddrinfo = new_getaddrinfo
            response = requests.post(post_url, headers=headers, json=payload, verify=False, timeout=60)
        finally:
            socket.getaddrinfo = old_getaddrinfo
        
        if response.status_code == 201:
            return response.json()
        else:
             raise Exception(f"Failed to publish to LinkedIn: {response.status_code} {response.text}")
