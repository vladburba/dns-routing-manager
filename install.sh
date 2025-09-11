#!/bin/bash
# DNS Routing Manager - Автоматический установщик для macOS
# Версия: 1.0.0

set -e  # Останавливаем при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Проверяем что мы на macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Эта программа работает только на macOS"
        exit 1
    fi
    print_success "Обнаружена macOS $(sw_vers -productVersion)"
}

# Проверяем права администратора
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        print_warning "Для установки маршрутов потребуются права администратора"
        echo "Введите пароль администратора:"
        sudo -v
    fi
    print_success "Права администратора получены"
}

# Устанавливаем Homebrew если нет
install_homebrew() {
    if command -v brew &> /dev/null; then
        print_success "Homebrew уже установлен"
        return
    fi
    
    print_info "Устанавливаем Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Добавляем Homebrew в PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    
    print_success "Homebrew установлен"
}

# Устанавливаем Python 3.12+
install_python() {
    if python3 --version 2>/dev/null | grep -E "Python 3\.(1[1-9]|[2-9][0-9])" > /dev/null; then
        print_success "Python $(python3 --version | cut -d' ' -f2) уже установлен"
        return
    fi
    
    print_info "Устанавливаем Python 3.12..."
    brew install python@3.12
    print_success "Python установлен"
}

# Создаем директорию для приложения
setup_app_directory() {
    APP_DIR="$HOME/dns-routing-manager"
    
    if [ -d "$APP_DIR" ]; then
        print_warning "Директория $APP_DIR уже существует"
        read -p "Удалить и переустановить? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$APP_DIR"
        else
            print_error "Установка отменена"
            exit 1
        fi
    fi
    
    print_info "Создаем директорию приложения..."
    mkdir -p "$APP_DIR"
    cd "$APP_DIR"
    print_success "Директория $APP_DIR создана"
}

