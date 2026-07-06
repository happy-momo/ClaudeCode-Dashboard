#!/usr/bin/env bash
# =============================================================================
# Claude Dashboard - Installation Script
# =============================================================================
#
# This script prepares the Claude Dashboard plugin environment:
# 1. Validates prerequisites (Python 3.11+, Node.js 18+)
# 2. Installs backend Python dependencies
# 3. Installs frontend npm dependencies
# 4. Builds the frontend for production
#
# After running this script, manually register the plugin with Claude Code.
#
# Usage:
#   bash scripts/install.sh
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

die() {
    log_error "$1"
    exit 1
}

# =============================================================================
# Prerequisites Check
# =============================================================================

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Python 3.11+
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' || echo "0.0")
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            PYTHON_CMD="python3"
        else
            die "Python 3.11+ is required. Found: $PYTHON_VERSION"
        fi
    else
        die "Python 3.11+ is required but not found."
    fi

    log_info "Python: $($PYTHON_CMD --version)"

    # Check Node.js 18+
    if ! command -v node &> /dev/null; then
        die "Node.js 18+ is required but not found."
    fi

    NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        die "Node.js 18+ is required. Found: v$NODE_VERSION"
    fi

    log_info "Node.js: $(node --version)"

    # Check npm
    if ! command -v npm &> /dev/null; then
        die "npm is required but not found."
    fi

    log_info "npm: $(npm --version)"

    log_success "Prerequisites check passed."
}

# =============================================================================
# Install Backend Dependencies
# =============================================================================

install_backend() {
    log_info "Installing backend dependencies..."

    BACKEND_DIR="$PROJECT_ROOT/backend"
    REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        die "requirements.txt not found at $REQUIREMENTS_FILE"
    fi

    # Create virtual environment if it doesn't exist
    VENV_DIR="$BACKEND_DIR/venv"
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating Python virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    # Activate virtual environment and install dependencies
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$REQUIREMENTS_FILE"

    log_success "Backend dependencies installed."
}

# =============================================================================
# Install Frontend Dependencies and Build
# =============================================================================

install_frontend() {
    log_info "Installing frontend dependencies..."

    FRONTEND_DIR="$PROJECT_ROOT/frontend"

    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        die "package.json not found at $FRONTEND_DIR/package.json"
    fi

    cd "$FRONTEND_DIR"

    # Install npm dependencies
    npm install --legacy-peer-deps

    log_success "Frontend dependencies installed."
}

build_frontend() {
    log_info "Building frontend for production..."

    FRONTEND_DIR="$PROJECT_ROOT/frontend"
    cd "$FRONTEND_DIR"

    # Build frontend - output goes to backend/static/
    npm run build

    # Verify build output
    if [ ! -f "$PROJECT_ROOT/backend/static/index.html" ]; then
        die "Frontend build failed - index.html not found"
    fi

    log_success "Frontend built successfully."
}

# =============================================================================
# Main Installation Flow
# =============================================================================

main() {
    echo ""
    echo "=============================================="
    echo "  Claude Dashboard - Installation Script"
    echo "=============================================="
    echo ""

    cd "$PROJECT_ROOT"

    check_prerequisites
    install_backend
    install_frontend
    build_frontend

    echo ""
    echo "=============================================="
    echo "  Environment Setup Complete!"
    echo "=============================================="
    echo ""
    echo "Next steps - Manual Plugin Installation:"
    echo ""
    echo "  1. Add the plugin to your Claude Code settings:"
    echo ""
    echo "     Edit ~/.claude/settings.json and add:"
    echo ""
    echo "     {"
    echo "       \"extraKnownMarketplaces\": {"
    echo "         \"claude-dashboard-local\": {"
    echo "           \"source\": {"
    echo "             \"source\": \"directory\","
    echo "             \"path\": \"$PROJECT_ROOT/.claude-plugin\""
    echo "           }"
    echo "         }"
    echo "       }"
    echo "     }"
    echo ""
    echo "  2. Update marketplaces and install:"
    echo "     claude plugin marketplace update"
    echo "     claude plugin install claude-dashboard-local"
    echo ""
    echo "  3. Start Claude Code:"
    echo "     claude"
    echo ""
    echo "  For development:"
    echo "    - Backend:  cd backend && source venv/bin/activate && python main.py"
    echo "    - Frontend: cd frontend && npm run dev"
    echo ""
}

# Run main function
main "$@"
