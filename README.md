# Battleship Online

A full-stack, real-time multiplayer Battleship game built with the PERN stack (Postgres-Express-React-Node) and deployed with Docker and Apache.

**Live Demo:** [https://csatabedearon.info/battleship/](https://csatabedearon.info/battleship/)

---

### Features

*   Real-time gameplay using WebSockets (Flask-SocketIO).
*   Public matchmaking to play against random opponents.
*   Private lobbies with shareable room codes.
*   Interactive game boards built with React.
*   Containerized for easy and consistent deployment.

### Technology Stack

*   **Frontend:** React, Vite, Socket.IO Client
*   **Backend:** Python, Flask, Flask-SocketIO, Gunicorn
*   **Web Server / Proxy:** Apache2
*   **Containerization:** Docker

---

### Running Locally (Development)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```
2.  **Install frontend dependencies:**
    ```bash
    cd frontend
    npm install
    ```
3.  **Install backend dependencies:**
    ```bash
    cd ../backend
    pip install -r requirements.txt
    ```
4.  **Run the backend server:**
    ```bash
    python app.py
    ```
5.  **In a new terminal, run the frontend dev server:**
    ```bash
    cd frontend
    npm run dev
    ```
6.  Open your browser to `http://localhost:5173`.

---

### Deployment to a Subdirectory (Production)

This project is configured to be deployed to a subdirectory (e.g., `https://yourdomain.com/battleship`) using Apache as a reverse proxy.

#### **1. Frontend Build Configuration**

The `frontend/vite.config.js` file must be configured with the correct base path:
```javascript
export default defineConfig({
  base: '/battleship/'
})
```

#### **2. Docker Configuration**

The `Dockerfile` is configured to build the frontend, copy the static assets, install Python dependencies, and run the Gunicorn server with the `eventlet` worker required for Flask-SocketIO.

```dockerfile
# (Relevant CMD section)
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5001", "app:app"]
```

#### **3. Apache Reverse Proxy Configuration**

Add the following to your Apache SSL virtual host configuration file (e.g., `/etc/apache2/sites-available/your-site-ssl.conf`). Ensure `mod_proxy`, `mod_proxy_http`, `mod_proxy_wstunnel`, and `mod_rewrite` are enabled.

```apache
RewriteEngine On

# Redirect .../battleship to .../battleship/ for consistency
RewriteRule ^/battleship$ /battleship/ [R=301,L]

# Proxy all standard HTTP requests for the app
<Location /battleship/>
    ProxyPass http://127.0.0.1:5001/
    ProxyPassReverse http://127.0.0.1:5001/
</Location>

# Handle the WebSocket upgrade specifically
RewriteCond %{HTTP:Upgrade} =websocket [NC]
RewriteCond %{REQUEST_URI} ^/battleship/socket.io [NC]
RewriteRule ^/battleship/socket.io/(.*) ws://127.0.0.1:5001/socket.io/$1 [P,L]

ProxyPassReverse /battleship/socket.io/ ws://127.0.0.1:5001/socket.io/
```

#### **4. Building and Running the Container**

```bash
# Build the image
sudo docker build -t battleship-app .

# Run the container
sudo docker run -d --name battleship-app --restart unless-stopped -p 127.0.0.1:5001:5001 battleship-app
```