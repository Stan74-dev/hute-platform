import json
import os
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List

import win32api
import win32print

HOST = "127.0.0.1"
PORT = 8765


def format_money(value: Any) -> str:
    try:
        return f"{float(value or 0):.2f}"
    except Exception:
        return "0.00"


def build_receipt_text(data: Dict[str, Any]) -> str:
    width = 42

    def line(text: str = "") -> str:
        return f"{text}\n"

    def center(text: str) -> str:
        return text.center(width) + "\n"

    def sep() -> str:
        return "-" * width + "\n"

    def two_col(left: str, right: str) -> str:
        left = str(left)
        right = str(right)
        space = max(1, width - len(left) - len(right))
        return f"{left}{' ' * space}{right}\n"

    parts: List[str] = []
    parts.append(center("HUTE"))
    parts.append(center("THERMAL RECEIPT"))
    parts.append(sep())
    parts.append(line(f"Receipt: {data.get('receipt_number', '-') }"))
    parts.append(line(f"Date: {data.get('created_at', '-') }"))
    parts.append(line(f"Warehouse: {data.get('warehouse_name', '-') }"))
    parts.append(line(f"Payment: {data.get('payment_method', '-') }"))
    parts.append(line(f"Status: {'OFFLINE SAVED' if data.get('is_offline') else 'COMPLETED'}"))
    parts.append(sep())

    for item in data.get("items", []):
        name = str(item.get("product_name", ""))[:width]
        qty = int(item.get("quantity", 0) or 0)
        unit_price = float(item.get("unit_price", 0) or 0)
        total = qty * unit_price

        parts.append(line(name))
        parts.append(two_col(f"{qty} x {format_money(unit_price)}", format_money(total)))

    parts.append(sep())
    parts.append(two_col("TOTAL", f"GBP {format_money(data.get('total_amount', 0))}"))
    parts.append(sep())
    parts.append(center("Thank you for your business"))
    parts.append(center("Powered by HUTE"))
    parts.append("\n" * 4)

    return "".join(parts)


def print_text_via_notepad(text: str) -> None:
    default_printer = win32print.GetDefaultPrinter()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as temp_file:
        temp_file.write(text)
        temp_path = temp_file.name

    try:
        win32api.ShellExecute(
            0,
            "printto",
            temp_path,
            f'"{default_printer}"',
            ".",
            0,
        )
    finally:
        pass


class PrintHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_headers(200)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"ok": True, "service": "hute-print-bridge"}).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"detail": "Not found"}).encode("utf-8"))

    def do_POST(self) -> None:
        if self.path != "/print":
            self._set_headers(404)
            self.wfile.write(json.dumps({"detail": "Not found"}).encode("utf-8"))
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))

            receipt_text = build_receipt_text(payload)
            print_text_via_notepad(receipt_text)

            self._set_headers(200)
            self.wfile.write(json.dumps({"ok": True, "message": "Print job sent"}).encode("utf-8"))
        except Exception as exc:
            self._set_headers(500)
            self.wfile.write(json.dumps({"ok": False, "detail": str(exc)}).encode("utf-8"))


def main() -> None:
    server = HTTPServer((HOST, PORT), PrintHandler)
    print(f"HUTE print bridge running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()