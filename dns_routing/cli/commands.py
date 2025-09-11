"""
CLI команды для DNS Routing Manager.
Использует Click для создания удобного интерфейса.
"""
import click
import sys
from typing import List
from pathlib import Path

from ..core.resolver import DNSResolver
from ..core.route_manager import RouteManager
from ..models import Domain, DomainType, RouteType
from ..config import get_config


@click.group(name="dns-routing")
@click.version_option(version="1.0.0", prog_name="DNS Routing Manager")
def cli():
    """
    DNS Routing Manager - Инструмент для селективной маршрутизации сетевого трафика.
    
    Позволяет направлять трафик через разные интерфейсы на основе доменных имен.
    """
    pass


@cli.command()
def status():
    """Показать текущий статус системы"""
    click.echo("=== DNS Routing Manager Status ===")
    
    try:
        config = get_config()
        
        click.echo(f"📡 Local Interface: {config.local_interface.name} (gateway: {config.local_interface.gateway})")
        click.echo(f"🔒 VPN Interface: {config.vpn_interface.name}")
        
        # Статистика DNS кэша
        resolver = DNSResolver()
        dns_stats = resolver.get_cache_stats()
        click.echo(f"🗄️  DNS Cache: {dns_stats['valid_entries']}/{dns_stats['total_entries']} valid entries")
        
        # Статистика маршрутов
        route_manager = RouteManager()
        routes_count = route_manager.get_active_routes_count()
        click.echo(f"🛣️  Active Routes: {routes_count}")
        
        # Проверяем файлы конфигурации
        config_files = [
            ("domains_ru.txt", config.domains_ru_file),
            ("domains_com.txt", config.domains_com_file),
            ("ips_local.txt", config.ips_local_file),
            ("ips_vpn.txt", config.ips_vpn_file),
        ]
        
        click.echo("\n📁 Configuration Files:")
        for name, path in config_files:
            if path.exists():
                line_count = len(path.read_text().strip().split('\n'))
                click.echo(f"   ✅ {name}: {line_count} entries")
            else:
                click.echo(f"   ❌ {name}: not found")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def dns():
    """DNS резолвинг и кэш операции"""
    pass


@dns.command()
@click.argument('domain')
@click.option('--type', 'domain_type', 
              type=click.Choice(['exact', 'wildcard', 'deep']), 
              default='exact',
              help='Тип домена для резолвинга')
