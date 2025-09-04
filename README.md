# plex_ical

A lightweight Flask-based service that merges your **Sonarr** and **Radarr** calendars into a **single iCal feed**.  
Useful for keeping track of upcoming shows and movies in one place.  

Runs as a Docker container (tested on Synology NAS with Portainer).

---

## Features
- ✅ Merges multiple iCal feeds (Sonarr + Radarr) into a single `.ics`
- ✅ Configurable via environment variables
- ✅ Adds proper `X-WR-CALNAME` so it shows as its own calendar
- ✅ Caches events to reduce load on Sonarr/Radarr
- ✅ Health check endpoint (`/health`)
- ✅ Works with Apple Calendar, Google Calendar, Outlook, etc.

---

## Requirements
- Docker or Docker Desktop (local testing)  
- Portainer (for Synology deployment)  

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/casahome2000/plex_ical.git
cd plex_ical
```

### 2. Configure environment variables
Copy the sample file and update it with your real Sonarr/Radarr iCal URLs:
```bash
cp .env.sample .env
```

Example:
```env
SONARR_ICAL_URL=http://192.168.1.10:8989/calendar?apikey=SONARR_KEY
RADARR_ICAL_URL=http://192.168.1.10:7878/calendar?apikey=RADARR_KEY

CAL_NAME=calendar_Entertainment
REFRESH_SECONDS=1800
VERIFY_SSL=true
TZ=America/Chicago
```

> 🔑 Sonarr/Radarr iCal links are in **Settings → Connect → iCal**.  

---

## Running Locally (for testing)

```bash
docker compose up --build
```

Open in browser:  
[http://localhost:5181/calendar](http://localhost:5181/calendar)

---

## Deploying to Synology with Portainer

### Option A: Use Prebuilt Image (recommended)
1. Build & push from your dev machine:
   ```bash
   docker build -t yourdockerhubuser/plex_ical:1 .
   docker push yourdockerhubuser/plex_ical:1
   ```

2. In Portainer → Stacks, create a new stack with:
   ```yaml
   version: "3.9"
   services:
     plex_ical:
       image: yourdockerhubuser/plex_ical:1
       container_name: plex_ical
       environment:
         SONARR_ICAL_URL: "http://192.168.1.10:8989/calendar?apikey=SONARR_KEY"
         RADARR_ICAL_URL: "http://192.168.1.10:7878/calendar?apikey=RADARR_KEY"
         CAL_NAME: "calendar_Entertainment"
         REFRESH_SECONDS: "1800"
         VERIFY_SSL: "true"
         TZ: "America/Chicago"
       ports:
         - "5181:8000"
       restart: unless-stopped
   ```

3. Deploy and you’re done.

---

### Option B: Build on Synology
1. Copy the project folder (`app.py`, `Dockerfile`, etc.) to `/volume1/docker/plex_ical/`.
2. SSH into your Synology and build the image:
   ```bash
   cd /volume1/docker/plex_ical
   docker build -t plex_ical:1 .
   ```
3. In Portainer, deploy a stack using the local image:
   ```yaml
   version: "3.9"
   services:
     plex_ical:
       image: plex_ical:1
       container_name: plex_ical
       environment:
         SONARR_ICAL_URL: "http://192.168.1.10:8989/calendar?apikey=SONARR_KEY"
         RADARR_ICAL_URL: "http://192.168.1.10:7878/calendar?apikey=RADARR_KEY"
         CAL_NAME: "calendar_Entertainment"
         REFRESH_SECONDS: "1800"
         VERIFY_SSL: "true"
         TZ: "America/Chicago"
       ports:
         - "5181:8000"
       restart: unless-stopped
   ```

---

## Using the Calendar Feed

### Apple Calendar (macOS)
⚠️ **Important**: Apple Calendar may fail with `webcal://`. Always use the **http://** URL unless you patch the server headers.

1. Open **Calendar.app**  
2. Go to **File → New Calendar Subscription…**  
3. Enter:
   ```
   http://<synology-ip>:5181/calendar
   ```
4. Click **Subscribe**  
5. It appears as a separate calendar named from `CAL_NAME`.

### iPhone/iPad (iOS)
- Go to **Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar**  
- Use:
  ```
  http://<synology-ip>:5181/calendar
  ```

---

## Endpoints
- `/calendar` → merged iCal feed  
- `/health` → JSON health info  
- `/` → basic service info  

---

## Troubleshooting
- **Portainer stack errors with `env_file`:** Portainer may not see NAS host paths. Use `environment:` instead.
- **Apple Calendar subscription fails:** Use `http://` instead of `webcal://`. Optionally patch `app.py` to serve `/calendar.ics` inline.
- **Image pull denied:** Either push to Docker Hub or build on Synology with `docker build -t plex_ical:1 .`.

---

## License
GNU General Public License v3.0
