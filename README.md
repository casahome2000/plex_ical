
# plex_ical

A lightweight Flask-based service that merges your **Sonarr** and **Radarr** calendars into a **single iCal feed**.  
Useful for keeping track of upcoming shows and movies in one place.  

Runs as a Docker container (tested on Synology NAS with Portainer, and Docker).

---

## Features
- ✅ Merges multiple iCal feeds (Sonarr + Radarr) into a single `.ics`
- ✅ Configurable via **environment variables at runtime** (no secrets in the image)
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

### 1) Clone
```bash
git clone https://github.com/casahome2000/plex_ical.git
cd plex_ical
```

### 2) Configure env vars
Copy and edit:
```bash
cp .env.sample .env
```

Example:
```env
SONARR_ICAL_URL=http://sonarr-ip:8989/feed/v3/calendar/Sonarr.ics?apikey=YOUR_SONARR_API_KEY
RADARR_ICAL_URL=http://radarr-ip:7878/feed/v3/calendar/Radarr.ics?apikey=YOUR_RADARR_API_KEY
CAL_NAME=media_Entertainment
REFRESH_SECONDS=1800
VERIFY_SSL=true
TZ=America/Chicago
```

---

## Running Locally (testing)
```bash
docker compose up --build
```
Open: [http://localhost:5181/calendar](http://localhost:5181/calendar)

---



## Deploying to Synology with Portainer

### Option A — Pull from Docker Hub (recommended)
```yaml
version: "3.9"
services:
  plex_ical:
    image: casahome2000/plex_ical:latest
    container_name: plex_ical
    environment:
      SONARR_ICAL_URL: "http://192.168.1.10:8989/feed/v3/calendar/Sonarr.ics?apikey=YOUR_SONARR_API_KEY"
      RADARR_ICAL_URL: "http://192.168.1.10:7878/feed/v3/calendar/Radarr.ics?apikey=YOUR_RADARR_API_KEY"
      CAL_NAME: "media_Entertainment"
      REFRESH_SECONDS: "1800"
      VERIFY_SSL: "true"
      TZ: "America/Chicago"
    ports:
      - "5181:8000"
    restart: unless-stopped
```

### Option B — Build on Synology
SSH or copy project to `/volume1/docker/plex_ical/`, then:
```bash
cd /volume1/docker/plex_ical
docker build -t plex_ical:latest .
```
Stack:
```yaml
version: "3.9"
services:
  plex_ical:
    image: plex_ical:latest
    container_name: plex_ical
    environment:
      SONARR_ICAL_URL: "http://192.168.1.10:8989/feed/v3/calendar/Sonarr.ics?apikey=YOUR_SONARR_API_KEY"
      RADARR_ICAL_URL: "http://192.168.1.10:7878/feed/v3/calendar/Radarr.ics?apikey=YOUR_RADARR_API_KEY"
      CAL_NAME: "media_Entertainment"
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
1. **Calendar.app → File → New Calendar Subscription…**  
2. Enter:
   ```
   http://<synology-ip>:5181/calendar
   ```
3. Subscribe. It appears as a separate calendar named from `CAL_NAME`.

### iPhone/iPad
Settings → Calendar → Accounts → Add Account → Other → **Add Subscribed Calendar**  
Use: `http://<synology-ip>:5181/calendar`

---

## Endpoints
- `/calendar` → merged iCal feed  
- `/health` → JSON health info  
- `/` → basic info

---

## Troubleshooting
- **“path not found” when building in Portainer**: Wrong endpoint or engine can’t read the host path. Fix by building locally on NAS or using Docker Hub.  
- **`env_file` errors in Portainer**: Some setups can’t see host paths; use `environment:`.  
- **Apple Calendar fails with `webcal://`**: Use `http://<ip>:port/calendar`. Optionally patch app to serve `/calendar.ics`.  


---

## License
GNU General Public License v3.0
