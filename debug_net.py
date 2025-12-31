import requests
import socket
import ssl
import os
import sys

print(f"Python executing: {sys.executable}")
print("Checking for Proxy Environment Variables...")
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    print(f"{key}: {os.environ.get(key)}")

print("\n--- TEST 1: Direct Socket Connection ---")
try:
    # Force IPv4 resolution
    addr_info = socket.getaddrinfo('www.linkedin.com', 443, socket.AF_INET, socket.SOCK_STREAM)
    ip = addr_info[0][4][0]
    print(f"Resolved www.linkedin.com to {ip}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect((ip, 443))
    
    context = ssl.create_default_context()
    ssock = context.wrap_socket(sock, server_hostname='www.linkedin.com')
    print("SSL Handshake: SUCCESS")
    print(f"Cipher: {ssock.cipher()}")
    ssock.close()
    sock.close()
except Exception as e:
    print(f"Socket/SSL Error: {e}")

print("\n--- TEST 2: Requests Library (Simple GET) ---")
try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    resp = requests.get('https://www.linkedin.com', headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
except Exception as e:
    print(f"Requests GET Error: {e}")

print("\n--- TEST 3: Requests Library (POST Token) ---")
try:
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    # This matches the failing call structure
    resp = requests.post(url, data={'grant_type': 'authorization_code'}, verify=False, timeout=10)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text[:100]}")
except Exception as e:
    print(f"Requests POST Error: {e}")

print("\n--- TEST 4: Requests with FORCED IPv4 ---")
def force_ipv4_monkeypatch():
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        # Filter results to only return AF_INET (IPv4)
        res = old_getaddrinfo(*args, **kwargs)
        return [r for r in res if r[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo
    return old_getaddrinfo

try:
    # Apply patch
    original_gai = force_ipv4_monkeypatch()
    print("Forced IPv4 enabled.")
    
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    # Verify=False to rule out SSL cert logic (though handshake itself is what fails usually)
    resp = requests.post(url, data={'grant_type': 'authorization_code'}, verify=False, timeout=10)
    print(f"Status Code: {resp.status_code}")
    
    # Restore
    socket.getaddrinfo = original_gai
except Exception as e:
    print(f"Forced IPv4 Error: {e}")

def test_token_exchange():
    print("\n--- Testing Token Exchange Simulation (IPv4 FORCE + Verify=False) ---")
    
    # URL to test (api.linkedin.com caused the timeout)
    url = "https://api.linkedin.com/v2/userinfo"
    
    # Store original getaddrinfo
    old_getaddrinfo = socket.getaddrinfo

    # Workaround for IPv6 issues on Windows
    def new_getaddrinfo(*args, **kwargs):
        res = old_getaddrinfo(*args, **kwargs)
        # Filter for IPv4 (Authorized Family 2)
        return [r for r in res if r[0] == socket.AF_INET]
    
    try:
        print(f"Applying IPv4 patch and requesting {url}...")
        socket.getaddrinfo = new_getaddrinfo
        
        response = requests.get(url, timeout=10, verify=False)
        if response.status_code == 200:
            print(f"FAILED (Unexpected 200 for dummy token): {response.status_code}")
        elif response.status_code == 401:
             print(f"SUCCESS! Connection verified (got expected 401): {response.status_code}")
        else:
             print(f"Unknown status: {response.status_code}")
        
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        print("Restoring original socket.getaddrinfo...")
        socket.getaddrinfo = old_getaddrinfo

if __name__ == "__main__":
    # Exclusive test for the failing endpoint
    test_token_exchange()
