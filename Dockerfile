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


# === STAGE 2: Build the Python Backend & Final Image ===
# We start fresh with a lean Python image for our final product.
FROM python:3.11-slim

# Set the working directory for the backend
WORKDIR /app

# Install Gunicorn, a production-ready web server for Python.
# We don't use the built-in Flask server for production.
RUN pip install gunicorn Flask Flask-SocketIO Flask-Cors

# Copy the built frontend files from the 'builder' stage into a 'static' folder.
# This is the magic of multi-stage builds.
COPY --from=builder /app/frontend/dist /app/static

# Copy the backend source code
COPY backend/ .

# Expose the port the container will run on.
EXPOSE 5001

# The command to run the application using the Gunicorn server.
# It will run 4 worker processes and bind to port 5001, accessible from anywhere inside the container.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "app:app"]