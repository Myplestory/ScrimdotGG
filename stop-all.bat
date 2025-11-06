@echo off
REM ScrimGG - Stop All Services (Batch Launcher)

powershell.exe -ExecutionPolicy Bypass -File "%~dp0stop-all.ps1"
