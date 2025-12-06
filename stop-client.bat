@echo off
REM ScrimGG - Stop Client Only (Batch Launcher)
REM This batch file launches the PowerShell script

powershell.exe -ExecutionPolicy Bypass -File "%~dp0stop-client.ps1"

