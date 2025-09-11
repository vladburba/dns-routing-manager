# DNS Routing Manager

[![GitHub release](https://img.shields.io/github/v/release/vladburba/dns-routing-manager?style=for-the-badge)](https://github.com/vladburba/dns-routing-manager/releases)
[![macOS](https://img.shields.io/badge/macOS-Sequoia%2015.6%2B-blue?style=for-the-badge&logo=apple)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/vladburba/dns-routing-manager?style=for-the-badge)](https://github.com/vladburba/dns-routing-manager/stargazers)

**🚀 Intelligent DNS routing manager for selective VPN traffic on macOS**

> Automatically route Russian domains via local network and international domains via VPN with professional CLI management and smart interface detection.

## ⚡ Quick Start

### One-command installation:
```bash
curl -fsSL https://raw.githubusercontent.com/vladburba/dns-routing-manager/main/install.sh | bash
```

### Verify installation:
```bash
dns-routing status
```

### Test safely:
```bash
dns-routing process --dry-run
```

## 🎯 Key Features

- 🧠 **Smart VPN Detection** - Automatically finds and configures VPN interfaces
- 🇷🇺 **Selective Routing** - Russian domains via local network (faster)
- 🌍 **International Access** - Foreign domains via VPN (bypass restrictions)
- 🛡️ **Safe Testing** - Dry-run mode to preview changes
- ⚙️ **Professional CLI** - Complete command-line management
- 📦 **Zero Config** - Works out of the box with automatic setup
- 🔄 **Easy Rollback** - Remove all routes with one command

## 🏗️ Technical Highlights

- **Modern Python Architecture** with dataclasses and type hints
- **Modular Design** with clear separation of concerns
- **Production-Ready** error handling and logging
- **YAML Configuration** with intelligent defaults
- **DNS Caching** with TTL for performance optimization
- **macOS Route Management** with tunnel interface support

## 📦 Perfect For

- VPN users needing selective routing
- Corporate networks with mixed traffic requirements
- DevOps engineers learning network automation
- System administrators managing macOS deployments
- Anyone wanting intelligent traffic management

---

**Инструмент для селективной маршрутизации сетевого трафика на macOS**

Позволяет направлять трафик через разные сетевые интерфейсы (локальная сеть или VPN) на основе доменных имен и IP адресов.

## 🎯 Проблема

VPN подключения часто перехватывают весь сетевой трафик через default route. Это создает проблемы:
- Российские сайты недоступны через зарубежные VPN
- Локальные ресурсы компании недоступны при включенном VPN
- Медленная работа локальных сервисов

## ✨ Решение

DNS Routing Manager автоматически:
- Резолвит домены в IP адреса
- Создает селективные маршруты для конкретных IP
- Направляет российский трафик (.ru) через локальную сеть
- Направляет международный трафик (.com) через VPN

## 🚀 Использование

### Основные команды

```bash
# Показать статус системы
dns-routing status

# Резолвить домен
dns-routing dns resolve yandex.ru
dns-routing dns resolve github.com --type wildcard

# Управление DNS кэшем
dns-routing dns cache
dns-routing dns clear

# Управление маршрутами
dns-routing routes add 8.8.8.8 --via vpn
dns-routing routes add 192.168.1.0/24 --via local
dns-routing routes check 8.8.8.8
dns-routing routes remove 8.8.8.8

# Массовая обработка доменов
dns-routing process --dry-run          # Безопасный просмотр
dns-routing process --ru-only          # Только российские домены
dns-routing process --com-only         # Только международные домены
dns-routing process                    # Все домены
```

### Типичный workflow

1. **Проверка статуса:**
   ```bash
   dns-routing status
   ```

2. **Тестирование в dry-run режиме:**
   ```bash
   dns-routing process --dry-run
   ```

3. **Обработка российских доменов:**
   ```bash
   dns-routing process --ru-only
   ```

4. **Обработка международных доменов:**
   ```bash
   dns-routing process --com-only
   ```

5. **Проверка результатов:**
   ```bash
   dns-routing routes check yandex.ru
   dns-routing routes check google.com
   ```

## 📁 Конфигурационные файлы

### domains_ru.txt - Российские домены
```
# Поисковики
yandex.ru
mail.ru

# Банки
sberbank.ru
tinkoff.ru

# Wildcard домены
*.gov.ru
*.edu.ru
```

### domains_com.txt - Международные домены
```
# Разработка
github.com
stackoverflow.com

# Облачные сервисы (deep wildcard)
**.amazonaws.com
**.googleapis.com
```

### ips_local.txt - Локальные IP
```
# Локальные подсети
192.168.0.0/16
10.0.0.0/8

# Конкретные серверы
192.168.1.100
```

## 🔧 Возможности

### DNS Resolver
- ✅ Резолвинг доменов через `dig`
- ✅ Поддержка wildcard (`*.example.com`) и deep wildcard (`**.example.com`)
- ✅ JSON кэширование с TTL
- ✅ Параллельная обработка доменов
- ✅ Валидация IPv4 адресов

### Route Manager
- ✅ Управление маршрутами через команду `route`
- ✅ Поддержка tunnel интерфейсов (utun) и обычных (en)
- ✅ Кэширование активных маршрутов
- ✅ Batch операции для множественного добавления
- ✅ Автоматическое определение типа сети (host/network)

### CLI Interface
- ✅ Click интерфейс с подкомандами
- ✅ Цветной вывод с эмодзи
- ✅ Confirmation prompts для опасных операций
- ✅ Dry-run режим для безопасного тестирования
- ✅ Подробная справка и примеры

## 🛡️ Безопасность

- Требует sudo для изменения маршрутов
- Dry-run режим для предварительного просмотра
- Confirmation prompts для опасных операций
- Кэширование для отслеживания изменений
- Валидация всех входных данных

## 🔍 Отладка

### Проверка конфигурации
```bash
dns-routing status
```

### Проверка DNS
```bash
dns-routing dns cache
dns-routing dns resolve example.com
```

### Проверка маршрутов
```bash
# Системные команды
route -n get 8.8.8.8
netstat -rn | grep utun4

# Через наш инструмент
dns-routing routes check 8.8.8.8
```

### Очистка
```bash
# Очистить DNS кэш
dns-routing dns clear

# Очистить все маршруты (ОСТОРОЖНО!)
dns-routing routes clear
```

## 📊 Мониторинг

### Статистика
- Количество записей в DNS кэше
- Количество активных маршрутов
- Статус конфигурационных файлов
- Информация о сетевых интерфейсах

### Логи
Логи сохраняются в `logs/dns_routing.log` (при включенном логировании).

## ⚡ Производительность

- **DNS кэширование** - повторные запросы выполняются мгновенно
- **Batch операции** - обработка множества доменов за один вызов
- **Валидация IP** - быстрая проверка без внешних вызовов
- **JSON кэш маршрутов** - отслеживание без системных запросов

## 🚫 Ограничения

- Только macOS (использует специфичные команды `route`)
- Требует права sudo
- Маршруты сбрасываются при перезагрузке системы
- Динамические IP сервисов могут изменяться

## 🔮 Планы развития

- [ ] Автозапуск через launchd
- [ ] GUI интерфейс
- [ ] Поддержка IPv6
- [ ] Автоматическое обновление IP диапазонов
- [ ] Интеграция с системными уведомлениями
- [ ] Web API для удаленного управления

## 📚 DevOps практики в проекте

### Архитектурные паттерны
- **Модульная архитектура** - разделение ответственности
- **Singleton** - единая точка конфигурации  
- **Command Pattern** - CLI команды
- **Repository Pattern** - работа с данными

### Современный Python
- **Type hints** - типизация везде
- **Dataclasses** - типизированные модели
- **Pathlib** - современная работа с путями
- **Click** - профессиональный CLI

### Configuration Management
- **YAML конфигурация** - читаемые настройки
- **Переменные окружения** - гибкость развертывания
- **Автопоиск конфигурации** - удобство использования

### Тестирование и валидация
- **Input validation** - проверка всех входных данных
- **Error handling** - обработка ошибок везде
- **Dry-run режим** - безопасное тестирование

## 📄 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork проекта
2. Создайте feature branch
3. Добавьте тесты для новой функциональности
4. Убедитесь что все тесты проходят
5. Создайте Pull Request

---

**Создано в рамках изучения DevOps практик**  
**Дата:** 06.09.2025  
**Версия:** 1.2.0
