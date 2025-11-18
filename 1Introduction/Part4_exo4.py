from typing import List, Dict
import time
import sys
import os
from bs4 import BeautifulSoup

# Importer les fonctions des exercices précédents
sys.path.append(os.path.dirname(__file__))
from Part4_exo2 import remove_extra_spaces, extract_domain, html_to_text
from Part4_exo3 import ImprovedHTTPRequester


class GoogleSearchScraper:
    """
    Classe pour scraper les résultats de recherche Google.
    Utilise ImprovedHTTPRequester de l'exercice 3 et DuckDuckGo comme alternative.
    """
    
    def __init__(self):
        """Initialise le scraper."""
        self.requester = ImprovedHTTPRequester(rotate_user_agent=True)
    
    def search_duckduckgo(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Effectue une recherche sur DuckDuckGo (plus permissif que Google).
        
        Args:
            query: Terme de recherche
            num_results: Nombre de résultats
            
        Returns:
            Liste des résultats
        """
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        
        try:
            print(f"[INFO] Recherche sur DuckDuckGo: '{query}'")
            soup = self.requester.get_soup(search_url, timeout=15)
            
            results = []
            search_results = soup.find_all('div', class_='result')
            
            print(f"[INFO] {len(search_results)} résultats trouvés")
            
            for result in search_results[:num_results]:
                try:
                    # Titre et URL
                    title_elem = result.find('a', class_='result__a')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    url = title_elem.get('href') if title_elem else ""
                    
                    # Description
                    desc_elem = result.find('a', class_='result__snippet')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    
                    # Nettoyer avec les fonctions de l'exercice 2
                    title = remove_extra_spaces(title)
                    description = remove_extra_spaces(description)
                    
                    if title and url:
                        if url.startswith('//'):
                            url = 'https:' + url
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'domain': extract_domain(url),
                            'description': description or "N/A"
                        })
                        
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            print(f"[ERROR] Erreur: {e}")
            return []
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Effectue une recherche (utilise DuckDuckGo car Google bloque le scraping).
        
        Args:
            query: Terme de recherche
            num_results: Nombre de résultats
            
        Returns:
            Liste des résultats
        """
        return self.search_duckduckgo(query, num_results)
    
    def search_and_display(self, query: str, num_results: int = 10):
        """
        Effectue une recherche et affiche les résultats.
        
        Args:
            query: Terme de recherche
            num_results: Nombre de résultats à afficher
        """
        print(f"\nRecherche pour: '{query}'")
        print("=" * 80)
        
        results = self.search(query, num_results)
        
        if not results:
            print("Aucun résultat trouvé.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Domaine: {result['domain']}")
            if result['description'] != "N/A":
                desc = result['description'][:150] + "..." if len(result['description']) > 150 else result['description']
                print(f"   Description: {desc}")
            print("-" * 80)
        
        print(f"\nTotal: {len(results)} résultats trouvés")
    
    def close(self):
        """Ferme la session du requester."""
        self.requester.close()


# Exemples d'utilisation
if __name__ == "__main__":
    print("=" * 80)
    print("EXERCICE 4 - SCRAPING DE MOTEUR DE RECHERCHE")
    print("=" * 80)
    print("\nUtilise les classes et fonctions des exercices précédents:")
    print("- ImprovedHTTPRequester (Exercice 3) : Requêtes HTTP avec rotation UserAgent")
    print("- remove_extra_spaces (Exercice 2) : Nettoyage du texte")
    print("- extract_domain (Exercice 2) : Extraction du domaine")
    print("\nNote: Utilise DuckDuckGo car Google bloque le scraping simple.\n")
    
    scraper = GoogleSearchScraper()
    
    # Test 1
    scraper.search_and_display("Python web scraping", num_results=5)
    
    # Pause
    time.sleep(2)
    
    # Test 2
    print("\n")
    scraper.search_and_display("BeautifulSoup tutorial", num_results=5)
    
    # Fermer
    scraper.close()
    
    print("\n" + "=" * 80)
    print("✓ Exercice 4 terminé avec succès!")
    print("=" * 80)
