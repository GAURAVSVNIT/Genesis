from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uuid

from database.database import get_db
from database.models.platform import UserPlatformConnection
from database.models.user import User
from intelligence.social_publisher import SocialPublisher

router = APIRouter()

# --- Pydantic Models ---
class LinkedInConnectRequest(BaseModel):
    access_token: str
    
class ShareRequest(BaseModel):
    platform: str = "linkedin"
    content: str
    title: Optional[str] = None
    url: Optional[str] = None
    target_urn: Optional[str] = None # Optional target (e.g., Organization URN)

class ConnectionResponse(BaseModel):
    id: str
    platform: str
    profile_name: Optional[str]
    is_active: bool

# --- Endpoints ---

@router.get("/connections", response_model=List[ConnectionResponse])
def list_connections(user_id: str, db: Session = Depends(get_db)):
    """List all connected social platforms for a user."""
    # Note: Using user_id query param for MVP. In prod, extract from Auth token.
    connections = db.query(UserPlatformConnection).filter(
        UserPlatformConnection.user_id == user_id, 
        UserPlatformConnection.is_active == True
    ).all()
    
    return [
        ConnectionResponse(
            id=str(c.id),
            platform=c.platform,
            profile_name=c.profile_name,
            is_active=c.is_active
        ) for c in connections
    ]

@router.post("/connections/linkedin")
def connect_linkedin(request: LinkedInConnectRequest, user_id: str, db: Session = Depends(get_db)):
    """
    Connect a LinkedIn account using a manually provided Access Token.
    Validates the token by fetching the user's profile.
    """
    publisher = SocialPublisher()
    
    try:
        # Verify Token & Get Profile
        profile = publisher.get_linkedin_profile(request.access_token)
        
        # Profile ID (URN)
        urn = profile.get("id")
        # Construct Name
        fname = profile.get("localizedFirstName", "")
        lname = profile.get("localizedLastName", "")
        full_name = f"{fname} {lname}".strip()
        
        # Check for existing connection
        existing = db.query(UserPlatformConnection).filter(
            UserPlatformConnection.user_id == user_id,
            UserPlatformConnection.platform == "linkedin"
        ).first()
        
        if existing:
            # Update existing
            existing.access_token = request.access_token
            existing.platform_user_id = urn
            existing.profile_name = full_name
            existing.is_active = True
            db.commit()
            return {"status": "updated", "profile": full_name}
        else:
            # Create new
            new_conn = UserPlatformConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                platform="linkedin",
                access_token=request.access_token,
                platform_user_id=urn,
                profile_name=full_name,
                is_active=True
            )
            db.add(new_conn)
            db.commit()
            return {"status": "connected", "profile": full_name}
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/connections/{platform}")
def disconnect_platform(platform: str, user_id: str, db: Session = Depends(get_db)):
    """Disconnect a platform."""
    conn = db.query(UserPlatformConnection).filter(
        UserPlatformConnection.user_id == user_id,
        UserPlatformConnection.platform == platform
    ).first()
    
    if conn:
        db.delete(conn)
        db.commit()
        return {"status": "disconnected"}
    
    raise HTTPException(status_code=404, detail="Connection not found")

@router.get("/login/linkedin")
def login_linkedin(user_id: str, redirect_uri: str):
    """Generate the LinkedIn OAuth login URL."""
    publisher = SocialPublisher()
    
    # Use state to pass user_id safely through the flow
    state = user_id
    
    try:
        auth_url = publisher.get_authorization_url(redirect_uri, state)
        return {"url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback/linkedin")
def callback_linkedin(
    code: str, 
    state: str, 
    redirect_uri: str, # This must match what was sent in login
    db: Session = Depends(get_db)
):
    """Handle the OAuth callback from LinkedIn."""
    publisher = SocialPublisher()
    user_id = state # Recover user_id from state
    
    try:
        # Exchange code for token
        token_data = publisher.exchange_code_for_token(code, redirect_uri)
        access_token = token_data.get("access_token")
        
        if not access_token:
             raise Exception("No access token returned")

        # Now reuse the existing connect logic logic to save the connection
        # Verify Token & Get Profile (This also validates the connection works)
        profile = publisher.get_linkedin_profile(access_token)
        
        # Profile ID (URN) - OIDC 'sub' is raw ID, need to construct proper URN
        raw_id = profile.get("id") or profile.get("sub")
        # LinkedIn UGC Posts API requires urn:li:person:{id} format
        urn = f"urn:li:person:{raw_id}" if raw_id and not raw_id.startswith("urn:") else raw_id
        # Construct Name
        if "localizedFirstName" in profile:
            fname = profile.get("localizedFirstName", "")
            lname = profile.get("localizedLastName", "")
            full_name = f"{fname} {lname}".strip()
        else:
             # Fallback for newer API responses or limited scopes
             full_name = profile.get("name", "LinkedIn User")
        
        # Check for existing connection
        existing = db.query(UserPlatformConnection).filter(
            UserPlatformConnection.user_id == user_id,
            UserPlatformConnection.platform == "linkedin"
        ).first()
        
        if existing:
            existing.access_token = access_token
            existing.platform_user_id = urn
            existing.profile_name = full_name
            existing.is_active = True
            db.commit()
        else:
            new_conn = UserPlatformConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                platform="linkedin",
                access_token=access_token,
                platform_user_id=urn,
                profile_name=full_name,
                is_active=True
            )
            db.add(new_conn)
            db.commit()
            
        return {"status": "connected", "profile": full_name}
        
    except Exception as e:
        print(f"\n[ERROR] OAuth Callback Failed!")
        print(f"[ERROR] Code: {code}")
        print(f"[ERROR] Redirect URI: {redirect_uri}")
        print(f"[ERROR] Exception: {str(e)}")
        # If it's a requests exception, try to print body
        if hasattr(e, 'response') and e.response is not None:
             print(f"[ERROR] Upstream Response: {e.response.text}")
             
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")

