#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Groovy Training — Project Launcher
# ─────────────────────────────────────────────────────────────────
# Usage:
#   ./start.sh            → Show menu
#   ./start.sh crud       → Start CRUD (port 3001 API + Vite dev)
#   ./start.sh docqa-v1   → Start Doc-Q&A v1 (port 3001 API + React)
#   ./start.sh docqa-v2   → Start RAG Doc-Q&A v2 (port 3001 all-in-one)
#   ./start.sh stop       → Stop all running projects
# ─────────────────────────────────────────────────────────────────

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

case "${1:-menu}" in
  menu)
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     🚀 Groovy Training — Project Launcher   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} CRUD App        ${YELLOW}→${NC} Student Management (React + Express)"
    echo -e "  ${GREEN}2)${NC} Doc-Q&A v1      ${YELLOW}→${NC} PDF Q&A with LLM (React + Express)"
    echo -e "  ${GREEN}3)${NC} RAG Doc-Q&A v2  ${YELLOW}→${NC} RAG-powered PDF Q&A (Cosmic UI)"
    echo ""
    echo -e "  ${GREEN}4)${NC} Stop All        ${YELLOW}→${NC} Kill all running servers"
    echo ""
    echo -n "  Choose (1-4): "
    read choice
    case $choice in
      1) "$0" crud ;;
      2) "$0" docqa-v1 ;;
      3) "$0" docqa-v2 ;;
      4) "$0" stop ;;
      *) echo -e "  ${RED}Invalid choice${NC}" ;;
    esac
    ;;
  
  crud)
    echo -e "\n  ${GREEN}▶ Starting CRUD (server + client)...${NC}"
    echo -e "  ${YELLOW}  API:  http://localhost:3001${NC}"
    echo -e "  ${YELLOW}  App:  http://localhost:5173${NC}\n"
    cd "$(dirname "$0")/week-1 d-5/CRUD"
    npm run dev
    ;;
  
  docqa-v1)
    echo -e "\n  ${GREEN}▶ Starting Doc-Q&A v1 (server + client)...${NC}"
    echo -e "  ${YELLOW}  API:  http://localhost:3001${NC}"
    echo -e "  ${YELLOW}  App:  http://localhost:3000${NC}\n"
    cd "$(dirname "$0")/week-2 d-5/smart-doc-qa"
    npm run dev
    ;;
  
  docqa-v2)
    echo -e "\n  ${GREEN}▶ Starting RAG Doc-Q&A v2...${NC}"
    echo -e "  ${YELLOW}  Open: http://localhost:3001${NC}\n"
    cd "$(dirname "$0")/week-3 d-1/rag-docqa"
    EMBEDDING_PROVIDER=ollama LLM_PROVIDER=ollama node server.js
    ;;
  
  stop)
    echo -e "\n  ${YELLOW}⏹  Stopping all project servers...${NC}"
    # Kill node processes on common ports
    lsof -ti:3000 -ti:3001 -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null
    echo -e "  ${GREEN}✅ Done${NC}\n"
    ;;
  
  *)
    echo -e "  ${RED}Unknown project: $1${NC}"
    echo -e "  Usage: ./start.sh [crud|docqa-v1|docqa-v2|stop]"
    ;;
esac
