# ticketing_system/asgi.py
"""
ASGI config for ticketing_system project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter # <--- TAMBAHKAN BARIS INI
from channels.auth import AuthMiddlewareStack # <--- TAMBAHKAN BARIS INI
import tickets.routing # <--- TAMBAHKAN BARIS INI

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticketing_system.settings')

# Original Django ASGI application
django_asgi_app = get_asgi_application()

# <--- GANTI BARIS application = get_asgi_application() dengan BLOK INI ---
application = ProtocolTypeRouter({
    "http": django_asgi_app, # Untuk permintaan HTTP biasa
    "websocket": AuthMiddlewareStack( # Untuk permintaan WebSocket, dengan autentikasi
        URLRouter(
            tickets.routing.websocket_urlpatterns # Mengarahkan ke routing WebSocket aplikasi 'tickets'
        )
    ),
})