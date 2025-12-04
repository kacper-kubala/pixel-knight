#!/bin/bash
#
# Pixel Knight - Startup Script
# AI Chat Interface with Search and RAG
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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies from requirements.txt
if [ -f "requirements.txt" ]; then
    # Check if requirements have changed
    REQUIREMENTS_HASH=$(md5 -q requirements.txt 2>/dev/null || md5sum requirements.txt | cut -d' ' -f1)
    INSTALLED_HASH=""
    if [ -f "venv/.requirements_hash" ]; then
        INSTALLED_HASH=$(cat venv/.requirements_hash)
    fi
    
    if [ "$REQUIREMENTS_HASH" != "$INSTALLED_HASH" ]; then
        echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
        pip install --quiet -r requirements.txt
        echo "$REQUIREMENTS_HASH" > venv/.requirements_hash
        echo -e "${GREEN}Dependencies installed!${NC}"
    else
        echo -e "${GREEN}Dependencies up to date.${NC}"
    fi
fi

# Create data directories if needed
mkdir -p data/sessions data/chroma

# Start the server
echo -e "${GREEN}Starting Pixel Knight server...${NC}"
echo ""
python run.py

