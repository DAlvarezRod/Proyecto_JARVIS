import subprocess
import json
from typing import Any, Dict, List


class WindowTool:
    name = "window_control"
    description = "Control application windows"

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_windows",
                "description": "Lista todas las ventanas abiertas con su proceso y titulo",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "control_window",
                "description": "Controla una ventana: minimizar, maximizar, restaurar o enfocar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app o parte del titulo de la ventana"},
                        "action": {"type": "string", "description": "Accion: minimize, maximize, restore, focus"},
                    },
                    "required": ["name", "action"],
                },
            },
            {
                "name": "close_window",
                "description": "Cierra una ventana por nombre",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app o parte del titulo"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "snap_window",
                "description": "Ajusta una ventana a una posicion de la pantalla",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app o parte del titulo"},
                        "position": {"type": "string", "description": "Posicion: left, right, top-left, top-right, bottom-left, bottom-right, full"},
                    },
                    "required": ["name", "position"],
                },
            },
            {
                "name": "move_resize_window",
                "description": "Mueve y/o redimensiona una ventana a posicion y tamano en pixeles",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nombre de la app o parte del titulo"},
                        "x": {"type": "integer", "description": "Posicion X en pixeles"},
                        "y": {"type": "integer", "description": "Posicion Y en pixeles"},
                        "width": {"type": "integer", "description": "Ancho en pixeles"},
                        "height": {"type": "integer", "description": "Alto en pixeles"},
                    },
                    "required": ["name"],
                },
            },
        ]

    def execute(self, function_name, arguments):
        if function_name == "list_windows":
            return self._list_windows()
        elif function_name == "control_window":
            return self._control_window(arguments.get("name", ""), arguments.get("action", ""))
        elif function_name == "close_window":
            return self._close_window(arguments.get("name", ""))
        elif function_name == "snap_window":
            return self._snap_window(arguments.get("name", ""), arguments.get("position", "left"))
        elif function_name == "move_resize_window":
            return self._move_resize(arguments)
        return "Funcion no encontrada"

    def _sanitize(self, text):
        return text.replace('"', '').replace("'", "").replace("$", "").replace("`", "").replace(";", "").replace("|", "").replace("&", "")

    def _run_ps(self, command):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, timeout=10,
                creationflags=0x08000000
            )
            return result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return "", str(e)

    def _list_windows(self):
        ps = (
            "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
            "Select-Object Id, ProcessName, MainWindowTitle | "
            "ConvertTo-Json -Compress"
        )
        out, err = self._run_ps(ps)
        if not out:
            return "No se encontraron ventanas abiertas"
        try:
            windows = json.loads(out)
            if isinstance(windows, dict):
                windows = [windows]
            lines = []
            for w in windows:
                lines.append(w.get("ProcessName", "") + " — " + w.get("MainWindowTitle", ""))
            return "Ventanas abiertas:\n" + "\n".join(lines)
        except json.JSONDecodeError:
            return "Ventanas:\n" + out

    def _find_window(self, name):
        safe = self._sanitize(name).lower()
        ps = (
            "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
            "Select-Object Id, ProcessName, MainWindowTitle, "
            "@{N='Handle';E={$_.MainWindowHandle}} | "
            "ConvertTo-Json -Compress"
        )
        out, _ = self._run_ps(ps)
        if not out:
            return None
        try:
            windows = json.loads(out)
            if isinstance(windows, dict):
                windows = [windows]
            for w in windows:
                proc = (w.get("ProcessName") or "").lower()
                title = (w.get("MainWindowTitle") or "").lower()
                if safe in proc or safe in title:
                    return w
        except json.JSONDecodeError:
            pass
        return None

    def _add_type_block(self, class_name, methods):
        lines = "Add-Type @\"\nusing System;\nusing System.Runtime.InteropServices;\n"
        lines += "public class " + class_name + " {\n"
        for m in methods:
            lines += "    " + m + "\n"
        lines += "}\n\"@\n"
        return lines

    def _control_window(self, name, action):
        if not name:
            return "Error: nombre de ventana requerido"
        window = self._find_window(name)
        if not window:
            return "No se encontro ventana con '" + name + "'"

        handle = window.get("Handle", 0)
        title = window.get("MainWindowTitle", "")
        h_str = str(handle)

        show_dll = '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);'
        focus_dll = '[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);'

        action_map = {
            "minimize": (6, "minimizada"),
            "maximize": (3, "maximizada"),
            "restore": (9, "restaurada"),
        }

        if action in action_map:
            cmd, label = action_map[action]
            ps = self._add_type_block("WC", [show_dll])
            ps += "[WC]::ShowWindow([IntPtr]" + h_str + ", " + str(cmd) + ")"
            self._run_ps(ps)
            return "Ventana " + label + ": " + title
        elif action == "focus":
            ps = self._add_type_block("WC", [show_dll, focus_dll])
            ps += "[WC]::ShowWindow([IntPtr]" + h_str + ", 9);\n"
            ps += "[WC]::SetForegroundWindow([IntPtr]" + h_str + ")"
            self._run_ps(ps)
            return "Ventana enfocada: " + title
        return "Accion no reconocida. Usa: minimize, maximize, restore, focus"

    def _close_window(self, name):
        if not name:
            return "Error: nombre de ventana requerido"
        window = self._find_window(name)
        if not window:
            return "No se encontro ventana con '" + name + "'"
        pid = window.get("Id", 0)
        title = window.get("MainWindowTitle", "")
        self._run_ps("Stop-Process -Id " + str(pid) + " -Force")
        return "Ventana cerrada: " + title

    def _snap_window(self, name, position):
        if not name:
            return "Error: nombre de ventana requerido"
        window = self._find_window(name)
        if not window:
            return "No se encontro ventana con '" + name + "'"

        handle = window.get("Handle", 0)
        title = window.get("MainWindowTitle", "")
        h_str = str(handle)

        show_dll = '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);'
        move_dll = '[DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int W, int H, bool repaint);'

        ps = "Add-Type -AssemblyName System.Windows.Forms;\n"
        ps += self._add_type_block("WS", [show_dll, move_dll])
        ps += "$s = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea;\n"
        ps += "$h = [IntPtr]" + h_str + ";\n"
        ps += "[WS]::ShowWindow($h, 9);\n"

        pos = position.lower().replace(" ", "-")
        snap_map = {
            "left": "(0, 0, [int]($s.Width/2), $s.Height",
            "right": "([int]($s.Width/2), 0, [int]($s.Width/2), $s.Height",
            "top-left": "(0, 0, [int]($s.Width/2), [int]($s.Height/2)",
            "top-right": "([int]($s.Width/2), 0, [int]($s.Width/2), [int]($s.Height/2)",
            "bottom-left": "(0, [int]($s.Height/2), [int]($s.Width/2), [int]($s.Height/2)",
            "bottom-right": "([int]($s.Width/2), [int]($s.Height/2), [int]($s.Width/2), [int]($s.Height/2)",
            "full": "(0, 0, $s.Width, $s.Height",
        }

        if pos not in snap_map:
            return "Posicion no reconocida. Usa: left, right, top-left, top-right, bottom-left, bottom-right, full"

        ps += "[WS]::MoveWindow($h, " + snap_map[pos] + ", $true)"
        self._run_ps(ps)
        return "Ventana '" + title + "' ajustada a " + position

    def _move_resize(self, params):
        name = params.get("name", "")
        if not name:
            return "Error: nombre de ventana requerido"
        window = self._find_window(name)
        if not window:
            return "No se encontro ventana con '" + name + "'"

        handle = window.get("Handle", 0)
        title = window.get("MainWindowTitle", "")
        h_str = str(handle)

        show_dll = '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);'
        move_dll = '[DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr hWnd, int X, int Y, int W, int H, bool repaint);'
        rect_dll = '[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT r);'

        ps = self._add_type_block("WM", [show_dll, move_dll, rect_dll])
        ps += "[StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }\n"

        has_x = "x" in params
        has_y = "y" in params
        has_w = "width" in params
        has_h = "height" in params

        if not (has_x and has_y and has_w and has_h):
            ps_get = self._add_type_block("WG", [rect_dll])
            ps_get += (
                "Add-Type @\"\n[StructLayout(LayoutKind.Sequential)] public struct RECT2 { public int L,T,R,B; }\n\"@\n"
                "$r = New-Object RECT2;\n"
                "[WG]::GetWindowRect([IntPtr]" + h_str + ", [ref]$r);\n"
                "'{0},{1},{2},{3}' -f $r.L, $r.T, ($r.R-$r.L), ($r.B-$r.T)"
            )
            out, _ = self._run_ps(ps_get)
            try:
                cx, cy, cw, ch = map(int, out.split(","))
            except (ValueError, AttributeError):
                cx, cy, cw, ch = 0, 0, 800, 600
        else:
            cx, cy, cw, ch = 0, 0, 800, 600

        x = params.get("x", cx)
        y = params.get("y", cy)
        w = params.get("width", cw)
        h = params.get("height", ch)

        ps2 = self._add_type_block("WM2", [show_dll, move_dll])
        ps2 += "$h = [IntPtr]" + h_str + ";\n"
        ps2 += "[WM2]::ShowWindow($h, 9);\n"
        ps2 += "[WM2]::MoveWindow($h, " + str(x) + ", " + str(y) + ", " + str(w) + ", " + str(h) + ", $true)"
        self._run_ps(ps2)
        return "Ventana '" + title + "' movida a x=" + str(x) + " y=" + str(y) + " (" + str(w) + "x" + str(h) + ")"