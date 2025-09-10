#!/usr/bin/env python3
"""
Простой тест DNS resolver'а
"""
from dns_routing.core.resolver import DNSResolver
from dns_routing.models import Domain, DomainType, RouteType

def test_dns_resolver():
    """Тестируем DNS resolver"""
    resolver = DNSResolver()
    
    # Тестовые домены
    test_domains = [
        Domain("google.com", DomainType.EXACT, RouteType.VPN),
        Domain("yandex.ru", DomainType.EXACT, RouteType.LOCAL),
        Domain("github.com", DomainType.WILDCARD, RouteType.VPN),
    ]
    
    print("=== DNS Resolver Test ===")
    
    for domain in test_domains:
        print(f"\nTesting {domain.name} ({domain.domain_type.value})...")
        result = resolver.resolve_domain(domain)
        
        if result.success:
            print(f"✅ Success: {len(result.ips)} IPs found")
            for ip in result.ips[:3]:  # Показываем первые 3 IP
                print(f"   {ip}")
            if len(result.ips) > 3:
                print(f"   ... and {len(result.ips) - 3} more")
        else:
            print(f"❌ Failed: {result.error_message}")
        
        print(f"   Resolution time: {result.resolution_time:.2f}s")
    
    # Статистика кэша
    print(f"\n=== Cache Stats ===")
    stats = resolver.get_cache_stats()
    print(f"Total entries: {stats['total_entries']}")
    print(f"Valid entries: {stats['valid_entries']}")

if __name__ == "__main__":
    test_dns_resolver()
