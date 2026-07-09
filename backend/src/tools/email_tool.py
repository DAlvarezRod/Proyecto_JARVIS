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
            {
                "name": "delete_emails",
                "description": "Elimina correos que coincidan con el criterio (los mueve a la papelera de Gmail)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_addr": {"type": "string", "description": "Eliminar correos de este remitente"},
                        "subject": {"type": "string", "description": "Eliminar correos que contengan esto en el asunto"},
                        "older_than_days": {"type": "integer", "description": "Eliminar correos mas viejos que X dias"},
                        "count": {"type": "integer", "description": "Maximo de correos a eliminar. Default: 10"},
                    },
                },
            },
            {
                "name": "archive_emails",
                "description": "Archiva correos del inbox (los quita del inbox pero se quedan guardados en Gmail)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_addr": {"type": "string", "description": "Archivar correos de este remitente"},
                        "subject": {"type": "string", "description": "Archivar correos con este asunto"},
                        "older_than_days": {"type": "integer", "description": "Archivar correos mas viejos que X dias"},
                        "count": {"type": "integer", "description": "Maximo de correos a archivar. Default: 10"},
                    },
                },
            },
            {
                "name": "mark_emails_read",
                "description": "Marca correos como leidos",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_addr": {"type": "string", "description": "Marcar como leidos correos de este remitente"},
                        "subject": {"type": "string", "description": "Marcar como leidos correos con este asunto"},
                        "all_unread": {"type": "boolean", "description": "Marcar TODOS los no leidos como leidos"},
                    },
                },
            },
            {
                "name": "list_labels",
                "description": "Lista todas las etiquetas/labels disponibles en Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "move_to_label",
                "description": "Mueve correos del inbox a una etiqueta de Gmail (Cristiano, Deporte, Juegos, Personal, Sistemas, Trabajo, Universidad u otra)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_addr": {"type": "string", "description": "Mover correos de este remitente"},
                        "subject": {"type": "string", "description": "Mover correos con este asunto"},
                        "label": {"type": "string", "description": "Nombre de la etiqueta destino (ej: Universidad, Trabajo, Personal)"},
                        "count": {"type": "integer", "description": "Maximo de correos a mover. Default: 10"},
                    },
                    "required": ["label"],
                },
            },
            {
                "name": "unsubscribe_email",
                "description": "Busca el link de darse de baja de correos de un remitente y lo abre en el navegador",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_addr": {"type": "string", "description": "Remitente del que quieres darte de baja"},
                        "subject": {"type": "string", "description": "Asunto del correo para encontrarlo"},
                    },
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
        try:
            decoded = decode_header(value)
            parts = []
            for part, charset in decoded:
                if isinstance(part, bytes):
                    parts.append(part.decode(charset or "utf-8", errors="replace"))
                else:
                    parts.append(str(part))
            return " ".join(parts)
        except Exception:
            return str(value)

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
                    try:
                        status, msg_data = mail.fetch(eid, "(RFC822)")
                        if not msg_data or not msg_data[0] or msg_data[0][1] is None:
                            continue
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
                    except Exception:
                        lines.append("(correo no legible)\n---")
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
                    try:
                        status, msg_data = mail.fetch(eid, "(RFC822)")
                        if not msg_data or not msg_data[0] or msg_data[0][1] is None:
                            continue
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
                    except Exception:
                        lines.append("(correo no legible)\n---")
                mail.logout()
                return "Encontrados (" + str(len(lines)) + "):\n\n" + "\n".join(lines)
            except Exception as e:
                return "Error buscando: " + str(e)
        elif function_name == "delete_emails":
            return self._delete_emails(arguments)
        elif function_name == "archive_emails":
            return self._archive_emails(arguments)
        elif function_name == "mark_emails_read":
            return self._mark_read(arguments)
        elif function_name == "list_labels":
            return self._list_labels()
        elif function_name == "move_to_label":
            return self._move_to_label(arguments)
        elif function_name == "unsubscribe_email":
            return self._unsubscribe(arguments)

        return "Funcion no encontrada"
    
    def _build_search(self, params):
        from_addr = params.get("from_addr", "")
        subject = params.get("subject", "")
        older_than_days = params.get("older_than_days", 0)
        criteria = []
        if from_addr:
            criteria.append('FROM "' + from_addr + '"')
        if subject:
            criteria.append('SUBJECT "' + subject + '"')
        if older_than_days:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=older_than_days)).strftime("%d-%b-%Y")
            criteria.append("BEFORE " + date)
        if not criteria:
            return None
        return "(" + " ".join(criteria) + ")"

    def _find_trash_folder(self, mail):
        for name in ["[Gmail]/Trash", "[Gmail]/Papelera"]:
            try:
                status, _ = mail.select('"' + name + '"')
                if status == "OK":
                    mail.select("INBOX")
                    return name
            except Exception:
                continue
        return "[Gmail]/Trash"

    def _delete_emails(self, params):
        user, pwd = self._get_creds()
        if not user:
            return "Error: credenciales no configuradas"
        criteria = self._build_search(params)
        if not criteria:
            return "Error: indica al menos from_addr, subject o older_than_days"
        count = params.get("count", 10)
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            trash = self._find_trash_folder(mail)
            mail.select("INBOX")
            status, data = mail.search(None, criteria)
            ids = data[0].split()
            if not ids:
                mail.logout()
                return "No se encontraron correos con ese criterio"
            to_delete = ids[-count:]
            deleted = []
            for eid in to_delete:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                subj = self._decode_header_value(msg.get("Subject", ""))
                frm = self._decode_header_value(msg.get("From", ""))
                mail.copy(eid, '"' + trash + '"')
                mail.store(eid, "+FLAGS", "\\Deleted")
                deleted.append(frm + " — " + subj)
            mail.expunge()
            mail.logout()
            return "Eliminados " + str(len(deleted)) + " correos:\n" + "\n".join(deleted)
        except Exception as e:
            return "Error eliminando correos: " + str(e)

    def _archive_emails(self, params):
        user, pwd = self._get_creds()
        if not user:
            return "Error: credenciales no configuradas"
        criteria = self._build_search(params)
        if not criteria:
            return "Error: indica al menos from_addr, subject o older_than_days"
        count = params.get("count", 10)
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            mail.select("INBOX")
            status, data = mail.search(None, criteria)
            ids = data[0].split()
            if not ids:
                mail.logout()
                return "No se encontraron correos con ese criterio"
            to_archive = ids[-count:]
            archived = []
            for eid in to_archive:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                subj = self._decode_header_value(msg.get("Subject", ""))
                frm = self._decode_header_value(msg.get("From", ""))
                mail.store(eid, "+FLAGS", "\\Deleted")
                archived.append(frm + " — " + subj)
            mail.expunge()
            mail.logout()
            return "Archivados " + str(len(archived)) + " correos (quitados del inbox):\n" + "\n".join(archived)
        except Exception as e:
            return "Error archivando correos: " + str(e)

    def _mark_read(self, params):
        user, pwd = self._get_creds()
        if not user:
            return "Error: credenciales no configuradas"
        all_unread = params.get("all_unread", False)
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            mail.select("INBOX")
            if all_unread:
                criteria = "(UNSEEN)"
            else:
                criteria = self._build_search(params)
                if not criteria:
                    return "Error: indica from_addr, subject o all_unread=true"
            status, data = mail.search(None, criteria)
            ids = data[0].split()
            if not ids:
                mail.logout()
                return "No hay correos sin leer con ese criterio"
            for eid in ids:
                mail.store(eid, "+FLAGS", "\\Seen")
            mail.logout()
            return str(len(ids)) + " correos marcados como leidos"
        except Exception as e:
            return "Error: " + str(e)
    def _list_labels(self):
        user, pwd = self._get_creds()
        if not user:
            return "Error: credenciales no configuradas"
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            status, folders = mail.list()
            labels = []
            for f in folders:
                decoded = f.decode()
                parts = decoded.split(' "/" ')
                if len(parts) > 1:
                    name = parts[-1].strip('"')
                    if not name.startswith("[Gmail]"):
                        labels.append(name)
            mail.logout()
            if not labels:
                return "No se encontraron etiquetas"
            return "Etiquetas disponibles:\n" + "\n".join(labels)
        except Exception as e:
            return "Error listando etiquetas: " + str(e)

    def _move_to_label(self, params):
        user, pwd = self._get_creds()
        if not user:
            return "Error: credenciales no configuradas"
        label = params.get("label", "")
        if not label:
            return "Error: etiqueta requerida"
        criteria = self._build_search(params)
        if not criteria:
            return "Error: indica from_addr o subject para saber que correos mover"
        count = params.get("count", 10)
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            mail.select("INBOX")
            status, data = mail.search(None, criteria)
            ids = data[0].split()
            if not ids:
                mail.logout()
                return "No se encontraron correos con ese criterio"
            to_move = ids[-count:]
            moved = []
            for eid in to_move:
                try:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    if not msg_data or not msg_data[0] or msg_data[0][1] is None:
                        continue
                    msg = email.message_from_bytes(msg_data[0][1])
                    subj = self._decode_header_value(msg.get("Subject", ""))
                    frm = self._decode_header_value(msg.get("From", ""))
                    result = mail.copy(eid, '"' + label + '"')
                    if result[0] == "OK":
                        mail.store(eid, "+FLAGS", "\\Deleted")
                        moved.append(frm + " — " + subj)
                    else:
                        moved.append("(no se pudo mover) " + frm + " — " + subj)
                except Exception:
                    continue
            mail.expunge()
            mail.logout()
            if not moved:
                return "No se pudieron mover correos a '" + label + "'. Verifica que la etiqueta exista."
            return "Movidos " + str(len(moved)) + " correos a '" + label + "':\n" + "\n".join(moved)
        except Exception as e:
            return "Error moviendo correos: " + str(e)

    def _unsubscribe(self, params):
        user, pwd = self._get_creds()
        if not user:
            return "Error: credenciales no configuradas"
        from_addr = params.get("from_addr", "")
        subject = params.get("subject", "")
        if not from_addr and not subject:
            return "Error: indica from_addr o subject para encontrar el correo"
        criteria = self._build_search(params)
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            mail.select("INBOX")
            status, data = mail.search(None, criteria)
            ids = data[0].split()
            if not ids:
                mail.logout()
                return "No se encontraron correos de ese remitente"
            eid = ids[-1]
            status, msg_data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            unsub = msg.get("List-Unsubscribe", "")
            mail.logout()
            if not unsub:
                return "Este correo no tiene link de baja automatico. Busca 'unsubscribe' o 'darse de baja' al final del correo."
            import re
            urls = re.findall(r'<(https?://[^>]+)>', unsub)
            if urls:
                import webbrowser
                webbrowser.open(urls[0])
                return "Abriendo link de baja en el navegador: " + urls[0]
            mailtos = re.findall(r'<(mailto:[^>]+)>', unsub)
            if mailtos:
                return "Para darte de baja, envia un correo a: " + mailtos[0].replace("mailto:", "")
            return "Header de baja encontrado pero no se pudo extraer el link: " + unsub
        except Exception as e:
            return "Error: " + str(e)
