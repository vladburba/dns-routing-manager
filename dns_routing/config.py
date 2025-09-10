"""
Загрузчик конфигурации для DNS Routing Manager.
Использует YAML для читаемости и singleton для единого экземпляра.
"""
import yaml
import os
from pathlib import Path
from typing import Optional
from .models import RoutingConfig, NetworkInterface


class ConfigLoader:
    """
    Singleton класс для загрузки конфигурации.
    Обеспечивает единую точку доступа к настройкам.
    """
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[RoutingConfig] = None
    
    def __new__(cls) -> 'ConfigLoader':
        """Singleton паттерн"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация только при первом создании"""
        if self._config is None:
            self._load_config()
    
    def _find_config_file(self) -> Path:
        """
        Ищем файл конфигурации в нескольких местах:
        1. Переменная окружения DNS_ROUTING_CONFIG
        2. config/settings.yaml в текущей директории
        3. ~/.dns-routing/settings.yaml
        4. /etc/dns-routing/settings.yaml
        """
        # Проверяем переменную окружения
        env_config = os.getenv('DNS_ROUTING_CONFIG')
        if env_config:
            config_path = Path(env_config)
            if config_path.exists():
                return config_path
        
        # Список возможных путей
        possible_paths = [
            Path.cwd() / "config" / "settings.yaml",
            Path.home() / ".dns-routing" / "settings.yaml", 
            Path("/etc/dns-routing/settings.yaml")
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        # Если ничего не найдено, создаем дефолтный в текущей директории
        default_path = Path.cwd() / "config" / "settings.yaml"
        if not default_path.exists():
            raise FileNotFoundError(f"Configuration file not found. Expected at: {default_path}")
        return default_path
    
    def _load_config(self) -> None:
        """Загружает конфигурацию из YAML файла"""
        config_file = self._find_config_file()
        
        try:
            with open(config_file, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            # Преобразуем относительные пути в абсолютные
            base_dir = config_file.parent.parent
            
            # Создаем объекты сетевых интерфейсов
            local_net = yaml_data['network']['local']
            vpn_net = yaml_data['network']['vpn']
            
            local_interface = NetworkInterface(
                name=local_net['interface'],
                gateway=local_net.get('gateway'),
                is_tunnel=local_net.get('is_tunnel', False)
            )
            
            vpn_interface = NetworkInterface(
                name=vpn_net['interface'], 
                gateway=vpn_net.get('gateway'),
                is_tunnel=vpn_net.get('is_tunnel', True)
            )
            
            # Создаем конфигурацию
            self._config = RoutingConfig(
                local_interface=local_interface,
                vpn_interface=vpn_interface,
                domains_ru_file=base_dir / yaml_data['files']['domains']['ru'],
                domains_com_file=base_dir / yaml_data['files']['domains']['com'],
                ips_local_file=base_dir / yaml_data['files']['ips']['local'],
                ips_vpn_file=base_dir / yaml_data['files']['ips']['vpn'],
                cache_dir=base_dir / yaml_data['paths']['cache_dir'],
                routes_cache_file=base_dir / yaml_data['paths']['routes_cache'],
                log_file=base_dir / yaml_data['paths']['log_file'],
                dns_timeout=yaml_data['dns']['timeout'],
                dns_retries=yaml_data['dns']['retries'],
                cache_ttl_hours=yaml_data['cache']['ttl_hours']
            )
            
            print(f"Configuration loaded from: {config_file}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {e}")
    
    @property
    def config(self) -> RoutingConfig:
        """Возвращает загруженную конфигурацию"""
        if self._config is None:
            self._load_config()
        return self._config
    
    def reload(self) -> None:
        """Перезагружает конфигурацию"""
        self._config = None
        self._load_config()


# Глобальная функция для удобного доступа к конфигурации
def get_config() -> RoutingConfig:
    """Возвращает глобальную конфигурацию"""
    return ConfigLoader().config
