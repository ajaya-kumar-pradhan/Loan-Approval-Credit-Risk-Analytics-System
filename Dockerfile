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
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the trained models first
COPY models/ ./models/
# Copy the backend code
COPY backend/ ./backend/
# Copy the built frontend from Step 1 into a folder the backend can see
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Hugging Face Spaces expects the app to run on port 7860
EXPOSE 7860

# Start the FastAPI server using uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
