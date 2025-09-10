import os

# Читаем текущий route_manager.py
with open('dns_routing/core/route_manager.py', 'r') as f:
    content = f.read()

# Заменяем проблемную функцию _save_routes_cache
old_function = '''    def _save_routes_cache(self) -> None:
        """Сохраняет кэш активных маршрутов"""
        try:
            self.routes_cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'routes': list(self.active_routes),
                'timestamp': __import__('time').time()
            }
            with open(self.routes_cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save routes cache: {e}")'''

new_function = '''    def _save_routes_cache(self) -> None:
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
                self._cache_error_shown = True'''

# Заменяем в коде
content = content.replace(old_function, new_function)

# Добавляем import os в начало файла если его нет
if 'import os' not in content:
    content = content.replace('import subprocess', 'import subprocess\nimport os')

# Записываем исправленный файл
with open('dns_routing/core/route_manager.py', 'w') as f:
    f.write(content)

print("✅ Route manager исправлен для работы с правами доступа")
