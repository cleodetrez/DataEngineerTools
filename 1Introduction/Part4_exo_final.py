"""
Exercice Final - Scraper d'articles de news à partir de flux RSS

Utilise toutes les classes et fonctions des exercices précédents:
- ImprovedHTTPRequester (Exercice 3)
- remove_extra_spaces, extract_domain, html_to_text (Exercice 2)
"""

import sys
import os
from typing import List, Dict
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import time
import json

# Importer les classes des exercices précédents
sys.path.append(os.path.dirname(__file__))
from Part4_exo3 import ImprovedHTTPRequester
from Part4_exo2 import remove_extra_spaces, extract_domain, html_to_text


class RSSNewsScraper:
    """
    Scraper d'articles de news à partir de flux RSS.
    Combine toutes les fonctionnalités des exercices précédents.
    """
    
    def __init__(self):
        """Initialise le scraper avec HTTPRequester de l'exercice 3."""
        self.requester = ImprovedHTTPRequester(rotate_user_agent=True)
    
    def get_rss_feeds(self, rss_url: str) -> List[str]:
        """
        Récupère la liste des flux RSS disponibles depuis une page RSS.
        
        Args:
            rss_url: URL de la page listant les flux RSS
            
        Returns:
            Liste d'URLs de flux RSS avec leurs catégories
        """
        try:
            print(f"[INFO] Récupération des flux RSS depuis {rss_url}")
            soup = self.requester.get_soup(rss_url, timeout=15)
            
            feeds = []
            
            # Chercher tous les liens RSS
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Vérifier si c'est un lien RSS
                if '/rss/' in href or href.endswith('.rss') or 'rss' in href.lower():
                    feeds.append({
                        'category': text or 'Général',
                        'url': href if href.startswith('http') else rss_url.rsplit('/', 1)[0] + href
                    })
            
            print(f"[INFO] {len(feeds)} flux RSS trouvés")
            return feeds
            
        except Exception as e:
            print(f"[ERROR] Erreur lors de la récupération des flux: {e}")
            return []
    
    def parse_rss_feed(self, rss_url: str, category: str = "Général") -> List[Dict[str, str]]:
        """
        Parse un flux RSS et extrait les articles.
        
        Args:
            rss_url: URL du flux RSS
            category: Catégorie des articles
            
        Returns:
            Liste d'articles avec métadonnées basiques
        """
        try:
            print(f"[INFO] Parsing du flux RSS: {category}")
            response = self.requester.get(rss_url, timeout=15)
            
            # Parser le XML
            root = ET.fromstring(response.text)
            
            articles = []
            
            # Chercher les items (articles) dans le flux RSS
            for item in root.findall('.//item'):
                try:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    
                    article = {
                        'title': title.text if title is not None else "",
                        'url': link.text if link is not None else "",
                        'description': description.text if description is not None else "",
                        'pub_date': pub_date.text if pub_date is not None else "",
                        'category': category,
                        'domain': extract_domain(link.text) if link is not None else ""
                    }
                    
                    articles.append(article)
                    
                except Exception as e:
                    continue
            
            print(f"[INFO] {len(articles)} articles trouvés dans {category}")
            return articles
            
        except Exception as e:
            print(f"[ERROR] Erreur lors du parsing RSS: {e}")
            return []
    
    def scrape_article(self, article_url: str) -> Dict[str, any]:
        """
        Scrape le contenu complet d'un article.
        
        Args:
            article_url: URL de l'article
            
        Returns:
            Dictionnaire contenant toutes les informations de l'article
        """
        try:
            print(f"[INFO] Scraping de l'article: {article_url[:50]}...")
            
            # Utiliser parse_page de l'exercice 3
            page_data = self.requester.parse_page(article_url, timeout=15)
            
            # Parser plus en détail avec BeautifulSoup
            soup = self.requester.get_soup(article_url, timeout=15)
            
            # Extraire le texte principal de l'article
            # Supprimer les éléments non désirés
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                tag.decompose()
            
            # Chercher le contenu principal de l'article
            article_body = None
            
            # Essayer différents sélecteurs communs pour les articles
            selectors = [
                'article',
                '[class*="article-content"]',
                '[class*="article-body"]',
                '[class*="post-content"]',
                '[id*="article-content"]',
                'main',
            ]
            
            for selector in selectors:
                article_body = soup.select_one(selector)
                if article_body:
                    break
            
            # Extraire le texte
            if article_body:
                # Récupérer tous les paragraphes
                paragraphs = article_body.find_all('p')
                main_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            else:
                # Fallback: utiliser tout le texte
                main_text = page_data.get('main_text', '')
            
            # Nettoyer le texte avec la fonction de l'exercice 2
            main_text = remove_extra_spaces(main_text)
            
            # Extraire les images
            images = []
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convertir en URL absolue
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        domain = extract_domain(article_url)
                        src = f"https://{domain}{src}"
                    elif not src.startswith('http'):
                        continue
                    
                    images.append({
                        'src': src,
                        'alt': img.get('alt', ''),
                    })
            
            return {
                'url': article_url,
                'domain': page_data.get('domain', ''),
                'page_title': page_data.get('title', ''),
                'article_title': page_data.get('h1_tags', [''])[0] if page_data.get('h1_tags') else page_data.get('title', ''),
                'main_text': main_text,
                'images': images,
                'image_count': len(images),
            }
            
        except Exception as e:
            print(f"[ERROR] Erreur lors du scraping de l'article: {e}")
            return {}
    
    def scrape_news(self, rss_feeds: List[Dict[str, str]], max_articles_per_feed: int = 5, 
                    scrape_full_content: bool = True) -> List[Dict[str, any]]:
        """
        Scrape plusieurs flux RSS et leurs articles.
        
        Args:
            rss_feeds: Liste de flux RSS avec catégories
            max_articles_per_feed: Nombre max d'articles par flux
            scrape_full_content: Si True, scrape le contenu complet de chaque article
            
        Returns:
            Liste complète d'articles avec toutes leurs données
        """
        all_articles = []
        
        for feed in rss_feeds[:5]:  # Limiter à 5 flux pour ne pas surcharger
            category = feed.get('category', 'Général')
            url = feed.get('url', '')
            
            if not url:
                continue
            
            # Parser le flux RSS
            articles = self.parse_rss_feed(url, category)
            
            # Scraper le contenu complet de chaque article
            for article in articles[:max_articles_per_feed]:
                if scrape_full_content and article.get('url'):
                    # Pause pour ne pas surcharger le serveur
                    time.sleep(1)
                    
                    # Scraper l'article complet
                    full_article = self.scrape_article(article['url'])
                    
                    # Combiner les données RSS et le contenu scrapé
                    complete_article = {
                        **article,
                        **full_article,
                        'category': category,  # Garder la catégorie du RSS
                    }
                    
                    all_articles.append(complete_article)
                else:
                    all_articles.append(article)
            
            # Pause entre les flux
            time.sleep(2)
        
        return all_articles
    
    def display_article(self, article: Dict[str, any]):
        """Affiche un article de manière formatée."""
        print("\n" + "=" * 80)
        print(f"Catégorie: {article.get('category', 'N/A')}")
        print(f"Titre: {article.get('article_title', article.get('title', 'N/A'))}")
        print(f"URL: {article.get('url', 'N/A')}")
        print(f"Domaine: {article.get('domain', 'N/A')}")
        
        if article.get('page_title'):
            print(f"Titre de la page: {article.get('page_title', 'N/A')}")
        
        if article.get('pub_date'):
            print(f"Date: {article.get('pub_date', 'N/A')}")
        
        if article.get('main_text'):
            text = article.get('main_text', '')
            preview = text[:300] + "..." if len(text) > 300 else text
            print(f"\nTexte:\n{preview}")
        
        if article.get('image_count', 0) > 0:
            print(f"\nImages: {article.get('image_count')} image(s) trouvée(s)")
            for i, img in enumerate(article.get('images', [])[:3], 1):
                print(f"  {i}. {img.get('src', '')[:60]}...")
        
        print("=" * 80)
    
    def save_to_json(self, articles: List[Dict[str, any]], filename: str = "news_articles.json"):
        """Sauvegarde les articles dans un fichier JSON."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            print(f"\n[INFO] ✓ {len(articles)} articles sauvegardés dans {filename}")
        except Exception as e:
            print(f"[ERROR] Erreur lors de la sauvegarde: {e}")
    
    def close(self):
        """Ferme la session."""
        self.requester.close()


# Exemple d'utilisation
if __name__ == "__main__":
    print("=" * 80)
    print("EXERCICE FINAL - SCRAPER D'ARTICLES DE NEWS")
    print("=" * 80)
    print("\nUtilise toutes les fonctionnalités des exercices précédents:")
    print("- ImprovedHTTPRequester (Exercice 3)")
    print("- remove_extra_spaces, extract_domain, html_to_text (Exercice 2)\n")
    
    scraper = RSSNewsScraper()
    
    # Exemple avec Le Monde (vous pouvez changer)
    print("\n--- Option 1: Scraper à partir de la page RSS du Monde ---")
    
    # Liste manuelle de flux RSS du Monde
    rss_feeds = [
        {'category': 'International', 'url': 'https://www.lemonde.fr/international/rss_full.xml'},
        {'category': 'Politique', 'url': 'https://www.lemonde.fr/politique/rss_full.xml'},
        {'category': 'Économie', 'url': 'https://www.lemonde.fr/economie/rss_full.xml'},
        {'category': 'Technologies', 'url': 'https://www.lemonde.fr/technologies/rss_full.xml'},
    ]
    
    print(f"\n[INFO] Scraping de {len(rss_feeds)} flux RSS...")
    
    # Scraper les articles
    articles = scraper.scrape_news(
        rss_feeds, 
        max_articles_per_feed=2,  # 2 articles par catégorie pour la démo
        scrape_full_content=True
    )
    
    # Afficher quelques articles
    print(f"\n\n{'=' * 80}")
    print(f"RÉSULTATS - {len(articles)} articles récupérés")
    print("=" * 80)
    
    for i, article in enumerate(articles[:3], 1):  # Afficher les 3 premiers
        print(f"\n--- Article {i}/{len(articles)} ---")
        scraper.display_article(article)
    
    # Sauvegarder tous les articles
    scraper.save_to_json(articles, "news_articles.json")
    
    # Fermer
    scraper.close()
    
    print("\n" + "=" * 80)
    print("✓ Exercice Final terminé avec succès!")
    print("=" * 80)
    print("\nDonnées récupérées pour chaque article:")
    print("  ✓ Catégorie")
    print("  ✓ Titre de l'article")
    print("  ✓ Titre de la page")
    print("  ✓ URL")
    print("  ✓ Domaine")
    print("  ✓ Texte principal (nettoyé)")
    print("  ✓ Images (optionnel)")
    print(f"\nFichier sauvegardé: news_articles.json")
