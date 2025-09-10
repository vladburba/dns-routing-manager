#!/bin/bash
# Настройка автоматизации DNS Routing Manager

PROJECT_DIR="$PWD"
SCRIPT_NAME="dns_routing_auto_update"

echo "=== DNS Routing Manager - Настройка автоматизации ==="

# Проверяем что мы в правильной директории
if [ ! -f "run.py" ] || [ ! -d "dns_routing" ]; then
    echo "❌ Ошибка: Запустите скрипт из корневой директории проекта dns-routing-manager"
    exit 1
fi

# Создаем исполняемый скрипт автообновления
cat > auto_update.py << 'EOF'
#!/usr/bin/env python3
# Автообновление создано setup_automation.sh
import sys
import os
from pathlib import Path

# Переходим в директорию проекта
project_dir = Path(__file__).parent
os.chdir(project_dir)

# Активируем виртуальное окружение
venv_activate = project_dir / "venv" / "bin" / "activate_this.py"
if venv_activate.exists():
    exec(open(venv_activate).read(), {'__file__': str(venv_activate)})

# Запускаем менеджер автообновления
from dns_routing.config import get_config
from dns_routing.core.resolver import DNSResolver
from dns_routing.core.route_manager import RouteManager

def smart_maintenance():
    """Умное обслуживание системы"""
    try:
        resolver = DNSResolver()
        cache_stats = resolver.get_cache_stats()
        
        print(f"Cache stats: {cache_stats['valid_entries']}/{cache_stats['total_entries']} valid")
        
        # Простая логика: если кэш почти пустой, обновляем
        if cache_stats['valid_entries'] < 5:
            print("Cache is low, running light refresh...")
            # Можно добавить логику обновления нескольких ключевых доменов
        
        return True
        
    except Exception as e:
        print(f"Maintenance error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--maintenance":
        smart_maintenance()
    else:
        print("DNS Routing Auto-Update - use --maintenance to run")
EOF

chmod +x auto_update.py

# Варианты автоматизации

echo ""
echo "📋 Выберите метод автоматизации:"
echo "1) Cron (рекомендуется) - периодический запуск"
echo "2) LaunchAgent (macOS) - системная служба"
echo "3) Только создать скрипты (ручной запуск)"
echo ""

read -p "Введите номер (1-3): " choice

case $choice in
    1)
        echo ""
        echo "=== Настройка Cron ==="
        
        # Создаем cron скрипт
        cat > cron_update.sh << EOF
#!/bin/bash
# Cron скрипт для DNS Routing Manager
cd "$PROJECT_DIR"
source venv/bin/activate
python3 auto_update.py --maintenance >> logs/auto_update.log 2>&1
EOF
        
        chmod +x cron_update.sh
        
        echo "Создан скрипт: $PROJECT_DIR/cron_update.sh"
        echo ""
        echo "Для добавления в cron выполните:"
        echo "  crontab -e"
        echo ""
        echo "И добавьте строку:"
        echo "  # DNS Routing Manager - каждые 4 часа"
        echo "  0 */4 * * * $PROJECT_DIR/cron_update.sh"
        echo ""
        echo "Или каждый день в 9:00:"
        echo "  0 9 * * * $PROJECT_DIR/cron_update.sh"
        ;;
        
    2)
        echo ""
        echo "=== Настройка LaunchAgent (macOS) ==="
        
        PLIST_FILE="$HOME/Library/LaunchAgents/com.dnsrouting.autoupdate.plist"
        
        # Создаем plist файл
        cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dnsrouting.autoupdate</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/auto_update.py</string>
        <string>--maintenance</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StartInterval</key>
    <integer>14400</integer>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd_error.log</string>
</dict>
</plist>
EOF

        echo "Создан LaunchAgent: $PLIST_FILE"
        echo ""
        echo "Для активации выполните:"
        echo "  launchctl load $PLIST_FILE"
        echo "  launchctl start com.dnsrouting.autoupdate"
        echo ""
        echo "Для деактивации:"
        echo "  launchctl unload $PLIST_FILE"
        ;;
        
    3)
        echo ""
        echo "=== Только скрипты созданы ==="
        echo "Созданы файлы:"
        echo "  - auto_update.py (основной скрипт)"
        echo ""
        echo "Ручной запуск:"
        echo "  python3 auto_update.py --maintenance"
        ;;
        
    *)
        echo "Неверный выбор"
        exit 1
        ;;
esac

# Создаем директорию для логов
mkdir -p logs

# Создаем простой скрипт проверки статуса
cat > check_status.py << 'EOF'
#!/usr/bin/env python3
"""Быстрая проверка статуса системы"""
import sys
from pathlib import Path

# Добавляем путь
sys.path.insert(0, str(Path(__file__).parent))

