"""
Модели данных для DNS Routing Manager.
Используем dataclasses для типизации и валидации.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from enum import Enum
from pathlib import Path
import ipaddress


class RouteType(Enum):
    """Типы маршрутов"""
    LOCAL = "local"  # Через локальную сеть
    VPN = "vpn"      # Через VPN туннель


class DomainType(Enum):
    """Типы доменов"""
    EXACT = "exact"      # точное совпадение: example.com
    WILDCARD = "wildcard"    # *.example.com
    DEEP_WILDCARD = "deep"   # **.example.com


@dataclass
class NetworkInterface:
    """Сетевой интерфейс"""
    name: str                    # en7, utun4
    gateway: Optional[str] = None    # 10.255.0.1 (для обычных интерфейсов)
    is_tunnel: bool = False      # True для utun интерфейсов
    
    def __post_init__(self):
        """Валидация после создания"""
        if not self.is_tunnel and not self.gateway:
            raise ValueError(f"Non-tunnel interface {self.name} requires gateway")


@dataclass 
class Domain:
    """Домен для маршрутизации"""
    name: str
    domain_type: DomainType
    route_type: RouteType
    resolved_ips: List[str] = field(default_factory=list)
    last_resolved: Optional[str] = None  # timestamp
    
    def __post_init__(self):
        """Определяем тип домена автоматически"""
        if self.name.startswith("**."):
            self.domain_type = DomainType.DEEP_WILDCARD
            self.name = self.name[3:]  # убираем **. 
        elif self.name.startswith("*."):
            self.domain_type = DomainType.WILDCARD  
            self.name = self.name[2:]  # убираем *.
        else:
            self.domain_type = DomainType.EXACT


@dataclass
class IPRoute:
    """IP маршрут (отдельный IP или подсеть)"""
    target: str  # IP или подсеть в формате CIDR
    route_type: RouteType
    is_network: bool = False
    
    def __post_init__(self):
        """Валидация IP и определение типа"""
        try:
            ip_obj = ipaddress.ip_network(self.target, strict=False)
            self.is_network = ip_obj.num_addresses > 1
        except ValueError:
            raise ValueError(f"Invalid IP or network: {self.target}")


@dataclass
class Route:
    """Активный маршрут в системе"""
    target: str  # IP или подсеть
    interface: str
    gateway: Optional[str] = None
    is_host: bool = True
    
    @property
    def route_key(self) -> str:
        """Уникальный ключ маршрута для кэширования"""
        return f"{self.target}:{self.interface}"


@dataclass
class RoutingConfig:
    """Полная конфигурация маршрутизации"""
    # Сетевые интерфейсы
    local_interface: NetworkInterface
    vpn_interface: NetworkInterface
    
    # Пути к файлам конфигурации
    domains_ru_file: Path
    domains_com_file: Path
    ips_local_file: Path
    ips_vpn_file: Path
    
    # Кэш и рабочие файлы
    cache_dir: Path
    routes_cache_file: Path
    log_file: Path
    
    # Параметры DNS
    dns_timeout: int = 5
    dns_retries: int = 3
    
    # Параметры кэширования
    cache_ttl_hours: int = 24
    
    def __post_init__(self):
        """Создаем необходимые директории"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class DNSResult:
    """Результат DNS резолвинга"""
    domain: str
    ips: List[str]
    success: bool
    error_message: Optional[str] = None
    resolution_time: Optional[float] = None


@dataclass
class OperationResult:
    """Результат операции с маршрутами"""
    success: bool
    message: str
    affected_routes: List[Route] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
