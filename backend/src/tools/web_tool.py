from typing import Any, Dict, List
import urllib.request
import re
import webbrowser

WEBSITE_SHORTCUTS = {
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "whatsapp web": "https://web.whatsapp.com",
    "reddit": "https://www.reddit.com",
    "github": "https://github.com",
    "chatgpt": "https://chat.openai.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "twitch": "https://www.twitch.tv",
    "tiktok": "https://www.tiktok.com",
    "linkedin": "https://www.linkedin.com",
    "wikipedia": "https://es.wikipedia.org",
    "maps": "https://maps.google.com",
    "drive": "https://drive.google.com",
    "calendar": "https://calendar.google.com",
}

class WebTool:
    name = "web"
    description = "Search the web and fetch URL content"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "web_search",
                "description": "Busca informacion en internet usando DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Texto a buscar"},
                        "count": {"type": "integer", "description": "Cantidad de resultados. Default: 5"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "web_search_news",
                "description": "Busca noticias recientes y resultados en tiempo real. Usar para deportes en vivo, clima, noticias del momento.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Texto a buscar en noticias"},
                        "count": {"type": "integer", "description": "Cantidad de resultados. Default: 5"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "fetch_url",
                "description": "Descarga y lee el contenido de una pagina web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL completa a visitar"},
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "open_website",
                "description": "Abre una pagina web en el navegador predeterminado. Puede recibir un nombre de sitio conocido (youtube, gmail, google, twitter, netflix, etc) o una URL completa.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL completa o nombre del sitio (youtube, gmail, google, twitter, etc)"},
                    },
                    "required": ["url"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "web_search":
            return self._search(arguments, news=False)

        elif function_name == "web_search_news":
            return self._search(arguments, news=True)

        elif function_name == "fetch_url":
            url = arguments.get("url", "")
            if not url:
                return "Error: URL vacia"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    content = resp.read().decode("utf-8", errors="ignore")
                content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)
                content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)
                content = re.sub(r"<[^>]+>", " ", content)
                content = re.sub(r"\s+", " ", content).strip()
                if len(content) > 4000:
                    content = content[:4000] + "... (truncado)"
                return "Contenido de " + url + ":\n\n" + content
            except Exception as e:
                return "Error abriendo URL: " + str(e)

        elif function_name == "open_website":
            url = arguments.get("url", "").strip()
            if not url:
                return "Error: URL requerida"
            url_lower = url.lower()
            if url_lower in WEBSITE_SHORTCUTS:
                url = WEBSITE_SHORTCUTS[url_lower]
            elif not url.startswith("http"):
                url = "https://www." + url_lower + ".com"
            webbrowser.open(url)
            return "Abriendo " + url + " en el navegador"

        return "Funcion no encontrada"

    def _search(self, arguments, news=False):
        query = arguments.get("query", "")
        count = arguments.get("count", 5)
        if not query:
            return "Error: query vacia"
        try:
            from ddgs import DDGS
            ddgs = DDGS()
            if news:
                results = ddgs.news(query, max_results=count)
            else:
                results = ddgs.text(query, max_results=count)
            if not results:
                return "No se encontraron resultados para: " + query
            lines = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                url = r.get("href", "") or r.get("url", "")
                body = r.get("body", "")[:200]
                date = r.get("date", "")
                line = str(i) + ". " + title + "\n   " + url + "\n   " + body
                if date:
                    line += "\n   Fecha: " + date
                lines.append(line)
            kind = "Noticias" if news else "Resultados"
            return kind + " para '" + query + "':\n\n" + "\n\n".join(lines)
        except Exception as e:
            return "Error buscando: " + str(e)