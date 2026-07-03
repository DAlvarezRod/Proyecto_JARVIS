import time


class SecurityManager:
    DANGEROUS_ACTIONS = {
        "delete_file": "eliminar un archivo",
        "close_app": "cerrar una aplicacion",
        "git_add_commit_push": "hacer commit y push al repositorio",
    }

    DANGEROUS_COMMANDS = [
        "del ", "rm ", "rmdir", "remove-item", "format",
        "shutdown", "restart", "taskkill", "stop-process",
        "reg delete", "diskpart", "net user", "net stop",
        "rd /s",
    ]

    def __init__(self):
        self._warned = {}
        self._timeout = 300

    def check(self, function_name, arguments):
        now = time.time()
        self._warned = {k: v for k, v in self._warned.items() if now - v < self._timeout}

        if function_name in self._warned:
            del self._warned[function_name]
            print("[SECURITY] Confirmado: " + function_name, flush=True)
            return True, ""

        if function_name in self.DANGEROUS_ACTIONS:
            self._warned[function_name] = now
            desc = self.DANGEROUS_ACTIONS[function_name]
            detail = ""
            if function_name == "delete_file":
                detail = ": " + str(arguments.get("path", ""))
            elif function_name == "close_app":
                detail = ": " + str(arguments.get("app_name", ""))
            print("[SECURITY] Bloqueado: " + function_name + detail, flush=True)
            return False, "CONFIRMACION REQUERIDA para " + desc + detail + ". Pregunta al usuario si desea continuar."

        if function_name == "run_command":
            cmd = str(arguments.get("command", "")).lower()
            for pattern in self.DANGEROUS_COMMANDS:
                if pattern in cmd:
                    self._warned[function_name] = now
                    print("[SECURITY] Comando peligroso: " + pattern.strip(), flush=True)
                    return False, "CONFIRMACION REQUERIDA: comando peligroso (" + pattern.strip() + "). Pregunta al usuario antes de ejecutar."

        return True, ""