# Скачиваем последнюю версию с GitHub
download_app() {
    print_info "Скачиваем DNS Routing Manager с GitHub..."
    
    # Скачиваем архив
    curl -L "https://github.com/vladburba/dns-routing-manager/archive/refs/heads/main.zip" -o dns-routing-manager.zip
    
    # Распаковываем
    unzip -q dns-routing-manager.zip
    mv dns-routing-manager-main/* .
    mv dns-routing-manager-main/.* . 2>/dev/null || true
    rm -rf dns-routing-manager-main dns-routing-manager.zip
    
    print_success "Приложение скачано"
}

# Создаем виртуальное окружение и устанавливаем зависимости
setup_python_environment() {
    print_info "Создаем виртуальное окружение Python..."
    python3 -m venv venv
    source venv/bin/activate
    
    print_info "Устанавливаем зависимости..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Python окружение настроено"
}

# Создаем исполняемый скрипт
create_executable() {
    print_info "Создаем исполняемый скрипт..."
    
    cat > dns-routing << 'EOF'
#!/bin/bash
# DNS Routing Manager - Запускатор

# Переходим в директорию приложения
cd "$HOME/dns-routing-manager"

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем правильное имя программы для Click
export CLICK_PROGRAM_NAME="dns-routing"
# Запускаем приложение с переданными аргументами
export CLICK_PROGRAM_NAME="dns-routing"
python3 run.py "$@"
EOF

    chmod +x dns-routing
    
    # Добавляем в PATH
    sudo ln -sf "$APP_DIR/dns-routing" /usr/local/bin/dns-routing
    
    print_success "Исполняемый файл создан: /usr/local/bin/dns-routing"
}

# Создаем конфигурацию по умолчанию
setup_default_config() {
    print_info "Настраиваем конфигурацию..."
    
    # Определяем локальный интерфейс и gateway
    LOCAL_INTERFACE=$(route get default | grep interface: | awk '{print $2}')
    GATEWAY=$(route get default | grep gateway: | awk '{print $2}')
    
    print_info "Локальный интерфейс: $LOCAL_INTERFACE (gateway: $GATEWAY)"
    
    # УМНОЕ ОПРЕДЕЛЕНИЕ VPN ИНТЕРФЕЙСА
    print_info "Определяем VPN интерфейс..."
    
    # Шаг 1: Ищем активный VPN туннель (с трафиком)
    VPN_INTERFACE=""
    
    # Получаем статистику всех utun интерфейсов
    print_info "Анализируем активность туннелей..."
    
    # Проверяем какие utun интерфейсы имеют исходящий трафик
    ACTIVE_TUNNELS=$(netstat -i | grep "utun" | awk '$10 > 0 {print $1}' | head -5)
    
    if [ -n "$ACTIVE_TUNNELS" ]; then
        # Берем первый активный туннель
        VPN_INTERFACE=$(echo "$ACTIVE_TUNNELS" | head -1)
        print_success "Найден активный VPN туннель: $VPN_INTERFACE"
    else
        print_info "Активных VPN туннелей не найдено, ищем доступные..."
        
        # Шаг 2: Если активных нет, ищем первый доступный utun
        AVAILABLE_TUNNELS=$(ifconfig | grep -E "^utun[0-9]+" | cut -d: -f1)
        
        if [ -n "$AVAILABLE_TUNNELS" ]; then
            VPN_INTERFACE=$(echo "$AVAILABLE_TUNNELS" | head -1)
            print_warning "Используется первый доступный туннель: $VPN_INTERFACE"
            print_warning "Убедитесь что VPN подключен или измените config/settings.yaml"
        else
            print_info "VPN туннели не найдены, ищем другие типы..."
            
            # Шаг 3: Проверяем другие типы VPN интерфейсов
            # ppp интерфейсы (старые VPN)
            PPP_INTERFACE=$(ifconfig | grep -E "^ppp[0-9]+" | head -1 | cut -d: -f1)
            if [ -n "$PPP_INTERFACE" ]; then
                VPN_INTERFACE="$PPP_INTERFACE"
                print_success "Найден PPP интерфейс: $VPN_INTERFACE"
            else
                # ipsec интерфейсы
                IPSEC_INTERFACE=$(ifconfig | grep -E "^ipsec[0-9]+" | head -1 | cut -d: -f1)
                if [ -n "$IPSEC_INTERFACE" ]; then
                    VPN_INTERFACE="$IPSEC_INTERFACE"
                    print_success "Найден IPSec интерфейс: $VPN_INTERFACE"
                fi
            fi
        fi
    fi
    
    # Шаг 4: Если VPN интерфейс все еще не найден, используем локальный
    if [ -z "$VPN_INTERFACE" ]; then
        VPN_INTERFACE="$LOCAL_INTERFACE"
        print_warning "VPN интерфейсы не найдены!"
        print_warning "Используется локальный интерфейс: $VPN_INTERFACE"
        print_warning "⚠️  Внимание: Локальный и VPN интерфейсы одинаковые"
        print_warning "⚠️  Отредактируйте config/settings.yaml после подключения VPN"
        VPN_IS_TUNNEL=false
    else
        VPN_IS_TUNNEL=true
    fi
    
    # Проверяем что LOCAL_INTERFACE и VPN_INTERFACE разные
    if [ "$LOCAL_INTERFACE" = "$VPN_INTERFACE" ] && [ "$VPN_IS_TUNNEL" = "true" ]; then
        print_warning "⚠️  Локальный и VPN интерфейсы одинаковые: $LOCAL_INTERFACE"
        print_warning "⚠️  Это может быть ошибкой определения"
        
        # Пытаемся найти другой туннель
        OTHER_TUNNEL=$(ifconfig | grep -E "^utun[0-9]+" | grep -v "$LOCAL_INTERFACE" | head -1 | cut -d: -f1)
        if [ -n "$OTHER_TUNNEL" ]; then
            VPN_INTERFACE="$OTHER_TUNNEL"
            print_info "Переключаемся на другой туннель: $VPN_INTERFACE"
        fi
    fi
    
    # Показываем найденные интерфейсы для отладки
    print_info "Доступные сетевые интерфейсы:"
    ifconfig | grep -E "^(en|utun|ppp|ipsec)[0-9]+" | while read -r line; do
        iface=$(echo "$line" | cut -d: -f1)
        if echo "$line" | grep -q "RUNNING"; then
            print_info "  ✅ $iface (активный)"
        else
            print_info "  ⭕ $iface (неактивный)"
        fi
    done
    
    # Обновляем конфигурацию
    if [ -f "config/settings.yaml" ]; then
        # Исправляем local интерфейс и gateway
        sed -i.bak "s/interface: \".*\" *# Твой основной интерфейс/interface: \"$LOCAL_INTERFACE\"           # Твой основной интерфейс/" config/settings.yaml
        sed -i.bak "s/gateway: \".*\" *# Твой локальный роутер/gateway: \"$GATEWAY\"      # Твой локальный роутер/" config/settings.yaml
        
        # Исправляем VPN интерфейс
        sed -i.bak "/vpn:/,/is_tunnel:/ s/interface: \".*\"/interface: \"$VPN_INTERFACE\"/" config/settings.yaml
        
        # Исправляем is_tunnel флаг для VPN
        if [ "$VPN_IS_TUNNEL" = "false" ]; then
            sed -i.bak "/vpn:/,/gateway:/ { /is_tunnel:/ s/true/false/; }" config/settings.yaml
        fi
        
        rm config/settings.yaml.bak 2>/dev/null || true
    fi
    
    print_success "✅ Конфигурация настроена:"
    print_success "   📡 Локальный: $LOCAL_INTERFACE (gateway: $GATEWAY)"
    if [ "$VPN_IS_TUNNEL" = "true" ]; then
        print_success "   🔒 VPN: $VPN_INTERFACE (туннель)"
    else
        print_warning "   ⚠️  VPN: $VPN_INTERFACE (НЕ туннель - требует настройки)"
    fi
    
    # Проверяем что интерфейсы действительно существуют
    if ! ifconfig "$LOCAL_INTERFACE" &>/dev/null; then
        print_error "❌ Локальный интерфейс $LOCAL_INTERFACE не найден!"
    fi
    
    if ! ifconfig "$VPN_INTERFACE" &>/dev/null; then
        print_error "❌ VPN интерфейс $VPN_INTERFACE не найден!"
        print_warning "   Подключите VPN или отредактируйте config/settings.yaml вручную"
    fi
    
    # Показываем рекомендации
    echo ""
    print_info "🔧 Рекомендации по настройке:"
    if [ "$VPN_IS_TUNNEL" = "false" ]; then
        print_warning "   1. Подключите VPN"
        print_warning "   2. Выполните: dns-routing status"
        print_warning "   3. При необходимости отредактируйте ~/dns-routing-manager/config/settings.yaml"
    else
        print_success "   1. Проверьте: dns-routing status"
        print_success "   2. Тестируйте: dns-routing process --dry-run"
        print_success "   3. Если нужен другой VPN туннель, отредактируйте config/settings.yaml"
    fi
    echo ""
}

# Проверяем установку
test_installation() {
    print_info "Проверяем установку..."
    
    if dns-routing status &>/dev/null; then
        print_success "DNS Routing Manager успешно установлен!"
    else
        print_warning "Установка завершена, но есть предупреждения"
        print_info "Попробуйте запустить: dns-routing status"
    fi
}

# Показываем инструкции по использованию
show_usage_instructions() {
    echo ""
    echo "🎉 Установка завершена!"
    echo ""
    echo "📋 Основные команды:"
    echo "  dns-routing status                    # Проверить статус"
    echo "  dns-routing dns resolve yandex.ru     # Протестировать DNS"
    echo "  dns-routing process --dry-run         # Показать что будет сделано"
    echo "  dns-routing process --ru-only         # Обработать .ru домены"
    echo ""
    echo "⚙️  Конфигурация:"
    echo "  Файл: $APP_DIR/config/settings.yaml"
    echo "  Домены: $APP_DIR/config/domains_*.txt"
    echo ""
    echo "🔧 Для настройки под вашу сеть:"
    echo "  1. Отредактируйте $APP_DIR/config/settings.yaml"
    echo "  2. Укажите правильные интерфейсы и gateway"
    echo "  3. Добавьте нужные домены в config/domains_*.txt"
    echo ""
    echo "❓ Помощь: dns-routing --help"
    echo "📚 Документация: https://github.com/vladburba/dns-routing-manager"
    echo ""
}

# Главная функция установки
main() {
    echo "🚀 DNS Routing Manager - Установщик для macOS"
    echo "==============================================="
    echo ""
    
    check_macos
    check_sudo
    install_homebrew
    install_python
    setup_app_directory
    download_app
    setup_python_environment
    create_executable
    setup_default_config
    test_installation
    show_usage_instructions
    
    print_success "Установка завершена успешно!"
}

# Обработка ошибок
trap 'print_error "Произошла ошибка при установке. Проверьте вывод выше."' ERR

# Запускаем установку
main "$@"