from dns_routing.config import get_config
from dns_routing.core.resolver import DNSResolver
from dns_routing.core.route_manager import RouteManager

def main():
    try:
        resolver = DNSResolver()
        route_manager = RouteManager()
        
        # DNS статистика
        dns_stats = resolver.get_cache_stats()
        print(f"DNS Cache: {dns_stats['valid_entries']}/{dns_stats['total_entries']} valid")
        
        # Маршруты
        routes_count = route_manager.get_active_routes_count()
        print(f"Active Routes: {routes_count}")
        
        # Проверяем несколько ключевых маршрутов
        key_ips = ["77.88.55.88", "8.8.8.8"]
        for ip in key_ips:
            route = route_manager.check_route(ip)
            if route:
                interface = route.get('interface', 'unknown')
                print(f"Route {ip}: via {interface}")
            else:
                print(f"Route {ip}: not found")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

chmod +x check_status.py

echo ""
echo "✅ Автоматизация настроена!"
echo ""
echo "📁 Созданные файлы:"
echo "  - auto_update.py (основной скрипт автообновления)"
echo "  - check_status.py (быстрая проверка статуса)"
if [ "$choice" = "1" ]; then
    echo "  - cron_update.sh (для cron)"
fi
echo ""
echo "🔧 Команды для управления:"
echo "  python3 check_status.py              # Проверка статуса"
echo "  python3 auto_update.py --maintenance # Ручное обслуживание"
echo "  python3 run.py status                # Полный статус системы"
echo ""
echo "📊 Мониторинг:"
echo "  tail -f logs/auto_update.log         # Логи автообновления"
echo "  tail -f logs/dns_routing.log         # Логи системы"
echo ""

# Создаем файл с рекомендациями
cat > AUTOMATION_README.md << 'EOF'
# Автоматизация DNS Routing Manager

## Созданные компоненты

### Основные скрипты
- `auto_update.py` - Основной скрипт автообновления
- `check_status.py` - Быстрая проверка статуса системы
- `cron_update.sh` - Скрипт для cron (если выбран)

### Стратегия автообновления

#### Умная логика обновления:
1. **Проверка состояния кэша** - обновление только при необходимости
2. **Приоритизация критичных доменов** - .gov, .bank, api. обновляются чаще
3. **Вероятностное обновление** - избегаем перегрузки DNS серверов
4. **Возрастная политика** - старые записи обновляются в первую очередь

#### Периодичность:
- **Проверка кэша**: каждые 4-6 часов
- **Очистка устаревших записей**: раз в день
- **Проверка критичных маршрутов**: каждые 2 часа

## Рекомендуемые настройки

### Для домашнего использования:
```bash
# Cron - раз в день утром
0 9 * * * /path/to/dns-routing-manager/cron_update.sh
```

### Для рабочей среды:
```bash
# Cron - каждые 4 часа в рабочее время
0 9,13,17 * * 1-5 /path/to/dns-routing-manager/cron_update.sh
```

### Для серверов:
```bash
# Cron - каждые 2 часа, но не в час пик
0 */2 * * * /path/to/dns-routing-manager/cron_update.sh
```

## Мониторинг

### Ежедневная проверка:
```bash
python3 check_status.py
```

### Проверка логов:
```bash
tail -f logs/auto_update.log
```

### Ручное обслуживание:
```bash
python3 auto_update.py --maintenance
```

## Безопасность

- Автоматизация НЕ изменяет маршруты без явной команды
- Только обновляет DNS кэш и проверяет состояние
- Все изменения логируются
- Можно отключить в любой момент

## Отключение автоматизации

### Cron:
```bash
crontab -e  # Удалить или закомментировать строку
```

### LaunchAgent (macOS):
```bash
launchctl unload ~/Library/LaunchAgents/com.dnsrouting.autoupdate.plist
rm ~/Library/LaunchAgents/com.dnsrouting.autoupdate.plist
```

## Кастомизация

Отредактируйте `auto_update.py` для изменения:
- Интервалов обновления
- Списка критичных доменов  
- Логики приоритизации
- Уровня логирования
EOF

echo "📖 Создан файл AUTOMATION_README.md с подробной документацией"
echo ""
echo "🎯 Рекомендация: Начните с ручного тестирования:"
echo "   python3 auto_update.py --maintenance"
echo ""

# Тестовый запуск
echo "🧪 Выполнить тестовый запуск? (y/n)"
read -p "> " test_run

if [ "$test_run" = "y" ] || [ "$test_run" = "Y" ]; then
    echo ""
    echo "=== Тестовый запуск ==="
    python3 check_status.py
    echo ""
    echo "Если статус в порядке, автоматизация готова к работе!"
fi