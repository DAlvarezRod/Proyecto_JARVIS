import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Any, Dict, List

from .base import Tool


class EmailTool(Tool):
    name = "email"
    description = "Send and read Gmail emails"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "send_email",
                "description": "Envia un correo electronico desde la cuenta de Gmail del usuario",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Direccion de correo del destinatario"},
                        "subject": {"type": "string", "description": "Asunto del correo"},
                        "body": {"type": "string", "description": "Contenido del correo"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
            {
                "name": "read_emails",
                "description": "Lee los correos mas recientes de la bandeja de entrada",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer", "description": "Cantidad de correos a leer. Default: 5"},
                        "folder": {"type": "string", "description": "Carpeta: INBOX, SENT, SPAM. Default: INBOX"},
                    },
                },
            },
            {
                "name": "search_emails",
                "description": "Busca correos por remitente, asunto o contenido",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Texto a buscar en los correos"},
                        "from_addr": {"type": "string", "description": "Filtrar por remitente. Opcional."},
                        "count": {"type": "integer", "description": "Cantidad maxima de resultados. Default: 5"},
                    },
                    "required": ["query"],
                },
            },
        ]

    def _get_creds(self):
        user = os.environ.get("GMAIL_USER", "")
        pwd = os.environ.get("GMAIL_APP_PASSWORD", "")
        if not user or not pwd:
            return None, None
        return user, pwd

    def _decode_header_value(self, value):
        if not value:
            return ""
        decoded = decode_header(value)
        parts = []
        for part, charset in decoded:
            if isinstance(part, bytes):
                parts.append(part.decode(charset or "utf-8", errors="ignore"))
            else:
                parts.append(part)
        return " ".join(parts)

    def _get_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        continue
        else:
            try:
                return msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return ""

    def execute(self, function_name, arguments):
        user, pwd = self._get_creds()
        if not user or not pwd:
            return "Error: GMAIL_USER y GMAIL_APP_PASSWORD no configurados"

        if function_name == "send_email":
            to = arguments.get("to", "")
            subject = arguments.get("subject", "")
            body = arguments.get("body", "")
            if not to or not subject:
                return "Error: destinatario y asunto requeridos"
            try:
                msg = MIMEMultipart()
                msg["From"] = user
                msg["To"] = to
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(user, pwd)
                server.send_message(msg)
                server.quit()
                return "Correo enviado a " + to + " | Asunto: " + subject
            except Exception as e:
                return "Error enviando correo: " + str(e)

        elif function_name == "read_emails":
            count = arguments.get("count", 5)
            folder = arguments.get("folder", "INBOX")
            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(user, pwd)
                mail.select(folder)
                status, data = mail.search(None, "ALL")
                ids = data[0].split()
                if not ids:
                    mail.logout()
                    return "No hay correos en " + folder
                recent_ids = ids[-count:]
                recent_ids.reverse()
                lines = []
                for eid in recent_ids:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    from_addr = self._decode_header_value(msg.get("From", ""))
                    subject = self._decode_header_value(msg.get("Subject", ""))
                    date = msg.get("Date", "")
                    body = self._get_body(msg)[:200]
                    lines.append(
                        "De: " + from_addr
                        + "\nAsunto: " + subject
                        + "\nFecha: " + date
                        + "\n" + body + "..."
                        + "\n---"
                    )
                mail.logout()
                return "Correos recientes (" + str(len(lines)) + "):\n\n" + "\n".join(lines)
            except Exception as e:
                return "Error leyendo correos: " + str(e)

        elif function_name == "search_emails":
            query = arguments.get("query", "")
            from_addr = arguments.get("from_addr", "")
            count = arguments.get("count", 5)
            if not query:
                return "Error: query vacia"
            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(user, pwd)
                mail.select("INBOX")
                criteria = ""
                if from_addr:
                    criteria = '(FROM "' + from_addr + '" SUBJECT "' + query + '")'
                else:
                    criteria = '(OR SUBJECT "' + query + '" BODY "' + query + '")'
                status, data = mail.search(None, criteria)
                ids = data[0].split()
                if not ids:
                    mail.logout()
                    return "No se encontraron correos con: " + query
                recent_ids = ids[-count:]
                recent_ids.reverse()
                lines = []
                for eid in recent_ids:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    from_who = self._decode_header_value(msg.get("From", ""))
                    subject = self._decode_header_value(msg.get("Subject", ""))
                    date = msg.get("Date", "")
                    lines.append(
                        "De: " + from_who
                        + "\nAsunto: " + subject
                        + "\nFecha: " + date
                        + "\n---"
                    )
                mail.logout()
                return "Encontrados (" + str(len(lines)) + "):\n\n" + "\n".join(lines)
            except Exception as e:
                return "Error buscando: " + str(e)

        return "Funcion no encontrada"