def resolve(domain, domain_type):
    """Резолвить домен в IP адреса"""
    click.echo(f"Resolving {domain} ({domain_type})...")
    
    try:
        resolver = DNSResolver()
        
        # Создаем объект домена
        domain_obj = Domain(
            name=domain,
            domain_type=DomainType(domain_type),
            route_type=RouteType.VPN  # Временно, для тестирования
        )
        
        result = resolver.resolve_domain(domain_obj)
        
        if result.success:
            click.echo(f"✅ Success: Found {len(result.ips)} IP addresses")
            for ip in result.ips:
                click.echo(f"   {ip}")
            click.echo(f"Resolution time: {result.resolution_time:.3f}s")
        else:
            click.echo(f"❌ Failed: {result.error_message}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@dns.command()
def cache():
    """Показать статистику DNS кэша"""
    try:
        resolver = DNSResolver()
        stats = resolver.get_cache_stats()
        
        click.echo("=== DNS Cache Stats ===")
        click.echo(f"Total entries: {stats['total_entries']}")
        click.echo(f"Valid entries: {stats['valid_entries']}")
        click.echo(f"Expired entries: {stats['expired_entries']}")
        click.echo(f"Cache file: {stats['cache_file']}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@dns.command()
@click.confirmation_option(prompt='Are you sure you want to clear DNS cache?')
def clear():
    """Очистить DNS кэш"""
    try:
        resolver = DNSResolver()
        resolver.clear_cache()
        click.echo("✅ DNS cache cleared")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@cli.group()
def routes():
    """Управление маршрутами"""
    pass


@routes.command()
@click.argument('target')
@click.option('--via', type=click.Choice(['local', 'vpn']), required=True,
              help='Маршрутизировать через local или vpn')
def add(target, via):
    """Добавить маршрут для IP или подсети"""
    click.echo(f"Adding route {target} via {via}...")
    
    try:
        route_manager = RouteManager()
        route_type = RouteType.LOCAL if via == 'local' else RouteType.VPN
        
        result = route_manager.add_route(target, route_type)
        
        if result.success:
            click.echo(f"✅ {result.message}")
        else:
            click.echo(f"❌ {result.message}")
            for error in result.errors:
                click.echo(f"   Error: {error}")
                
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@routes.command()
@click.argument('target')
def remove(target):
    """Удалить маршрут для IP или подсети"""
    click.echo(f"Removing route for {target}...")
    
    try:
        route_manager = RouteManager()
        result = route_manager.remove_route(target)
        
        if result.success:
            click.echo(f"✅ {result.message}")
        else:
            click.echo(f"❌ {result.message}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@routes.command()
@click.argument('target')
def check(target):
    """Проверить существующий маршрут"""
    click.echo(f"Checking route for {target}...")
    
    try:
        route_manager = RouteManager()
        route_info = route_manager.check_route(target)
        
        if route_info:
            click.echo("✅ Route found:")
            for key, value in route_info.items():
                click.echo(f"   {key}: {value}")
        else:
            click.echo("❌ No route found")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@routes.command()
@click.confirmation_option(prompt='Are you sure you want to clear all routes?')
def clear():
    """Очистить все маршруты (ОСТОРОЖНО!)"""
    click.echo("⚠️  Clearing all routes...")
    
    try:
        route_manager = RouteManager()
        result = route_manager.clear_all_routes()
        
        if result.success:
            click.echo(f"✅ {result.message}")
        else:
            click.echo(f"❌ {result.message}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


def load_domains_from_file(file_path: Path) -> List[str]:
    """Загружает домены из файла, игнорируя комментарии"""
    domains = []
    
    if not file_path.exists():
        return domains
    
    for line in file_path.read_text().strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            domains.append(line)
    
    return domains


@cli.command()
@click.option('--ru-only', is_flag=True, help='Обработать только российские домены')
@click.option('--com-only', is_flag=True, help='Обработать только международные домены')
@click.option('--dry-run', is_flag=True, help='Показать что будет сделано без выполнения')
def process(ru_only, com_only, dry_run):
    """Обработать все домены из конфигурационных файлов"""
    
    if dry_run:
        click.echo("🔍 DRY RUN MODE - команды не будут выполнены")
    
    try:
        config = get_config()
        resolver = DNSResolver()
        route_manager = RouteManager()
        
        tasks = []
        
        # Загружаем российские домены
        if not com_only:
            ru_domains = load_domains_from_file(config.domains_ru_file)
            if ru_domains:
                tasks.append(('Russian domains', ru_domains, RouteType.LOCAL))
                click.echo(f"📁 Loaded {len(ru_domains)} Russian domains")
        
        # Загружаем международные домены
        if not ru_only:
            com_domains = load_domains_from_file(config.domains_com_file)
            if com_domains:
                tasks.append(('International domains', com_domains, RouteType.VPN))
                click.echo(f"📁 Loaded {len(com_domains)} international domains")
        
        if not tasks:
            click.echo("❌ No domains to process")
            return
        
        # Обрабатываем каждую группу доменов
        for group_name, domain_names, route_type in tasks:
            click.echo(f"\n=== Processing {group_name} ===")
            
            # Создаем объекты доменов
            domains = []
            for domain_name in domain_names:
                domain = Domain(
                    name=domain_name,
                    domain_type=DomainType.EXACT,  # Определится автоматически в __post_init__
                    route_type=route_type
                )
                domains.append(domain)
            
            if dry_run:
                click.echo(f"Would resolve {len(domains)} domains and add routes via {route_type.value}")
                continue
            
            # Резолвим домены
            click.echo(f"🔍 Resolving {len(domains)} domains...")
            results = resolver.resolve_domains(domains)
            
            # Собираем все IP для добавления маршрутов
            all_ips = []
            for result in results:
                if result.success:
                    all_ips.extend(result.ips)
            
            if all_ips:
                # Убираем дубликаты
                unique_ips = list(set(all_ips))
                click.echo(f"🛣️  Adding {len(unique_ips)} unique routes...")
                
                # Добавляем маршруты
                route_result = route_manager.add_routes_bulk(unique_ips, route_type)
                
                if route_result.success:
                    click.echo(f"✅ {route_result.message}")
                else:
                    click.echo(f"❌ {route_result.message}")
            else:
                click.echo("❌ No IPs resolved for routing")
        
        click.echo(f"\n✅ Processing complete!")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
