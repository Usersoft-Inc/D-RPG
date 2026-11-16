"""Долбазавр RPG. Запуск: python D-Rex.py  (или python D-Rex.py --console для режима консоли)."""

import sys

if __name__ == "__main__":
    if "--console" in sys.argv:
        import game
        game.run_console()
    else:
        import window
        window.run()
