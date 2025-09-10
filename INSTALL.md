# 🚀 Установка DNS Routing Manager

**Автоматическая установка на macOS в одну команду**

## ⚡ Быстрая установка

```bash
curl -fsSL https://raw.githubusercontent.com/vladburba/dns-routing-manager/main/install.sh | bash
```

**Или скачайте и запустите:**

```bash
# 1. Скачайте установщик
curl -O https://raw.githubusercontent.com/vladburba/dns-routing-manager/main/install.sh

# 2. Сделайте исполняемым
chmod +x install.sh

# 3. Запустите установку
./install.sh
```

## 📋 Что установщик делает

1. **Проверяет совместимость** с macOS
2. **Устанавливает Homebrew** (если нет)
3. **Устанавливает Python 3.12+** (если нет)
4. **Скачивает последнюю версию** с GitHub
5. **Настраивает виртуальное окружение** Python
6. **Создает команду `dns-routing`** доступную везде
7. **Автоматически определяет** ваши сетевые интерфейсы

## ✅ После установки

### Проверьте установку:
```bash
dns-routing status
```

### Основные команды:
```bash
# Показать справку
dns-routing --help

# Протестировать DNS резолвинг
dns-routing dns resolve yandex.ru
dns-routing dns resolve google.com

# Показать что будет сделано (безопасно)
dns-routing process --dry-run

# Обработать российские домены через локальную сеть
dns-routing process --ru-only

# Обработать международные домены через VPN
dns-routing process --com-only
```

## ⚙️ Настройка под вашу сеть

### 1. Определите ваши интерфейсы:
```bash
# Посмотрите активные интерфейсы
ifconfig | grep -E "^(en|utun)"

# Посмотрите gateway
netstat -rn | grep default
```

### 2. Отредактируйте конфигурацию:
```bash
# Откройте файл конфигурации
nano ~/dns-routing-manager/config/settings.yaml
```

Измените секцию `network`:
```yaml
network:
  local:
    interface: "en0"        # Ваш основной интерфейс (WiFi/Ethernet)
    gateway: "192.168.1.1"  # Ваш роутер
  vpn:
    interface: "utun0"      # Ваш VPN интерфейс
```

### 3. Настройте домены:
```bash
# Российские домены (через локальную сеть)
nano ~/dns-routing-manager/config/domains_ru.txt

# Международные домены (через VPN)
nano ~/dns-routing-manager/config/domains_com.txt
```

## 🔧 Примеры доменов

### domains_ru.txt (локальная сеть):
```
yandex.ru
mail.ru
sberbank.ru
tinkoff.ru
*.gov.ru
*.edu.ru
```

### domains_com.txt (VPN):
```
github.com
stackoverflow.com
*.amazonaws.com
*.googleapis.com
facebook.com
twitter.com
```

## 🆘 Решение проблем

### Ошибка прав доступа:
```bash
# Дайте права администратора
sudo -v
```

### VPN интерфейс не найден:
```bash
# Подключитесь к VPN сначала
# Проверьте доступные интерфейсы:
ifconfig | grep utun
```

### Команда dns-routing не найдена:
```bash
# Перезапустите терминал или выполните:
export PATH="/usr/local/bin:$PATH"
```

### Проблемы с DNS:
```bash
# Проверьте что dig установлен:
which dig

# Если нет - установите:
brew install bind
```

## 🗑️ Удаление

```bash
# Удалить приложение
rm -rf ~/dns-routing-manager

# Удалить команду
sudo rm /usr/local/bin/dns-routing

# Очистить маршруты (если были добавлены)
# dns-routing routes clear  # Перед удалением!
```

## 📞 Поддержка

- **GitHub Issues**: https://github.com/vladburba/dns-routing-manager/issues
- **Документация**: https://github.com/vladburba/dns-routing-manager
- **Email**: vladburba@example.com

## ⚠️ Важные замечания

- **Требуется macOS** (тестировалось на Sequoia 15.6.1+)
- **Требуются права sudo** для изменения маршрутов
- **VPN должен быть подключен** для работы с VPN интерфейсами
- **Маршруты сбрасываются** при перезагрузке системы
- **Всегда тестируйте** в dry-run режиме перед применением
