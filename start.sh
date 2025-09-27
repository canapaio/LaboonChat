#!/bin/bash
# LaboonChat Unix Launcher
# ========================
# 🐋 Faithful connections across digital oceans 🌊

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "    🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊"
echo "    🌊                                            🌊"
echo "    🌊        🐋 LaboonChat 🐋                   🌊"
echo "    🌊                                            🌊"
echo "    🌊    \"Faithful connections across           🌊"
echo "    🌊         digital oceans\"                   🌊"
echo "    🌊                                            🌊"
echo "    🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊🌊"
echo -e "${NC}"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python non trovato! Installa Python 3.9+ dal tuo package manager${NC}"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo -e "${RED}❌ Python $PYTHON_VERSION trovato, ma serve Python 3.9+${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION trovato${NC}"

# Check if LaboonChat is installed
if ! $PYTHON_CMD -c "import laboon_chat" &> /dev/null; then
    echo -e "${YELLOW}📦 Installazione LaboonChat in corso...${NC}"
    
    # Try pip3 first, then pip
    if command -v pip3 &> /dev/null; then
        pip3 install -e .
    elif command -v pip &> /dev/null; then
        pip install -e .
    else
        echo -e "${RED}❌ pip non trovato! Installa pip per Python${NC}"
        exit 1
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Errore durante l'installazione!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ LaboonChat installato con successo${NC}"
fi

echo -e "${GREEN}🚀 Avvio LaboonChat...${NC}"
echo

# Start LaboonChat
$PYTHON_CMD -m laboon_chat.launcher.laboon_launcher

# Check exit code
if [ $? -ne 0 ]; then
    echo
    echo -e "${RED}❌ LaboonChat si è chiuso con errori${NC}"
    exit 1
fi