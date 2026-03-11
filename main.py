import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cli import Assistant


def main():
    """主入口函数"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    assistant = Assistant(config_path)
    assistant.run()


if __name__ == "__main__":
    main()
