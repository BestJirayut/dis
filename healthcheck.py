"""
Health check web server เล็กๆ สำหรับ Fly.io
เปิดพอร์ต 8080 ให้ platform ตรวจสอบว่าแอปยังทำงานอยู่
รันคู่ขนานกับบอท Discord ด้วย asyncio
"""

import os
from aiohttp import web


async def handle_root(request: web.Request) -> web.Response:
    return web.Response(text="Announcement bot is running ✅")


async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def build_app() -> web.Application:
    app = web.Application()
    app.add_routes(
        [
            web.get("/", handle_root),
            web.get("/health", handle_health),
        ]
    )
    return app


async def start_health_server():
    """เริ่ม web server แบบ non-blocking — เรียกจาก async context"""
    port = int(os.environ.get("PORT", "8080"))
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    return runner
