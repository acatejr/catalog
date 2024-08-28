Deployment Steps
================
1. git pull  
2. docker compose -f .docker/compose.yml up -d --build (check to see if this maybe something like reload or restart, if os level change)  
3. ./manage.py migrate
4. ./manage.py collectstatic

