#!/bin/bash
#
# Pixel Knight - Startup Script
# AI Chat Interface with Search and RAG
# Works on macOS, Linux, and Windows (Git Bash)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                     PIXEL KNIGHT                         ║"
echo "║              AI Chat Interface with RAG                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Detect Python command (python3 on Unix, python on Windows)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}Using Python: $PYTHON_CMD${NC}"

# Detect OS for venv paths
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash, Cygwin, etc.)
    VENV_ACTIVATE="venv/Scripts/activate"
    VENV_PYTHON="venv/Scripts/python"
    VENV_PIP="venv/Scripts/pip"
else
    # macOS / Linux
    VENV_ACTIVATE="venv/bin/activate"
    VENV_PYTHON="venv/bin/python"
    VENV_PIP="venv/bin/pip"
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        echo -e "${YELLOW}Try: $PYTHON_CMD -m pip install --user virtualenv${NC}"
        exit 1
    fi
fi

# Verify venv was created properly
if [ ! -f "$VENV_PYTHON" ] && [ ! -f "${VENV_PYTHON}.exe" ]; then
    echo -e "${RED}Virtual environment not created properly${NC}"
    echo -e "${YELLOW}Removing and recreating...${NC}"
    rm -rf venv
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
if [ -f "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE"
else
    echo -e "${YELLOW}Note: Using venv Python directly${NC}"
fi

# Install/update dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    # Check if requirements have changed (cross-platform hash)
    if command -v md5sum &> /dev/null; then
        REQUIREMENTS_HASH=$(md5sum requirements.txt | cut -d' ' -f1)
    elif command -v md5 &> /dev/null; then
        REQUIREMENTS_HASH=$(md5 -q requirements.txt)
    else
        REQUIREMENTS_HASH="unknown"
    fi
    
    INSTALLED_HASH=""
    if [ -f "venv/.requirements_hash" ]; then
        INSTALLED_HASH=$(cat venv/.requirements_hash)
    fi
    
    if [ "$REQUIREMENTS_HASH" != "$INSTALLED_HASH" ]; then
        echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
        "$VENV_PIP" install --quiet -r requirements.txt 2>/dev/null || \
        "$VENV_PIP" install -r requirements.txt
        echo "$REQUIREMENTS_HASH" > venv/.requirements_hash
        echo -e "${GREEN}Dependencies installed!${NC}"
    else
        echo -e "${GREEN}Dependencies up to date.${NC}"
    fi
fi

# Create data directories if needed
mkdir -p data/sessions data/chroma data/uploads data/images

# Start the server
echo -e "${GREEN}Starting Pixel Knight server...${NC}"
echo ""
"$VENV_PYTHON" run.py
