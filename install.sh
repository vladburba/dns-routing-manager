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

# Запускаем приложение с переданными аргументами
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
    
    # Определяем сетевые интерфейсы автоматически
    LOCAL_INTERFACE=$(route get default | grep interface: | awk '{print $2}')
    GATEWAY=$(route get default | grep gateway: | awk '{print $2}')
    VPN_INTERFACE=$(ifconfig | grep -E "^utun[0-9]" | head -1 | cut -d: -f1)
    
    if [ -z "$VPN_INTERFACE" ]; then
        VPN_INTERFACE="utun0"  # Дефолтное значение
    fi
    
    # Обновляем конфигурацию
    if [ -f "config/settings.yaml" ]; then
        sed -i.bak "s/interface: \".*\"/interface: \"$LOCAL_INTERFACE\"/" config/settings.yaml
        sed -i.bak "s/gateway: \".*\"/gateway: \"$GATEWAY\"/" config/settings.yaml
        sed -i.bak "s/interface: \"utun.*\"/interface: \"$VPN_INTERFACE\"/" config/settings.yaml
        rm config/settings.yaml.bak
    fi
    
    print_success "Конфигурация настроена для $LOCAL_INTERFACE (gateway: $GATEWAY) и $VPN_INTERFACE"
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
