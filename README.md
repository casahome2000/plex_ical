# plex_ical

A lightweight Flask-based service that merges your **Sonarr** and **Radarr** calendars into a **single iCal feed**.  
Useful for keeping track of upcoming shows and movies in one place.  

Runs as a Docker container (works well on Synology NAS with Portainer).

---

## Features
- ✅ Merges multiple iCal feeds (Sonarr + Radarr) into a single `.ics`
- ✅ Configurable via `.env` file
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
git clone https://github.com/yourusername/plex_ical.git
cd plex_ical
```

### 2. Create `.env`
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

> 🔑 You can find the iCal links in **Sonarr/Radarr → Settings → Connect → iCal**.

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
1. Build and push image from your dev machine:
   ```bash
   docker build -t yourdockerhubuser/plex_ical:1 .
   docker push yourdockerhubuser/plex_ical:1
   ```

2. In Portainer, create a **Stack** with this `docker-compose.yml`:
   ```yaml
   services:
     plex_ical:
       image: yourdockerhubuser/plex_ical:1
       container_name: plex_ical
       env_file:
         - /volume1/docker/plex_ical/.env
       ports:
         - "5181:8000"
       restart: unless-stopped
   ```

3. Place your `.env` at `/volume1/docker/plex_ical/.env` on Synology.

### Option B: Build on Synology
1. Copy the project folder (`app.py`, `Dockerfile`, `.env`, etc.) to `/volume1/docker/plex_ical/`.
2. In Portainer → Stacks, upload your `docker-compose.yml` that points to the local context:
   ```yaml
   services:
     plex_ical:
       build:
         context: /volume1/docker/plex_ical
         dockerfile: Dockerfile
       container_name: plex_ical
       env_file:
         - /volume1/docker/plex_ical/.env
       ports:
         - "5181:8000"
       restart: unless-stopped
   ```

---

## Using the Calendar Feed

### Subscribe in Apple Calendar (macOS)
1. Open **Calendar.app**
2. Go to **File → New Calendar Subscription**
3. Enter your Synology URL:
   ```
   http://<synology-ip>:5181/calendar
   ```
4. Click **Subscribe**
5. It will appear as a **separate calendar** named from `CAL_NAME`.

### On iPhone/iPad
- Go to **Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar**  
- Use the same URL:
  ```
  http://<synology-ip>:5181/calendar
  ```

---

## Endpoints
- `/calendar` → The merged iCal feed
- `/health` → JSON health info
- `/` → Basic info (name, cache, etc.)

---

## Example .env
```env
SONARR_ICAL_URL=http://sonarr:8989/calendar?apikey=XXXX
RADARR_ICAL_URL=http://radarr:7878/calendar?apikey=YYYY
CAL_NAME=calendar_Entertainment
REFRESH_SECONDS=1800
VERIFY_SSL=true
TZ=America/Chicago
```

---

## License
GNU General Public License v3.0
