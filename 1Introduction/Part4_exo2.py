import re
from html import unescape
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def remove_extra_spaces(text: str) -> str:
    """
    Supprime tous les espaces superflus d'une string.
    - Remplace les multiples espaces par un seul
    - Supprime les espaces en début et fin de ligne
    - Remplace les multiples sauts de ligne par un seul
    
    Args:
        text: Texte avec espaces superflus
        
    Returns:
        Texte nettoyé sans espaces superflus
    """
    if not text:
        return text
    
    # Remplace les multiples espaces par un seul
    text = re.sub(r' +', ' ', text)
    
    # Remplace les multiples sauts de ligne par un seul
    text = re.sub(r'\n+', '\n', text)
    
    # Supprime les espaces en début et fin de chaque ligne
    lines = [line.strip() for line in text.split('\n')]
    
    # Supprime les lignes vides
    lines = [line for line in lines if line]
    
    # Rejoint les lignes
    return '\n'.join(lines)


def html_to_text(html_string: str, remove_scripts: bool = True) -> str:
    """
    Convertit une string HTML en texte intelligible.
    - Enlève les balises HTML
    - Décode les entités HTML (&nbsp;, &eacute;, etc.)
    - Supprime les caractères spéciaux
    - Nettoie les espaces superflus
    
    Args:
        html_string: String HTML à convertir
        remove_scripts: Si True, supprime les balises script et style
        
    Returns:
        Texte propre et lisible
    """
    if not html_string:
        return ""
    
    # Parse le HTML avec BeautifulSoup
    soup = BeautifulSoup(html_string, 'html.parser')
    
    # Supprime les scripts et styles
    if remove_scripts:
        for script in soup(['script', 'style']):
            script.decompose()
    
    # Extrait le texte
    text = soup.get_text()
    
    # Décode les entités HTML restantes
    text = unescape(text)
    
    # Supprime les espaces superflus
    text = remove_extra_spaces(text)
    
    return text


def extract_domain(url: str, include_subdomain: bool = False) -> str:
    """
    Extrait le domaine d'une URL.
    
    Args:
        url: URL complète
        include_subdomain: Si True, inclut le sous-domaine (www, api, etc.)
                          Si False, retourne uniquement le domaine principal
        
    Returns:
        Domaine extrait de l'URL
        
    Examples:
        >>> extract_domain("https://www.example.com/path?query=1")
        'example.com'
        >>> extract_domain("https://www.example.com/path?query=1", include_subdomain=True)
        'www.example.com'
        >>> extract_domain("https://api.github.com/users")
        'github.com'
    """
    if not url:
        return ""
    
    # Ajoute le schéma si absent pour que urlparse fonctionne correctement
    if not url.startswith(('http://', 'https://', '//')):
        url = 'http://' + url
    
    # Parse l'URL
    parsed = urlparse(url)
    netloc = parsed.netloc or parsed.path.split('/')[0]
    
    if include_subdomain:
        return netloc
    
    # Extrait le domaine principal (sans sous-domaine)
    parts = netloc.split('.')
    
    # Si c'est une adresse IP ou un domaine simple, retourne tel quel
    if len(parts) <= 2:
        return netloc
    
    # Retourne les deux dernières parties (domaine + TLD)
    # Gère les cas comme .co.uk, .com.au, etc.
    if len(parts) >= 3 and parts[-2] in ['co', 'com', 'ac', 'gov', 'org', 'net']:
        return '.'.join(parts[-3:])
    
    return '.'.join(parts[-2:])


# Tests et exemples d'utilisation
if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: Suppression des espaces superflus")
    print("=" * 60)
    
    text_with_spaces = "Bonjour    monde!   \n\n\n   Ceci est    un test.  \n  Nouvelle ligne.   "
    print(f"Texte original:\n'{text_with_spaces}'")
    print(f"\nTexte nettoyé:\n'{remove_extra_spaces(text_with_spaces)}'")
    
    print("\n" + "=" * 60)
    print("Test 2: Conversion HTML vers texte")
    print("=" * 60)
    
    html = """
    <html>
        <head>
            <title>Page de test</title>
            <script>alert('test');</script>
        </head>
        <body>
            <h1>Titre Principal</h1>
            <p>Ceci est un paragraphe avec des &eacute;l&eacute;ments sp&eacute;ciaux.</p>
            <p>Un autre paragraphe avec &nbsp; des espaces&nbsp;ins&eacute;cables.</p>
            <div>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </body>
    </html>
    """
    
    print(f"HTML original:\n{html[:100]}...")
    print(f"\nTexte extrait:\n{html_to_text(html)}")
    
    print("\n" + "=" * 60)
    print("Test 3: Extraction de domaine")
    print("=" * 60)
    
    urls = [
        "https://www.example.com/path/to/page?query=value",
        "http://api.github.com/users/octocat",
        "https://subdomain.example.co.uk/page",
        "www.google.fr",
        "example.com/path",
        "https://www.lemonde.fr/article/12345",
    ]
    
    for url in urls:
        domain = extract_domain(url)
        domain_with_sub = extract_domain(url, include_subdomain=True)
        print(f"\nURL: {url}")
        print(f"  Domaine principal: {domain}")
        print(f"  Avec sous-domaine: {domain_with_sub}")
