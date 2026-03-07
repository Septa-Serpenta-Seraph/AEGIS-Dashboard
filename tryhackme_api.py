"""
TryHackMe API client for AEGIS Dashboard.

Supports two modes:
1. Live mode (with VPN or API key) – fetches real data from THM.
2. Mock mode – returns realistic sample data for demo.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class TryHackMeClient:
    """
    Client for interacting with TryHackMe's API.
    """
    
    def __init__(self, mode: str = 'mock', api_key: Optional[str] = None):
        """
        Initialize the client.
        
        Args:
            mode: 'mock' (default) or 'live' (requires VPN or API key).
            api_key: Optional TryHackMe API key (for live mode).
        """
        self.mode = mode
        self.api_key = api_key
        self.base_url = 'https://tryhackme.com/api'
        
        # Mock data stores
        self._mock_profile = self._build_mock_profile()
        self._mock_rooms = self._build_mock_rooms()
        self._mock_progress = self._build_mock_progress()
    
    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    
    def get_profile(self) -> Dict[str, Any]:
        """Fetch user profile (rank, badges, join date, etc.)."""
        if self.mode == 'mock':
            return self._mock_profile
        
        # TODO: Implement live API call
        return {"error": "Live mode not yet implemented"}
    
    def get_rooms(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch rooms (with completion status if available).
        
        Args:
            limit: Max number of rooms to return.
        """
        if self.mode == 'mock':
            return self._mock_rooms[:limit]
        
        # TODO: Implement live API call
        return [{"error": "Live mode not yet implemented"}]
    
    def get_progress(self, days: int = 30) -> Dict[str, Any]:
        """
        Fetch progress timeline (rooms completed per day).
        
        Args:
            days: Number of past days to include.
        """
        if self.mode == 'mock':
            # Filter to last N days
            cutoff = (datetime.now() - timedelta(days=days)).timestamp()
            filtered = {k: v for k, v in self._mock_progress.items() 
                        if datetime.fromisoformat(k).timestamp() >= cutoff}
            return filtered
        
        # TODO: Implement live API call
        return {"error": "Live mode not yet implemented"}
    
    # ------------------------------------------------------------------
    # Mock data builders
    # ------------------------------------------------------------------
    
    def _build_mock_profile(self) -> Dict[str, Any]:
        """Generate a realistic mock THM profile."""
        return {
            "username": "adora",
            "rank": "Hacker",
            "rank_id": 5,
            "avatar": "https://tryhackme.com/images/avatars/default.svg",
            "join_date": "2025-01-15",
            "country": "US",
            "badges": [
                {"name": "Intro to Offensive Security", "earned": "2025-02-10"},
                {"name": "Network Security", "earned": "2025-02-28"},
                {"name": "Web Fundamentals", "earned": "2025-03-05"},
            ],
            "points": 1240,
            "rooms_completed": 17,
            "streak_days": 7,
            "subscribed": False,
        }
    
    def _build_mock_rooms(self) -> List[Dict[str, Any]]:
        """Generate a list of mock rooms with completion status."""
        rooms = [
            {
                "id": "bufferoverflowprep",
                "title": "Buffer Overflow Prep",
                "difficulty": "Medium",
                "category": "Exploitation",
                "completed": True,
                "completed_at": "2025-03-01",
                "stars": 4,
                "tags": ["buffer overflow", "binary exploitation", "oscp"],
            },
            {
                "id": "basicpentesting",
                "title": "Basic Pentesting",
                "difficulty": "Easy",
                "category": "Penetration Testing",
                "completed": True,
                "completed_at": "2025-02-20",
                "stars": 5,
                "tags": ["nmap", "gobuster", "hydra", "ssh"],
            },
            {
                "id": "vulnversity",
                "title": "Vulnversity",
                "difficulty": "Easy",
                "category": "Web Application Security",
                "completed": False,
                "completed_at": None,
                "stars": 3,
                "tags": ["file upload", "brute force", "reverse shell"],
            },
            {
                "id": "cyberheroes",
                "title": "Cyber Heroes",
                "difficulty": "Easy",
                "category": "Beginner",
                "completed": True,
                "completed_at": "2025-01-25",
                "stars": 5,
                "tags": ["intro", "cybersecurity", "threats"],
            },
            {
                "id": "blaster",
                "title": "Blaster",
                "difficulty": "Medium",
                "category": "Exploitation",
                "completed": False,
                "completed_at": None,
                "stars": 2,
                "tags": ["windows", "eternalblue", "metasploit"],
            },
            {
                "id": "overpass",
                "title": "Overpass",
                "difficulty": "Easy",
                "category": "Web Application Security",
                "completed": True,
                "completed_at": "2025-02-15",
                "stars": 4,
                "tags": ["password cracking", "ssh keys", "cron jobs"],
            },
        ]
        return rooms
    
    def _build_mock_progress(self) -> Dict[str, int]:
        """Generate mock daily completion counts."""
        # Generate last 60 days with some random completions
        progress = {}
        base_date = datetime.now() - timedelta(days=60)
        for i in range(60):
            date_str = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            # Simulate activity every 3–4 days
            if i % 4 == 0:
                progress[date_str] = 1
            elif i % 7 == 0:
                progress[date_str] = 2
            else:
                progress[date_str] = 0
        # Add a spike recently
        recent = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        progress[recent] = 3
        return progress
    
    # ------------------------------------------------------------------
    # Live API helpers (placeholder)
    # ------------------------------------------------------------------
    
    def _live_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make a live API request to TryHackMe."""
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        url = f'{self.base_url}/{endpoint.lstrip("/")}'
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {'error': str(e)}


# Singleton instance for easy import
_thm_client = TryHackMeClient(mode='mock')

def get_client() -> TryHackMeClient:
    """Return the shared THM client instance."""
    return _thm_client

def set_mode(mode: str, api_key: Optional[str] = None):
    """Re‑initialize the client with a new mode."""
    global _thm_client
    _thm_client = TryHackMeClient(mode=mode, api_key=api_key)