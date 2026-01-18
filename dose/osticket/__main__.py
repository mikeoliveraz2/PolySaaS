"""CLI entry point for OSTicket reverse proxy.

Run with: python -m dose.osticket
"""

from .proxy import run

if __name__ == "__main__":
    print("Starting OSTicket reverse proxy on http://127.0.0.1:8001")
    print("Access at: http://127.0.0.1:8001/admin/osticket/login.php")
    run(host="127.0.0.1", port=8001)
