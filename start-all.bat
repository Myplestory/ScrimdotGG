@echo off
REM ScrimGG - Start All Services (Batch Launcher)
REM This batch file launches the PowerShell script

powershell.exe -ExecutionPolicy Bypass -File "%~dp0start-all.ps1"
