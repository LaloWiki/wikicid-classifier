"""
Scraper para extraer información de las páginas web de empresas WikiCID
Con respaldo de búsqueda web cuando el sitio no está disponible
"""

import requests
from bs4 import BeautifulSoup
import time
import json
from typing import Dict, Optional
import logging
import urllib.parse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def extract_info(self, url: str, empresa_nombre: str = "") -> Optional[Dict[str, str]]:
        """
        Extrae información relevante de una URL.
        Si falla, intenta buscar información en Google.
        """
        # Intentar extraer del website original
        info = self._extract_from_url(url)
        
        if info:
            return info
        
        # Si falló, intentar búsqueda web de respaldo
        if empresa_nombre:
            logger.info(f"⚠️ Website no disponible, buscando información en web sobre: {empresa_nombre}")
            return self._search_web_fallback(empresa_nombre, url)
        
        return None
    
    def _extract_from_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extrae información de una URL específica
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer información
            info = {
                'url': url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'meta_description': self._extract_meta_description(soup),
                'h1_tags': self._extract_h1_tags(soup),
                'keywords': self._extract_keywords(soup),
                'text_content': self._extract_text_content(soup),
                'source': 'website_directo'
            }
            
            logger.info(f"✓ Información extraída de: {url}")
            return info
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏱ Timeout al acceder a: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"✗ Error al acceder a {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"✗ Error inesperado con {url}: {str(e)}")
            return None
    
    def _search_web_fallback(self, empresa_nombre: str, original_url: str) -> Optional[Dict[str, str]]:
        """
        Busca información de la empresa en DuckDuckGo (no requiere API)
        """
        try:
            # Usar DuckDuckGo HTML search (no requiere API)
            query = f"{empresa_nombre} artificial intelligence AI technology"
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            
            response = requests.get(search_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer resultados de búsqueda
            results = soup.find_all('div', class_='result__body', limit=5)
            
            description_parts = []
            for result in results:
                snippet = result.find('a', class_='result__snippet')
                if snippet:
                    description_parts.append(snippet.get_text().strip())
            
            combined_description = ' '.join(description_parts[:3])  # Primeros 3 resultados
            
            if combined_description:
                info = {
                    'url': original_url,
                    'title': f"{empresa_nombre} - Información de búsqueda web",
                    'description': combined_description[:1000],
                    'meta_description': combined_description[:500],
                    'h1_tags': empresa_nombre,
                    'keywords': 'AI, artificial intelligence, technology',
                    'text_content': combined_description[:800],
                    'source': 'busqueda_web_respaldo'
                }
                
                logger.info(f"✓ Información encontrada vía búsqueda web para: {empresa_nombre}")
                return info
            else:
                logger.warning(f"⚠️ No se encontró información vía búsqueda para: {empresa_nombre}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Error en búsqueda web de respaldo para {empresa_nombre}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrae el título de la página"""
        title = soup.find('title')
        return title.get_text().strip() if title else ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrae la descripción desde diferentes fuentes"""
        # Intentar obtener de meta description
        meta_desc = self._extract_meta_description(soup)
        if meta_desc:
            return meta_desc
        
        # Buscar en párrafos principales
        paragraphs = soup.find_all('p', limit=5)
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 50:  # Párrafos con contenido significativo
                return text[:500]
        
        return ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extrae la meta descripción"""
        meta_tags = [
            soup.find('meta', attrs={'name': 'description'}),
            soup.find('meta', attrs={'property': 'og:description'}),
            soup.find('meta', attrs={'name': 'twitter:description'})
        ]
        
        for meta in meta_tags:
            if meta and meta.get('content'):
                return meta.get('content').strip()
        
        return ""
    
    def _extract_h1_tags(self, soup: BeautifulSoup) -> str:
        """Extrae los h1 tags"""
        h1_tags = soup.find_all('h1', limit=3)
        return ' | '.join([h1.get_text().strip() for h1 in h1_tags])
    
    def _extract_keywords(self, soup: BeautifulSoup) -> str:
        """Extrae keywords de meta tags"""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            return meta_keywords.get('content').strip()
        return ""
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extrae contenido de texto general (primeros 1000 caracteres)"""
        # Eliminar scripts y estilos
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        text = soup.get_text()
        # Limpiar texto
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:1000]  # Primeros 1000 caracteres

def test_scraper():
    """Función de prueba"""
    scraper = WebScraper()
    test_url = "https://www.247.ai"
    
    print(f"\n🧪 Probando scraper con: {test_url}\n")
    info = scraper.extract_info(test_url)
    
    if info:
        print("✅ Información extraída:")
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print("❌ No se pudo extraer información")

if __name__ == "__main__":
    test_scraper()
