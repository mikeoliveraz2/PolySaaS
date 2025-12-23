"""Command-line interface for PolySaaS."""
import argparse
import sys

from polysaas.core.config import settings


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="PolySaaS CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"PolySaaS {settings.VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start server command
    start_parser = subparsers.add_parser("start", help="Start the PolySaaS server")
    start_parser.add_argument(
        "--host",
        default=settings.HOST,
        help=f"Host to bind to (default: {settings.HOST})",
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"Port to bind to (default: {settings.PORT})",
    )
    start_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development mode)",
    )

    args = parser.parse_args()

    if args.command == "start":
        import uvicorn

        uvicorn.run(
            "polysaas.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    elif args.command is None:
        parser.print_help()
        sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
