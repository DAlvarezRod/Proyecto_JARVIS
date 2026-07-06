import os
from typing import Any, Dict, List

from .base import Tool


class DocumentTool(Tool):
    name = "documents"
    description = "Read and summarize PDF and Word documents"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "read_document",
                "description": "Lee el contenido de un archivo PDF o Word (.docx). Usa esto cuando el usuario pida leer, resumir o analizar un documento.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Ruta del archivo PDF o DOCX"},
                        "pages": {"type": "string", "description": "Paginas a leer del PDF. Ej: '1-5', '1,3,5', 'all'. Default: all"},
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "search_document",
                "description": "Busca un documento PDF o Word por nombre en el computador y lo lee.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre del archivo a buscar (parcial o completo)"},
                        "folder": {"type": "string", "description": "Carpeta donde buscar. Default: Desktop, Documents, Downloads."},
                    },
                    "required": ["name"],
                },
            },
        ]

    def _find_file(self, name, folder=None):
        user_profile = os.environ.get("USERPROFILE", "")
        if folder:
            dirs = [folder]
        else:
            dirs = [
                os.path.join(user_profile, "OneDrive", "Desktop"),
                os.path.join(user_profile, "OneDrive", "Documents"),
                os.path.join(user_profile, "Desktop"),
                os.path.join(user_profile, "Documents"),
                os.path.join(user_profile, "Downloads"),
            ]

        name_lower = name.lower()
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if name_lower in f.lower() and (f.lower().endswith(".pdf") or f.lower().endswith(".docx")):
                        return os.path.join(root, f)
        return None

    def _read_pdf(self, path, pages=None):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            total = len(reader.pages)

            if pages and pages != "all":
                indices = self._parse_pages(pages, total)
            else:
                indices = range(total)

            text = ""
            for i in indices:
                if i < total:
                    page_text = reader.pages[i].extract_text() or ""
                    text += "\n--- Pagina " + str(i + 1) + " ---\n" + page_text

            if not text.strip():
                return "El PDF no tiene texto extraible (puede ser escaneado/imagen)."

            if len(text) > 6000:
                text = text[:6000] + "\n\n... (truncado, " + str(total) + " paginas en total)"

            return "Documento: " + os.path.basename(path) + " (" + str(total) + " paginas)\n" + text
        except Exception as e:
            return "Error leyendo PDF: " + str(e)

    def _read_docx(self, path):
        try:
            from docx import Document
            doc = Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)

            if not text.strip():
                return "El documento Word esta vacio."

            if len(text) > 6000:
                text = text[:6000] + "\n\n... (truncado)"

            return "Documento: " + os.path.basename(path) + " (" + str(len(paragraphs)) + " parrafos)\n\n" + text
        except Exception as e:
            return "Error leyendo Word: " + str(e)

    def _parse_pages(self, pages_str, total):
        indices = []
        for part in pages_str.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                start = max(1, int(start.strip()))
                end = min(total, int(end.strip()))
                indices.extend(range(start - 1, end))
            else:
                idx = int(part.strip()) - 1
                if 0 <= idx < total:
                    indices.append(idx)
        return indices

    def execute(self, function_name, arguments):
        if function_name == "read_document":
            return self._exec_read(arguments)
        elif function_name == "search_document":
            return self._exec_search(arguments)
        return "Funcion no encontrada"

    def _exec_read(self, arguments):
        path = arguments.get("path", "").strip()
        pages = arguments.get("pages", "all").strip()
        if not path:
            return "Error: ruta requerida"
        if not os.path.isfile(path):
            return "No se encontro el archivo: " + path

        if path.lower().endswith(".pdf"):
            return self._read_pdf(path, pages)
        elif path.lower().endswith(".docx"):
            return self._read_docx(path)
        return "Formato no soportado. Solo PDF y DOCX."

    def _exec_search(self, arguments):
        name = arguments.get("name", "").strip()
        folder = arguments.get("folder", "").strip() or None
        if not name:
            return "Error: nombre requerido"

        found = self._find_file(name, folder)
        if not found:
            return "No se encontro documento: " + name

        if found.lower().endswith(".pdf"):
            return self._read_pdf(found)
        elif found.lower().endswith(".docx"):
            return self._read_docx(found)
        return "Archivo encontrado pero formato no soportado: " + found