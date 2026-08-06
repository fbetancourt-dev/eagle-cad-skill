# Installer script for EAGLE CAD Agentic Skill on Windows (PowerShell)
$ErrorActionPreference = "Stop"

$SkillsDir = "$env:USERPROFILE\.gemini\config\skills"
$TargetDir = "$SkillsDir\eagle"

Write-Host "-> Installing EAGLE CAD Agentic Skill into $TargetDir..."

if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null
}

if (Test-Path $TargetDir) {
    Write-Host "Updating existing installation at $TargetDir..."
    Remove-Item -Recurse -Force $TargetDir
}

git clone https://github.com/fbetancourt-dev/eagle-cad-skill.git $TargetDir

Write-Host "-> EAGLE CAD Agentic Skill installed successfully!"
Write-Host "Location: $TargetDir"
