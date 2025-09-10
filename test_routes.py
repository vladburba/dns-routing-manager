#!/usr/bin/env python3
"""
Тест Route Manager'а (ОСТОРОЖНО: изменяет системные маршруты!)
"""
from dns_routing.core.route_manager import RouteManager
from dns_routing.models import RouteType

def test_route_manager():
    """Тестируем Route Manager"""
    manager = RouteManager()
    
    print("=== Route Manager Test ===")
    print("⚠️  ВНИМАНИЕ: Этот тест изменяет системные маршруты!")
    print("⚠️  Убедись что у тебя есть права sudo!")
    
    # Проверяем права
    input("\nНажми Enter чтобы продолжить или Ctrl+C для отмены...")
    
    # Тестовые IP (используем безопасные адреса)
    test_ips = [
        "8.8.8.8",      # Google DNS
        "1.1.1.1",      # Cloudflare DNS
    ]
    
    print(f"\n=== Добавление тестовых маршрутов ===")
    
    # Добавляем маршруты через VPN
    for ip in test_ips:
        print(f"\nДобавляем маршрут для {ip} через VPN...")
        result = manager.add_route(ip, RouteType.VPN)
        
        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")
            if result.errors:
                for error in result.errors:
                    print(f"   Error: {error}")
    
    print(f"\n=== Проверка маршрутов ===")
    
    # Проверяем что маршруты добавились
    for ip in test_ips:
        print(f"\nПроверяем маршрут для {ip}...")
        route_info = manager.check_route(ip)
        
        if route_info:
            print(f"✅ Маршрут найден:")
            print(f"   Interface: {route_info.get('interface', 'N/A')}")
            print(f"   Gateway: {route_info.get('gateway', 'N/A')}")
        else:
            print(f"❌ Маршрут не найден")
    
    print(f"\n=== Статистика ===")
    print(f"Активных маршрутов в кэше: {manager.get_active_routes_count()}")
    
    print(f"\n=== Очистка тестовых маршрутов ===")
    
    # Удаляем тестовые маршруты
    for ip in test_ips:
        print(f"\nУдаляем маршрут для {ip}...")
        result = manager.remove_route(ip)
        
        if result.success:
            print(f"✅ {result.message}")
        else:
            print(f"❌ {result.message}")
    
    print(f"\nФинальное количество маршрутов: {manager.get_active_routes_count()}")
    print("\n=== Тест завершен ===")

if __name__ == "__main__":
    test_route_manager()
