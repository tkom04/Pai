#!/bin/bash
# Personal AI Assistant - Startup Script (Unix/Linux/macOS)
# This script starts both the backend (FastAPI) and frontend (Next.js)

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  Personal AI Assistant - Starting Services   ${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python && ! command_exists python3; then
    echo -e "${RED}ERROR: Python is not installed or not in PATH!${NC}"
    echo -e "${RED}Please install Python 3.9+ and add it to your PATH${NC}"
    exit 1
fi

# Use python3 if available, otherwise python
if command_exists python3; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
else
    PYTHON_CMD=python
    PIP_CMD=pip
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"

SKIP_FRONTEND=0
if ! command_exists node; then
    echo -e "${YELLOW}WARNING: Node.js is not installed or not in PATH!${NC}"
    echo -e "${YELLOW}Frontend will not start. Install Node.js if you want to run the frontend.${NC}"
    SKIP_FRONTEND=1
else
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js found: $NODE_VERSION${NC}"
fi

echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    echo -e "${YELLOW}Creating a template .env file...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Created .env file. Please edit it with your actual credentials.${NC}"
    else
        echo -e "${RED}Could not create .env file. Please create one manually.${NC}"
    fi
    echo ""
fi

# Install Python dependencies if needed
echo -e "${YELLOW}Checking Python dependencies...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}ERROR: requirements.txt not found!${NC}"
    exit 1
fi

# Check if fastapi is installed
if ! $PIP_CMD show fastapi >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    $PYTHON_CMD -m pip install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Python dependencies already installed${NC}"
fi

echo ""

# Install Node dependencies if frontend exists and Node is available
if [ $SKIP_FRONTEND -eq 0 ] && [ -f "frontend copy/package.json" ]; then
    echo -e "${YELLOW}Checking Node.js dependencies...${NC}"
    cd "frontend copy"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing Node.js dependencies (this may take a few minutes)...${NC}"
        npm install
        echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
    else
        echo -e "${GREEN}✓ Node.js dependencies already installed${NC}"
    fi

    cd ..
    echo ""
fi

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"

    # Kill background jobs
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi

    echo ""
    echo -e "${CYAN}All services stopped. Goodbye!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}Starting Backend (FastAPI)...${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload &
BACKEND_PID=$!

echo -e "${GREEN}✓ Backend starting on http://localhost:8080${NC}"
echo -e "${CYAN}  - API Docs: http://localhost:8080/docs${NC}"
echo -e "${CYAN}  - Health Check: http://localhost:8080/healthz${NC}"
echo ""

# Wait a moment for backend to start
sleep 3

# Start frontend if available
if [ $SKIP_FRONTEND -eq 0 ] && [ -f "frontend copy/package.json" ]; then
    echo -e "${CYAN}================================================${NC}"
    echo -e "${CYAN}Starting Frontend (Next.js)...${NC}"
    echo -e "${CYAN}================================================${NC}"
    echo ""

    cd "frontend copy"
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    echo -e "${GREEN}✓ Frontend starting on http://localhost:3000${NC}"
    echo ""
fi

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  All services started successfully!          ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${CYAN}Backend API: http://localhost:8080/docs${NC}"
if [ $SKIP_FRONTEND -eq 0 ] && [ -f "frontend copy/package.json" ]; then
    echo -e "${CYAN}Frontend UI: http://localhost:3000${NC}"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for background jobs
wait
