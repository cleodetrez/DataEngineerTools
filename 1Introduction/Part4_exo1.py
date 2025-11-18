import requests
import time
from typing import Optional, Dict, Any


class HTTPRequester:
    """
    Classe pour effectuer des requêtes HTTP avec UserAgent fixe, timeout configurable et retry récursif.
    """
    
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    DEFAULT_TIMEOUT = 10  # secondes
    
    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialise le requester avec un UserAgent.
        
        Args:
            user_agent: UserAgent personnalisé (optionnel)
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def get(self, url: str, timeout: Optional[float] = None, max_retries: int = 3, 
            retry_delay: float = 1.0, **kwargs) -> requests.Response:
        """
        Effectue une requête GET avec mécanisme de retry récursif.
        
        Args:
            url: URL cible
            timeout: Timeout en secondes (défaut: DEFAULT_TIMEOUT)
            max_retries: Nombre maximum de tentatives
            retry_delay: Délai entre les tentatives en secondes
            **kwargs: Arguments additionnels pour requests.get
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: Si toutes les tentatives échouent
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        return self._request_with_retry('GET', url, timeout, max_retries, retry_delay, **kwargs)
    
    def post(self, url: str, timeout: Optional[float] = None, max_retries: int = 3,
             retry_delay: float = 1.0, **kwargs) -> requests.Response:
        """
        Effectue une requête POST avec mécanisme de retry récursif.
        
        Args:
            url: URL cible
            timeout: Timeout en secondes (défaut: DEFAULT_TIMEOUT)
            max_retries: Nombre maximum de tentatives
            retry_delay: Délai entre les tentatives en secondes
            **kwargs: Arguments additionnels pour requests.post
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: Si toutes les tentatives échouent
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        return self._request_with_retry('POST', url, timeout, max_retries, retry_delay, **kwargs)
    
    def _request_with_retry(self, method: str, url: str, timeout: float, 
                           max_retries: int, retry_delay: float, 
                           current_attempt: int = 0, **kwargs) -> requests.Response:
        """
        Méthode récursive pour effectuer des requêtes avec retry.
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            url: URL cible
            timeout: Timeout en secondes
            max_retries: Nombre maximum de tentatives
            retry_delay: Délai entre les tentatives
            current_attempt: Numéro de la tentative actuelle
            **kwargs: Arguments additionnels pour la requête
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: Si toutes les tentatives échouent
        """
        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
            
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            if current_attempt >= max_retries:
                print(f"Echec apres {max_retries + 1} tentatives pour {url}")
                raise e
            
            print(f"Tentative {current_attempt + 1}/{max_retries + 1} echouee pour {url}. "
                  f"Nouvelle tentative dans {retry_delay}s...")
            time.sleep(retry_delay)
            
            # Appel récursif
            return self._request_with_retry(
                method, url, timeout, max_retries, retry_delay, 
                current_attempt + 1, **kwargs
            )
    
    def close(self):
        """Ferme la session."""
        self.session.close()
    
    def __enter__(self):
        """Support du context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme automatiquement la session."""
        self.close()


# Exemple d'utilisation
if __name__ == "__main__":
    # Utilisation basique
    requester = HTTPRequester()
    
    try:
        # Requête GET avec timeout par défaut
        response = requester.get("https://httpbin.org/get")
        print(f"Status: {response.status_code}")
        print(f"Content: {response.json()}")
        
        # Requête GET avec timeout personnalisé
        response = requester.get("https://httpbin.org/delay/2", timeout=5)
        print(f"\nStatus avec timeout: {response.status_code}")
        
        # Requête POST
        data = {"key": "value"}
        response = requester.post("https://httpbin.org/post", json=data)
        print(f"\nPOST Status: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur: {e}")
    finally:
        requester.close()
    
    # Utilisation avec context manager
    print("\n--- Avec context manager ---")
    with HTTPRequester() as req:
        response = req.get("https://httpbin.org/get", max_retries=2)
        print(f"Status: {response.status_code}")
