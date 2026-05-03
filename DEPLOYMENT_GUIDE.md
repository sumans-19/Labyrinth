# Labyrinth Forge: Production Deployment Guide

Because Labyrinth Forge runs multiple raw TCP servers (SSH and TCP Honeypots) alongside an HTTP server, it requires a Virtual Private Server (VPS) for the backend.

## Phase 1: Prepare the Frontend for Production

Before uploading your code, you need to tell the frontend where the backend will live.

1. Create a `frontend/.env` file:
   ```env
   VITE_BACKEND_IP=your_future_vps_ip
   ```
2. Open `frontend/src/utils/runtime.js` and modify your URL getters so they use the production IP when not running locally:
   ```javascript
   export function getBackendHttpBase() {
     const ip = import.meta.env.VITE_BACKEND_IP || '127.0.0.1';
     return `http://${ip}:8000`;
   }
   
   export function getBackendWsBase() {
     const ip = import.meta.env.VITE_BACKEND_IP || '127.0.0.1';
     return `ws://${ip}:8000`;
   }
   ```
3. Push all your latest code to a GitHub repository.

---

## Phase 2: Host the Frontend on Vercel

1. Go to [Vercel.com](https://vercel.com) and create a free account.
2. Click **Add New -> Project**.
3. Import your GitHub repository.
4. **Important Configuration:**
   * **Framework Preset:** Vite
   * **Root Directory:** Edit this and select `frontend` (since your React app is inside the frontend folder, not the root).
5. Click **Deploy**. Vercel will give you a live URL in about 30 seconds.

---

## Phase 3: Host the Backend on DigitalOcean

*You can use AWS EC2, Linode, or Google Cloud. DigitalOcean is used here for simplicity.*

1. Go to [DigitalOcean](https://digitalocean.com) and create a Droplet.
   * **Image:** Ubuntu 24.04 LTS
   * **Size:** Basic Shared CPU, Regular Intel ($6/mo is fine)
2. SSH into your new server using the IP they provide:
   ```bash
   ssh root@your_droplet_ip
   ```
3. Install Python and clone your repo:
   ```bash
   apt update
   apt install python3-pip python3-venv git -y
   git clone https://github.com/yourusername/labyrinth-forge.git
   cd labyrinth-forge/backend
   ```
4. Set up the environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Create your `.env` file on the server:
   ```bash
   nano .env
   # Paste your GROQ_API_KEY and GEMINI_API_KEY here, then save.
   ```
6. Open the firewall for your Honeypots and API:
   ```bash
   ufw allow 8000/tcp  # Web API / WebSockets
   ufw allow 8888/tcp  # Raw TCP Honeypot
   ufw allow 2222/tcp  # SSH Honeypot
   ufw enable
   ```

### Running the Backend Permanently

If you just run `python main.py`, it will die when you close your SSH terminal. Use `tmux` to keep it alive:

1. Type `tmux` to open a terminal multiplexer.
2. Ensure your virtual environment is active (`source venv/bin/activate`).
3. Run the backend: `python main.py`
4. Press `Ctrl+b`, then release and press `d` to detach. The server will now run in the background forever.

*(To reattach later, type `tmux attach`)*

---

## Phase 4: Link Them Together

1. Take the public IP of your DigitalOcean Droplet.
2. Go back to your Vercel Dashboard.
3. Go to **Settings -> Environment Variables**.
4. Add `VITE_BACKEND_IP` and paste your Droplet's IP address.
5. Go to the **Deployments** tab and click **Redeploy**.

Your frontend is now publicly hosted on Vercel and talking directly to your raw honeypots on DigitalOcean!
