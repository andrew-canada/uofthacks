#!/bin/bash

# Pipeline Automation Script
# Runs the complete trend analysis pipeline with proper environment setup

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Gen Z Trend Analysis Pipeline - Automated Run       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to pipeline directory
cd "$SCRIPT_DIR"
echo -e "${BLUE}📂 Working directory: $SCRIPT_DIR${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found at $PROJECT_ROOT/venv${NC}"
    echo -e "${YELLOW}   Creating virtual environment...${NC}"
    python3 -m venv "$PROJECT_ROOT/venv"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source "$PROJECT_ROOT/venv/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Check if required packages are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python3 -c "import pymongo, google.genai" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing missing dependencies...${NC}"
    pip install -q pymongo google-generativeai
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ All dependencies present${NC}"
fi
echo ""

# Check if config file exists
if [ ! -f "video_analysis/config.py" ]; then
    echo -e "${RED}❌ Configuration file not found!${NC}"
    echo -e "${YELLOW}   Please copy config.example.py to config.py and add your API keys:${NC}"
    echo -e "   ${BLUE}cp video_analysis/config.example.py video_analysis/config.py${NC}"
    exit 1
fi

# Check if shop_export.json exists
if [ ! -f "shop_export.json" ]; then
    echo -e "${YELLOW}⚠️  shop_export.json not found${NC}"
    echo -e "${YELLOW}   Run extraction.py first or use sample data${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration files verified${NC}"
echo ""

# Clean up old generated files (optional)
if [ "$1" == "--clean" ]; then
    echo -e "${BLUE}🧹 Cleaning previous run files...${NC}"
    rm -f twelve_labs_analysis.json gemini_recommendations.json *.log
    echo -e "${GREEN}✓ Cleaned${NC}"
    echo ""
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate timestamp for log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/pipeline_run_${TIMESTAMP}.log"

echo -e "${BLUE}📝 Logging to: $LOG_FILE${NC}"
echo ""

# Run the pipeline with output to both console and log file
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   Starting Pipeline                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

python3 pipeline.py 2>&1 | tee "$LOG_FILE"

# Check exit status
PIPELINE_EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  Pipeline Completed! ✓                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}✓ Twelve Labs analysis saved${NC}"
    echo -e "${GREEN}✓ Gemini recommendations generated${NC}"
    echo -e "${GREEN}✓ MongoDB updated with new trends${NC}"
    echo ""
    echo -e "${BLUE}📄 Generated Files:${NC}"
    if [ -f "twelve_labs_analysis.json" ]; then
        SIZE=$(ls -lh twelve_labs_analysis.json | awk '{print $5}')
        echo -e "   - twelve_labs_analysis.json (${SIZE})"
    fi
    if [ -f "gemini_recommendations.json" ]; then
        SIZE=$(ls -lh gemini_recommendations.json | awk '{print $5}')
        echo -e "   - gemini_recommendations.json (${SIZE})"
    fi
    echo -e "   - ${LOG_FILE}"
    echo ""

    # Show trend count from MongoDB
    echo -e "${BLUE}📊 MongoDB Status:${NC}"
    python3 -c "
from pymongo import MongoClient
from video_analysis.config import MONGODB_CONNECTION_STRING
client = MongoClient(MONGODB_CONNECTION_STRING)
db = client['thewinningteam']
count = db['trends'].count_documents({})
print(f'   Total trends in database: {count}')
recent = list(db['trends'].find().sort('created_at', -1).limit(1))
if recent:
    print(f'   Last updated: {recent[0][\"created_at\"].strftime(\"%Y-%m-%d %H:%M:%S\")}')
" 2>/dev/null || echo -e "${YELLOW}   Could not connect to MongoDB${NC}"

    echo ""
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                   Pipeline Failed! ✗                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${RED}❌ Pipeline exited with error code: $PIPELINE_EXIT_CODE${NC}"
    echo -e "${YELLOW}   Check the log file for details: $LOG_FILE${NC}"
    echo ""
    exit $PIPELINE_EXIT_CODE
fi
