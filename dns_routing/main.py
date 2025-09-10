#!/usr/bin/env python3
"""
Главная точка входа для DNS Routing Manager.
Командный интерфейс для управления маршрутизацией.
"""
import click
import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from dns_routing.cli.commands import cli

if __name__ == '__main__':
    cli()
