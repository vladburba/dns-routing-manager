"""
DNS Resolver для DNS Routing Manager.
Обрабатывает резолвинг доменов с поддержкой wildcard и кэширования.
"""
import subprocess
import json
import time
from typing import List, Optional, Dict
from pathlib import Path
from ..models import DNSResult, DomainType, Domain
from ..config import get_config


class DNSResolver:
    """
    DNS резолвер с поддержкой кэширования и wildcard доменов.
    """
    
    def __init__(self):
        self.config = get_config()
        self.cache_file = self.config.cache_dir / "dns_cache.json"
        self.cache: Dict[str, Dict] = {}
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Загружает DNS кэш из файла"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                print(f"DNS cache loaded: {len(self.cache)} entries")
        except Exception as e:
            print(f"Warning: Could not load DNS cache: {e}")
            self.cache = {}
    
    def _save_cache(self) -> None:
        """Сохраняет DNS кэш в файл"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save DNS cache: {e}")
    
    def _is_cache_valid(self, domain: str) -> bool:
        """Проверяет валидность кэша для домена"""
        if domain not in self.cache:
            return False
        
        cached_time = self.cache[domain].get('timestamp', 0)
        ttl_seconds = self.config.cache_ttl_hours * 3600
        
        return (time.time() - cached_time) < ttl_seconds
    
    def _dig_resolve(self, domain: str) -> List[str]:
        """
        Резолвит домен используя команду dig.
        Возвращает список IPv4 адресов.
        """
        try:
            # Используем dig для резолвинга
            cmd = [
                'dig', '+short', '+time=5', '+tries=3', 
                domain, 'A'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.dns_timeout
            )
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
            
            # Фильтруем только IPv4 адреса
            ips = []
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and self._is_valid_ipv4(line):
                    ips.append(line)
            
            return ips
            
        except subprocess.TimeoutExpired:
            raise Exception(f"DNS timeout for {domain}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"DNS resolution failed for {domain}: {e.stderr}")
        except Exception as e:
            raise Exception(f"DNS error for {domain}: {str(e)}")
    
    def _is_valid_ipv4(self, ip: str) -> bool:
        """Проверяет валидность IPv4 адреса"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False
    
    def _expand_wildcard_domain(self, domain: str, domain_type: DomainType) -> List[str]:
        """
        Расширяет wildcard домены в список конкретных доменов.
        
        *.example.com -> [example.com, www.example.com]
        **.example.com -> [example.com, www.example.com, api.example.com, cdn.example.com]
        """
        domains = [domain]  # Базовый домен всегда включен
        
        if domain_type == DomainType.WILDCARD:
            # Простой wildcard: добавляем www
            domains.append(f"www.{domain}")
            
        elif domain_type == DomainType.DEEP_WILDCARD:
            # Глубокий wildcard: добавляем популярные поддомены
            common_subdomains = [
                'www', 'api', 'cdn', 'static', 'images', 'assets',
                'mail', 'ftp', 'blog', 'shop', 'store', 'admin'
            ]
            for subdomain in common_subdomains:
                domains.append(f"{subdomain}.{domain}")
        
        return domains
    
    def resolve_domain(self, domain: Domain) -> DNSResult:
        """
        Резолвит один домен с учетом его типа.
        """
        start_time = time.time()
        all_ips = []
        errors = []
        
        try:
            # Получаем список доменов для резолвинга
            domains_to_resolve = self._expand_wildcard_domain(
                domain.name, domain.domain_type
            )
            
            for dom in domains_to_resolve:
                try:
                    # Проверяем кэш
                    if self._is_cache_valid(dom):
                        cached_ips = self.cache[dom]['ips']
                        all_ips.extend(cached_ips)
                        print(f"Cache hit for {dom}: {cached_ips}")
                        continue
                    
                    # Резолвим через dig
                    ips = self._dig_resolve(dom)
                    if ips:
                        all_ips.extend(ips)
                        
                        # Сохраняем в кэш
                        self.cache[dom] = {
                            'ips': ips,
                            'timestamp': time.time()
                        }
                        print(f"Resolved {dom}: {ips}")
                    
                except Exception as e:
                    error_msg = f"Failed to resolve {dom}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Warning: {error_msg}")
            
            # Убираем дубликаты IP
            unique_ips = list(set(all_ips))
            resolution_time = time.time() - start_time
            
            # Сохраняем кэш
            if unique_ips:
                self._save_cache()
            
            success = len(unique_ips) > 0
            
            return DNSResult(
                domain=domain.name,
                ips=unique_ips,
                success=success,
                error_message="; ".join(errors) if errors else None,
                resolution_time=resolution_time
            )
            
        except Exception as e:
            resolution_time = time.time() - start_time
            error_msg = str(e)
            
            return DNSResult(
                domain=domain.name,
                ips=[],
                success=False,
                error_message=error_msg,
                resolution_time=resolution_time
            )
    
    def resolve_domains(self, domains: List[Domain]) -> List[DNSResult]:
        """
        Резолвит список доменов.
        В будущем можно добавить параллельную обработку.
        """
        results = []
        
        print(f"Resolving {len(domains)} domains...")
        
        for i, domain in enumerate(domains, 1):
            print(f"[{i}/{len(domains)}] Resolving {domain.name}...")
            result = self.resolve_domain(domain)
            results.append(result)
        
        return results
    
    def clear_cache(self) -> None:
        """Очищает DNS кэш"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        print("DNS cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Возвращает статистику кэша"""
        total_entries = len(self.cache)
        valid_entries = sum(1 for domain in self.cache.keys() 
                           if self._is_cache_valid(domain))
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': total_entries - valid_entries,
            'cache_file': str(self.cache_file)
        }
