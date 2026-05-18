#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "未找到 docker，请先安装 Docker。" >&2
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "已从 .env.example 创建 .env，建议修改 DJANGO_SECRET_KEY。"
fi

docker compose up -d --build

PORT=8080
if [ -f .env ]; then
  val=$(grep -E '^[[:space:]]*WEB_PORT[[:space:]]*=' .env | head -1 | cut -d= -f2 | tr -d ' \r')
  [ -n "$val" ] && PORT="$val"
fi

echo ""
echo "部署完成。浏览器打开: http://localhost:${PORT}"
echo "创建管理员: docker compose exec api python manage.py createsuperuser"
