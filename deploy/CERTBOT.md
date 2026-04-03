# Let’s Encrypt (Certbot webroot)

HTTP validation is served from **`/.well-known/acme-challenge/`** via Nginx using the host directory **`/var/www/certbot`** (mounted read-only in the `nginx` container).

## 1. One-time setup on the Droplet

```bash
sudo mkdir -p /var/www/certbot
sudo chown -R root:root /var/www/certbot
```

Ensure **`api.tunedin.live`** and **`collector.tunedin.live`** DNS A records point at this Droplet, then:

```bash
cd /opt/wapow   # your clone path
docker compose -f docker-compose.prod.yml up -d nginx app collector
```

## 2. Obtain certificates (on the host)

```bash
sudo certbot certonly --webroot -w /var/www/certbot \
  -d api.tunedin.live \
  -d collector.tunedin.live
```

Certbot writes challenges under `/var/www/certbot/.well-known/acme-challenge/`; Nginx serves them from the mounted volume.

## 3. Enable HTTPS (after certs exist)

Certificates are usually stored as:

- `/etc/letsencrypt/live/api.tunedin.live/fullchain.pem`
- `/etc/letsencrypt/live/api.tunedin.live/privkey.pem`

(First `-d` name is the folder name when both names are on one certificate.)

1. Replace Nginx config with the TLS version (or merge equivalent `listen 443 ssl` blocks):

   ```bash
   sudo cp /opt/wapow/deploy/nginx-https.conf /opt/wapow/deploy/nginx.conf
   ```

2. Extend Compose for TLS: add **`443:443`** and mount **`/etc/letsencrypt`**, e.g. under `nginx`:

   ```yaml
   ports:
     - "80:80"
     - "443:443"
   volumes:
     - ./deploy/nginx.conf:/etc/nginx/nginx.conf:ro
     - /var/www/certbot:/var/www/certbot:ro
     - /etc/letsencrypt:/etc/letsencrypt:ro
   ```

3. Reload:

   ```bash
   docker compose -f docker-compose.prod.yml up -d nginx
   ```

## 4. Renewal

Certbot’s cron/systemd timer renews certs on the host. After renewal, reload Nginx so it picks up new files:

```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

Optional hook (`/etc/letsencrypt/renewal-hooks/deploy/`): run the `docker compose ... exec nginx nginx -s reload` command there.
