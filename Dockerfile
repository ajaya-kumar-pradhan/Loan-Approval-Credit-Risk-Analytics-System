# --- STEP 1: Build the React Frontend ---
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install
# Copy the rest of the frontend code and build
COPY frontend/ ./
RUN npm run build

# --- STEP 2: Setup the Python API ---
FROM python:3.9-slim

# Hugging Face Spaces requires running as a non-root user (uid 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Install Python requirements
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the trained models first
COPY --chown=user models/ ./models/
# Copy the backend code
COPY --chown=user backend/ ./backend/
# Copy the built frontend from Step 1 into a folder the backend can see
COPY --chown=user --from=frontend-build /app/frontend/dist ./frontend/dist

# Hugging Face Spaces expects the app to run on port 7860
EXPOSE 7860

# Start the FastAPI server using uvicorn
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
