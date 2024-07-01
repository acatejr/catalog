Deployment Steps
================
1. git pull  
2. docker compose -f .docker/compose.yml up -d --build (check to see if this maybe something like reload or restart, if os level change)  
3. ./manage.py migrate
4. ./manage.py collectstatic


  services:

  mmp:
    container_name: mmp
    image: mmp
    build: .
    env_file:
      - .env
    ports:
      - 8000:8000
    volumes:
      - $PWD:/mmp
      - static:/var/www/static
      - media:/var/www/media
    tty: true
    stdin_open: true
    restart: unless-stopped
    command: "gunicorn mmp.wsgi:application --bind '0.0.0.0:8000' --reload"

  postgres:
    container_name: mmp_postgres
    image: ankane/pgvector
    ports:
      - "5432:5432"
    env_file:
      - .env
    volumes:
      - pgdata:/var/lib/postgresql/data

  caddy:
    container_name: mmp_caddy
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"

    volumes:
      # Caddy specific urls
        - $PWD/caddy/Caddyfile:/etc/caddy/Caddyfile
        - type: volume
          source: media
          target: /usr/share/caddy/media
          read_only: true
          volume:
            nocopy: true
        - type: volume
          source: static
          target: /usr/share/caddy/static
          read_only: true
          volume:
            nocopy: true
    restart: unless-stopped

volumes:
  pgdata:
  static:
  media: