"""
Route Manager для DNS Routing Manager.
Управляет системными маршрутами через команды route в macOS.
"""
import subprocess
import json
import os
from typing import List, Dict, Optional, Set
from pathlib import Path
from ..models import Route, NetworkInterface, OperationResult, RouteType
from ..config import get_config


class RouteManager:
    """
    Менеджер маршрутов для macOS.
    Управляет добавлением/удалением маршрутов через команду route.
    """
    
    def __init__(self):
        self.config = get_config()
        self.routes_cache_file = self.config.routes_cache_file
        self.active_routes: Set[str] = set()
        self._load_routes_cache()
    
    def _load_routes_cache(self) -> None:
        """Загружает кэш активных маршрутов"""
        try:
            if self.routes_cache_file.exists():
                with open(self.routes_cache_file, 'r') as f:
                    data = json.load(f)
                    self.active_routes = set(data.get('routes', []))
                print(f"Routes cache loaded: {len(self.active_routes)} active routes")
        except Exception as e:
            print(f"Warning: Could not load routes cache: {e}")
            self.active_routes = set()
    
    def _save_routes_cache(self) -> None:
        """Сохраняет кэш активных маршрутов"""
        try:
            # Создаем директорию с правильными правами
            self.routes_cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Если запущено под sudo, получаем реального пользователя
            real_user = os.environ.get('SUDO_USER')
            if real_user:
                import pwd
                real_uid = pwd.getpwnam(real_user).pw_uid
                real_gid = pwd.getpwnam(real_user).pw_gid
            
            data = {
                'routes': list(self.active_routes),
                'timestamp': __import__('time').time()
            }
            
            # Записываем файл
            with open(self.routes_cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Меняем владельца файла на реального пользователя
            if real_user:
                os.chown(self.routes_cache_file, real_uid, real_gid)
                
        except Exception as e:
            # Не показываем ошибку каждый раз - логируем только один раз
            if not hasattr(self, '_cache_error_shown'):
                print(f"Info: Routes cache disabled due to permissions")
                self._cache_error_shown = True
    
    def _check_sudo(self) -> bool:
        """Проверяет доступность sudo"""
        try:
            result = subprocess.run(
                ['sudo', '-n', 'true'], 
                capture_output=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_route_command(self, cmd: List[str]) -> tuple[bool, str]:
        """
        Выполняет команду route с обработкой ошибок.
        Возвращает (success, output/error)
        """
        try:
            # Добавляем sudo если требуется
            if getattr(self.config, "security", {}).get('require_sudo', True):
                cmd = ['sudo'] + cmd
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Проверяет валидность IP адреса"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def _parse_network(self, target: str) -> tuple[str, bool]:
        """
        Парсит сетевой адрес и определяет тип.
        Возвращает (target, is_network)
        """
        if '/' in target:
            # CIDR нотация: 192.168.1.0/24
            network, prefix = target.split('/')
            try:
                prefix_int = int(prefix)
                if 0 <= prefix_int <= 32:
                    return target, True
            except ValueError:
                pass
        
        # Проверяем как обычный IP
        if self._is_valid_ip(target):
            return target, False
        
        raise ValueError(f"Invalid IP or network: {target}")
    
    def add_route(self, target: str, route_type: RouteType) -> OperationResult:
        """
        Добавляет маршрут для IP или подсети.
        
        Args:
            target: IP адрес или подсеть (192.168.1.1 или 192.168.0.0/16)
            route_type: LOCAL или VPN
        """
        try:
            # Парсим target
            parsed_target, is_network = self._parse_network(target)
            
            # Выбираем интерфейс
            if route_type == RouteType.LOCAL:
                interface = self.config.local_interface
            else:
                interface = self.config.vpn_interface
            
            # Создаем ключ для кэша
            route_key = f"{parsed_target}:{interface.name}"
            
            # Проверяем что маршрут еще не добавлен
            if route_key in self.active_routes:
                return OperationResult(
                    success=True,
                    message=f"Route {parsed_target} via {interface.name} already exists",
                    affected_routes=[]
                )
            
            # Формируем команду route
            if is_network:
                # Для подсети
                cmd = ['route', 'add', '-net', parsed_target]
            else:
                # Для отдельного хоста
                cmd = ['route', 'add', '-host', parsed_target]
            
            # Добавляем интерфейс или gateway
            if interface.is_tunnel:
                # Для туннельных интерфейсов (utun)
                cmd.extend(['-interface', interface.name])
            else:
                # Для обычных интерфейсов через gateway
                if not interface.gateway:
                    raise ValueError(f"Gateway required for interface {interface.name}")
                cmd.append(interface.gateway)
            
            # Выполняем команду
            success, output = self._run_route_command(cmd)
            
            if success:
                # Добавляем в кэш
                self.active_routes.add(route_key)
                self._save_routes_cache()
                
                route = Route(
                    target=parsed_target,
                    interface=interface.name,
                    gateway=interface.gateway if not interface.is_tunnel else None,
                    is_host=not is_network
                )
                
                return OperationResult(
                    success=True,
                    message=f"Route added: {parsed_target} via {interface.name}",
                    affected_routes=[route]
                )
            else:
                return OperationResult(
                    success=False,
                    message=f"Failed to add route: {output}",
                    errors=[output]
                )
                
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Error adding route for {target}: {str(e)}",
                errors=[str(e)]
            )
    
    def remove_route(self, target: str) -> OperationResult:
        """
        Удаляет маршрут для IP или подсети.
        """
        try:
            # Парсим target
            parsed_target, is_network = self._parse_network(target)
            
            # Формируем команду route delete
            if is_network:
                cmd = ['route', 'delete', '-net', parsed_target]
            else:
                cmd = ['route', 'delete', '-host', parsed_target]
            
            # Выполняем команду
            success, output = self._run_route_command(cmd)
            
            if success:
                # Удаляем из кэша (пробуем все возможные интерфейсы)
                routes_to_remove = [key for key in self.active_routes 
                                  if key.startswith(f"{parsed_target}:")]
                
                for route_key in routes_to_remove:
                    self.active_routes.discard(route_key)
                
                self._save_routes_cache()
                
                return OperationResult(
                    success=True,
                    message=f"Route removed: {parsed_target}",
                    affected_routes=[]
                )
            else:
                # Маршрут может уже отсутствовать - это не ошибка
                if "not in table" in output.lower() or "no such process" in output.lower():
                    return OperationResult(
                        success=True,
                        message=f"Route {parsed_target} was not present",
                        affected_routes=[]
                    )
                else:
                    return OperationResult(
                        success=False,
                        message=f"Failed to remove route: {output}",
                        errors=[output]
                    )
                    
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Error removing route for {target}: {str(e)}",
                errors=[str(e)]
            )
    
    def add_routes_bulk(self, targets: List[str], route_type: RouteType) -> OperationResult:
        """
        Добавляет множество маршрутов за один вызов.
        """
        all_routes = []
        all_errors = []
        success_count = 0
        
        print(f"Adding {len(targets)} routes via {route_type.value}...")
        
        for i, target in enumerate(targets, 1):
            print(f"[{i}/{len(targets)}] Adding route for {target}...")
            
            result = self.add_route(target, route_type)
            
            if result.success:
                success_count += 1
                all_routes.extend(result.affected_routes)
                print(f"  ✅ {result.message}")
            else:
                all_errors.extend(result.errors)
                print(f"  ❌ {result.message}")
        
        overall_success = success_count > 0
        
        return OperationResult(
            success=overall_success,
            message=f"Added {success_count}/{len(targets)} routes successfully",
            affected_routes=all_routes,
            errors=all_errors
        )
    
    def check_route(self, target: str) -> Optional[Dict]:
        """
        Проверяет существующий маршрут для IP.
        Возвращает информацию о маршруте или None.
        """
        try:
            cmd = ['route', '-n', 'get', target]
            success, output = self._run_route_command(cmd)
            
            if success:
                # Парсим вывод route get
                route_info = {}
                for line in output.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        route_info[key.strip()] = value.strip()
                
                return route_info
            
            return None
            
        except Exception as e:
            print(f"Error checking route for {target}: {e}")
            return None
    
    def get_active_routes_count(self) -> int:
        """Возвращает количество активных маршрутов"""
        return len(self.active_routes)
    
    def clear_all_routes(self) -> OperationResult:
        """
        Удаляет все маршруты из кэша.
        ВНИМАНИЕ: Это может нарушить сетевое соединение!
        """
        if not self.active_routes:
            return OperationResult(
                success=True,
                message="No routes to clear",
                affected_routes=[]
            )
        
        errors = []
        removed_count = 0
        
        # Создаем копию для итерации
        routes_to_remove = list(self.active_routes)
        
        for route_key in routes_to_remove:
            target = route_key.split(':')[0]
            result = self.remove_route(target)
            
            if result.success:
                removed_count += 1
            else:
                errors.extend(result.errors)
        
        return OperationResult(
            success=removed_count > 0,
            message=f"Removed {removed_count}/{len(routes_to_remove)} routes",
            affected_routes=[],
            errors=errors
        )
