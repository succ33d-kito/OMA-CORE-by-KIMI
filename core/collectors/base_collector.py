"""O.M.A.-C.O.R.E. Base Collector"""
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class BaseCollector:
    """Clase base para todos los collectors de OMA-CORE."""
    
    def __init__(self, name: str, source_confidence: float = 0.5):
        self.name = name
        self.source_confidence = source_confidence
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OMA-CORE/2.0",
            "Accept": "application/json",
        })
        self.stats = {
            "requests_made": 0,
            "requests_failed": 0,
            "events_generated": 0,
            "last_run": None,
        }

    def collect(self):
        raise NotImplementedError

    def _make_request(self, url: str, params: Optional[Dict] = None, 
                      timeout: int = 30, headers: Optional[Dict] = None) -> Optional[Dict]:
        try:
            req_headers = dict(self.session.headers)
            if headers:
                req_headers.update(headers)
            response = self.session.get(url, params=params, timeout=timeout, headers=req_headers)
            response.raise_for_status()
            self.stats["requests_made"] += 1
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                return response.json()
            else:
                return {"text": response.text, "content_type": content_type}
        except requests.exceptions.Timeout:
            self.stats["requests_failed"] += 1
            print(f"[{self.name}] Timeout en {url}")
            return None
        except requests.exceptions.HTTPError as e:
            self.stats["requests_failed"] += 1
            print(f"[{self.name}] HTTP Error {e.response.status_code}: {url}")
            return None
        except requests.exceptions.ConnectionError:
            self.stats["requests_failed"] += 1
            print(f"[{self.name}] Error de conexión: {url}")
            return None
        except Exception as e:
            self.stats["requests_failed"] += 1
            print(f"[{self.name}] Error inesperado: {e}")
            return None

    def _post_request(self, url: str, data: Optional[Dict] = None, 
                      json_data: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
        try:
            response = self.session.post(url, data=data, json=json_data, timeout=timeout)
            response.raise_for_status()
            self.stats["requests_made"] += 1
            return response.json() if "json" in response.headers.get("content-type", "").lower() else {"text": response.text}
        except Exception as e:
            self.stats["requests_failed"] += 1
            print(f"[{self.name}] POST Error: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "success_rate": (self.stats["requests_made"] - self.stats["requests_failed"]) / max(self.stats["requests_made"], 1),
            "source_confidence": self.source_confidence,
        }
