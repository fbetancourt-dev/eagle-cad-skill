#!/usr/bin/env bash
# Installer script for EAGLE CAD Agentic Skill
set -e

SKILLS_DIR="${HOME}/.gemini/config/skills"
TARGET_DIR="${SKILLS_DIR}/eagle"

echo "-> Installing EAGLE CAD Agentic Skill into ${TARGET_DIR}..."

mkdir -p "${SKILLS_DIR}"

if [ -d "${TARGET_DIR}" ]; then
    echo "Updating existing installation at ${TARGET_DIR}..."
    rm -rf "${TARGET_DIR}"
fi

git clone https://github.com/fbetancourt-dev/eagle-cad-skill.git "${TARGET_DIR}"

echo "-> EAGLE CAD Agentic Skill installed successfully!"
echo "Location: ${TARGET_DIR}"
