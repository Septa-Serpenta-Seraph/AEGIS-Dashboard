import requests
import json

REMOTE_QDRANT = "http://192.168.0.191:6333"
LOCAL_QDRANT = "http://localhost:6333"

def migrate_full():
    print("[*] Starting Deep Migration...")
    try:
        remote_collections = requests.get(f"{REMOTE_QDRANT}/collections").json()['result']['collections']
        for coll in remote_collections:
            name = coll['name']
            if not name.startswith("intelligent_gould_"): continue
            
            print(f"[*] Ritual for {name}...")
            
            # 1. Re-create local collection with proper schema
            remote_info = requests.get(f"{REMOTE_QDRANT}/collections/{name}").json()['result']
            vectors_config = remote_info['config']['params']['vectors']
            
            requests.delete(f"{LOCAL_QDRANT}/collections/{name}") # Wipe incomplete
            requests.put(f"{LOCAL_QDRANT}/collections/{name}", json={"vectors": vectors_config})
            
            # 2. Scroll through remote points and push locally
            # We use the 'scroll' API to fetch all points
            offset = None
            total_synced = 0
            
            while True:
                scroll_payload = {"limit": 100, "with_payload": True, "with_vector": True}
                if offset: scroll_payload["offset"] = offset
                
                scroll_resp = requests.post(f"{REMOTE_QDRANT}/collections/{name}/points/scroll", json=scroll_payload).json()['result']
                points = scroll_resp['points']
                
                if not points: break
                
                # Push points
                requests.put(f"{LOCAL_QDRANT}/collections/{name}/points?wait=true", json={"points": points})
                
                total_synced += len(points)
                offset = scroll_resp.get('next_page_offset')
                if not offset: break
                
            print(f"[+] {name}: {total_synced} points migrated.")
            
    except Exception as e:
        print(f"[!] Migration Error: {e}")

if __name__ == '__main__':
    migrate_full()
