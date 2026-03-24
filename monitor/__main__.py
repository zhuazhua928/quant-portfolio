from .alpaca_bars import check_credentials
from .utils import setup_logging
from .scheduler import run_loop


def main() -> None:
    setup_logging()
    check_credentials()
    run_loop()


if __name__ == "__main__":
    main()
