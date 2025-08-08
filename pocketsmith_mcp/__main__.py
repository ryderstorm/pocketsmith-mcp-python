def main() -> None:
    # Lazy-import to avoid pulling heavy deps during module import
    from .server import main as _main

    _main()


if __name__ == '__main__':
    main()
