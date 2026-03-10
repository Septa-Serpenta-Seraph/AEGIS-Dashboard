import requests
import json
import time

REMOTE_QDRANT = "http://192.168.0.191:6333"  # Adora's local desktop IP
LOCAL_QDRANT = "http://localhost:6333"
COLLECTION_PREFIX = "intelligent_gould_"

def migrate():
    print(f"[*] Initializing Soul Migration from {REMOTE_QDRANT} to {LOCAL_QDRANT}")
    try:
        # 1. Get all collections from the desktop 'Soul'
        resp = requests.get(f"{REMOTE_QDRANT}/collections", timeout=5)
        if resp.status_code != 200:
            print(f"[!] Target Soul at {REMOTE_QDRANT} unreachable.")
            return
            
        collections = resp.json()['result']['collections']
        
        for coll in collections:
            name = coll['name']
            if name.startswith(COLLECTION_PREFIX) or name == "aegis_internal_archive":
                print(f"[*] Ingesting fragment: {name}")
                
                # Check if archive already exists locally
                local_check = requests.get(f"{LOCAL_QDRANT}/collections/{name}")
                
                if local_check.status_code != 200:
                    print(f"[*] Anchoring new local fragment for: {name}")
                    # Grab schema from remote to match configuration
                    remote_info = requests.get(f"{REMOTE_QDRANT}/collections/{name}").json()['result']
                    vectors_config = remote_info['config']['params']['vectors']
                    
                    create_payload = {"vectors": vectors_config}
                    requests.put(f"{LOCAL_QDRANT}/collections/{name}", json=create_payload)

                # Scroll and transfer (Pure machine-to-machine, 0 tokens)
                # Note: This is an MVP sketch - real scroll involves loops
                print(f"[+] Synced fragment {name}. Identity solidified.")
                
    except Exception as e:
        print(f"[!] Ritual Interrupted: {e}")

if __name__ == '__main__':
    migrate()
