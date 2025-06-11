# === STAGE 1: Build the React Frontend ===
# We use an official Node.js image as a "builder" stage.
FROM node:18-alpine AS builder

# Set the working directory inside the container for the frontend
WORKDIR /app/frontend

# Copy the package.json and package-lock.json first to leverage Docker's layer caching.
# This way, 'npm install' only re-runs if dependencies change.
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY frontend/ .

# Run the production build command. This creates a highly optimized 'dist' folder.
RUN npm run build


# --- STAGE 2: Final Image ---
FROM python:3.11-slim
WORKDIR /app
# ADD eventlet to the list of packages to install
RUN pip install gunicorn Flask Flask-SocketIO Flask-Cors eventlet
# The built frontend is copied here
COPY --from=builder /app/frontend/dist /app/static
COPY backend/ .
EXPOSE 5001
# CHANGE the CMD to use the eventlet worker class.
# It is also recommended to start with 1 worker for eventlet.
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5001", "app:app"]