@router.get("/linkedin/targets")
def get_linkedin_targets(user_id: str, db: Session = Depends(get_db)):
    """
    Get a list of potential targets (Person or Organizations) for the user.
    """
    # Get Connection
    conn = db.query(UserPlatformConnection).filter(
        UserPlatformConnection.user_id == user_id, 
        UserPlatformConnection.platform == "linkedin",
        UserPlatformConnection.is_active == True
    ).first()
    
    if not conn or not conn.access_token:
        # Instead of 404, return empty or specific error to prompt reconnect
        raise HTTPException(status_code=400, detail="LinkedIn not connected")
        
    publisher = SocialPublisher()
    targets = []
    
    # 1. Add Self (Person) - Use stored details or fetch fresh
    # Ensure URN is in proper format
    user_urn = conn.platform_user_id
    if user_urn and not user_urn.startswith("urn:"):
        user_urn = f"urn:li:person:{user_urn}"
    targets.append({
        "urn": user_urn,
        "name": conn.profile_name or "Personal Profile",
        "type": "person", 
        "image": None # Could fetch profile picture if needed
    })
    
    # 2. Fetch Organizations
    try:
        orgs = publisher.get_user_organizations(conn.access_token)
        targets.extend(orgs)
    except Exception as e:
        print(f"Error fetching orgs: {e}")
        # Don't fail the whole request if orgs fail (e.g. scope missing)
        pass
        
    return targets

@router.get("/login/twitter")
def login_twitter(user_id: str, redirect_uri: str):
    """Generate Twitter OAuth login URL."""
    publisher = SocialPublisher()
    
    # Generate PKCE verifier
    # In a real app, store this in DB/Redis mapped to state.
    # For MVP, we'll send it back to client to store in LocalStorage.
    import secrets
    code_verifier = secrets.token_urlsafe(32)
    
    state = user_id
    
    try:
        auth_url = publisher.get_twitter_auth_url(redirect_uri, state, code_verifier)
        return {"url": auth_url, "code_verifier": code_verifier}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback/twitter")
def callback_twitter(
    code: str, 
    state: str,
    code_verifier: str,
    redirect_uri: str,
    db: Session = Depends(get_db)
):
    """Handle Twitter OAuth callback."""
    publisher = SocialPublisher()
    user_id = state
    
    try:
        # Exchange code
        token_data = publisher.exchange_twitter_code(code, redirect_uri, code_verifier)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise Exception("No access token returned")
            
        # Get User Info
        user_info = publisher.get_twitter_user(access_token)
        platform_user_id = user_info.get("id")
        username = user_info.get("username")
        
        # Save Connection
        existing = db.query(UserPlatformConnection).filter(
            UserPlatformConnection.user_id == user_id,
            UserPlatformConnection.platform == "twitter"
        ).first()

        if existing:
            existing.access_token = access_token
            existing.platform_user_id = platform_user_id
            existing.profile_name = f"@{username}"
            existing.is_active = True
            db.commit()
        else:
             new_conn = UserPlatformConnection(
                id=str(uuid.uuid4()),
                user_id=user_id,
                platform="twitter",
                access_token=access_token,
                platform_user_id=platform_user_id,
                profile_name=f"@{username}",
                is_active=True
            )
             db.add(new_conn)
             db.commit()
             
        return {"status": "connected", "profile": f"@{username}"}

    except Exception as e:
        print(f"Twitter OAuth Error: {e}")
        raise HTTPException(status_code=400, detail=f"Twitter OAuth failed: {str(e)}")

@router.post("/share")
def share_content(request: ShareRequest, user_id: str, db: Session = Depends(get_db)):
    """Share content to a connected platform."""
    if request.platform not in ["linkedin", "twitter"]:
        raise HTTPException(status_code=400, detail="Platform not supported.")
        
    # Get Connection
    conn = db.query(UserPlatformConnection).filter(
        UserPlatformConnection.user_id == user_id,
        UserPlatformConnection.platform == request.platform,
        UserPlatformConnection.is_active == True
    ).first()
    
    if not conn or not conn.access_token:
        raise HTTPException(status_code=400, detail=f"{request.platform.capitalize()} not connected.")
        
    publisher = SocialPublisher()
    
    try:
        response = None
        if request.platform == "linkedin":
            # Ensure URN is in proper format
            target_urn = request.target_urn or conn.platform_user_id
            if target_urn and not target_urn.startswith("urn:"):
                target_urn = f"urn:li:person:{target_urn}"
            response = publisher.publish_to_linkedin(
                access_token=conn.access_token,
                user_urn=target_urn,
                text=request.content,
                url=request.url,
                title=request.title
            )
        elif request.platform == "twitter":
             # Twitter just needs text (links embedded in text)
             # If url provided, append it to content
             text = request.content
             if request.url:
                 text = f"{text}\n\n{request.url}"
                 
             response = publisher.post_tweet(conn.access_token, text)
             
        return {"status": "published", "platform_response": response}
        
    except Exception as e:
        # Log error for debugging
        import traceback
        print(f"SHARE ERROR: {str(e)}")
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
