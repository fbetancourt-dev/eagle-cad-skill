@echo off
REM Installer script for EAGLE CAD Agentic Skill on Windows Command Prompt
SET SKILLS_DIR=%USERPROFILE%\.gemini\config\skills
SET TARGET_DIR=%SKILLS_DIR%\eagle

echo -> Installing EAGLE CAD Agentic Skill into %TARGET_DIR%...

IF NOT EXIST "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"

IF EXIST "%TARGET_DIR%" (
    echo Updating existing installation at %TARGET_DIR%...
    rmdir /S /Q "%TARGET_DIR%"
)

git clone https://github.com/fbetancourt-dev/eagle-cad-skill.git "%TARGET_DIR%"

echo -> EAGLE CAD Agentic Skill installed successfully!
echo Location: %TARGET_DIR%
