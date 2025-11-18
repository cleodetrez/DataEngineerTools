import requests
import time
import random
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class ImprovedHTTPRequester:
    """
    Classe améliorée pour effectuer des requêtes HTTP avec rotation de UserAgent,
    récupération d'objets BeautifulSoup et parsing HTML avancé.
    """
    
    # Liste de User Agents pour rotation aléatoire
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    ]
    
    DEFAULT_TIMEOUT = 10  # secondes
    
    def __init__(self, user_agents: Optional[List[str]] = None, rotate_user_agent: bool = True):
        """
        Initialise le requester avec rotation de UserAgent.
        
        Args:
            user_agents: Liste personnalisée de UserAgents (optionnel)
            rotate_user_agent: Si True, effectue une rotation aléatoire des UserAgents
        """
        self.user_agents = user_agents or self.USER_AGENTS
        self.rotate_user_agent = rotate_user_agent
        self.session = requests.Session()
        self._update_user_agent()
    
    def _update_user_agent(self):
        """Met à jour le UserAgent de la session (rotation aléatoire si activée)."""
        if self.rotate_user_agent:
            user_agent = random.choice(self.user_agents)
        else:
            user_agent = self.user_agents[0]
        
        self.session.headers.update({'User-Agent': user_agent})
    
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
        # Rotation du UserAgent avant chaque requête
        if self.rotate_user_agent:
            self._update_user_agent()
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
        # Rotation du UserAgent avant chaque requête
        if self.rotate_user_agent:
            self._update_user_agent()
        return self._request_with_retry('POST', url, timeout, max_retries, retry_delay, **kwargs)
    
    def get_soup(self, url: str, timeout: Optional[float] = None, max_retries: int = 3,
                 retry_delay: float = 1.0, parser: str = 'html.parser', **kwargs) -> BeautifulSoup:
        """
        Récupère l'objet BeautifulSoup d'une URL.
        
        Args:
            url: URL cible
            timeout: Timeout en secondes (défaut: DEFAULT_TIMEOUT)
            max_retries: Nombre maximum de tentatives
            retry_delay: Délai entre les tentatives
            parser: Parser à utiliser ('html.parser', 'lxml', etc.)
            **kwargs: Arguments additionnels pour requests.get
            
        Returns:
            Objet BeautifulSoup
            
        Raises:
            requests.exceptions.RequestException: Si la requête échoue
        """
        response = self.get(url, timeout, max_retries, retry_delay, **kwargs)
        return BeautifulSoup(response.text, parser)
    
    def parse_page(self, url: str, timeout: Optional[float] = None, 
                   max_retries: int = 3) -> Dict[str, Any]:
        """
        Parse une page HTML et extrait les informations principales.
        
        Args:
            url: URL de la page à parser
            timeout: Timeout en secondes
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Dictionnaire contenant:
                - title: Titre de la page (balise <title>)
                - h1_tags: Liste de tous les H1
                - image_links: Liste des liens vers les images
                - external_links: Liste des liens sortants vers d'autres sites
                - main_text: Texte principal de la page (nettoyé)
                - url: URL de la page
                - domain: Domaine de la page
        """
        soup = self.get_soup(url, timeout, max_retries)
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Récupération du titre
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else ""
        
        # Récupération de tous les H1
        h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
        
        # Récupération des liens vers les images
        image_links = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Convertir les liens relatifs en absolus
                absolute_url = urljoin(url, src)
                image_links.append(absolute_url)
        
        # Récupération des liens sortants vers d'autres sites
        external_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            parsed_link = urlparse(absolute_url)
            
            # Vérifier si c'est un lien externe
            if parsed_link.netloc and parsed_link.netloc != domain:
                external_links.append(absolute_url)
        
        # Récupération du texte principal
        # Supprimer les scripts et styles
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Extraire le texte
        main_text = soup.get_text()
        
        # Nettoyer le texte
        lines = [line.strip() for line in main_text.split('\n')]
        lines = [line for line in lines if line]
        main_text = '\n'.join(lines)
        
        return {
            'url': url,
            'domain': domain,
            'title': title_text,
            'h1_tags': h1_tags,
            'image_links': image_links,
            'external_links': external_links,
            'main_text': main_text[:1000] + '...' if len(main_text) > 1000 else main_text
        }
    
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
            
            # Rotation du UserAgent pour le retry
            if self.rotate_user_agent:
                self._update_user_agent()
            
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
    print("=" * 80)
    print("Test de la classe ImprovedHTTPRequester")
    print("=" * 80)
    
    with ImprovedHTTPRequester(rotate_user_agent=True) as requester:
        # Test 1: Récupération d'un objet soup
        print("\n1. Test de get_soup()")
        print("-" * 80)
        try:
            soup = requester.get_soup("https://www.esiee.fr/")
            print(f"Titre de la page: {soup.title.string if soup.title else 'Non trouvé'}")
            print(f"Nombre de liens: {len(soup.find_all('a'))}")
        except Exception as e:
            print(f"Erreur: {e}")
        
        # Test 2: Parsing complet d'une page
        print("\n2. Test de parse_page()")
        print("-" * 80)
        try:
            result = requester.parse_page("https://www.esiee.fr/")
            
            print(f"\nURL: {result['url']}")
            print(f"Domaine: {result['domain']}")
            print(f"Titre: {result['title']}")
            print(f"\nNombre de H1: {len(result['h1_tags'])}")
            if result['h1_tags']:
                print(f"H1 trouvés: {result['h1_tags'][:3]}")
            
            print(f"\nNombre d'images: {len(result['image_links'])}")
            if result['image_links']:
                print(f"Exemples d'images: {result['image_links'][:3]}")
            
            print(f"\nNombre de liens externes: {len(result['external_links'])}")
            if result['external_links']:
                print(f"Exemples de liens externes: {result['external_links'][:3]}")
            
            print(f"\nTexte principal (extrait):")
            print(result['main_text'][:500] + "...")
            
        except Exception as e:
            print(f"Erreur: {e}")
        
        # Test 3: Vérification de la rotation des UserAgents
        print("\n3. Test de rotation des UserAgents")
        print("-" * 80)
        user_agents_used = set()
        for i in range(5):
            requester._update_user_agent()
            ua = requester.session.headers.get('User-Agent')
            user_agents_used.add(ua)
            print(f"Requête {i+1}: {ua[:50]}...")
        
        print(f"\nNombre de UserAgents différents utilisés: {len(user_agents_used)}")
