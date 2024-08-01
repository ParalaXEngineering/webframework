@echo off
setlocal

:: Use command-line arguments for file paths
set "path_to_new_executable=%~1"
set "original_executable_path=%~2"
set "log_file=BTL_log.txt"

:: Renommer l'exécutable original pour backup
move "%original_executable_path%" "%original_executable_path%.bck"

:: Vérifier si le renommage a réussi
if %ERRORLEVEL% neq 0 (
    echo Erreur lors de la mise à jour : Impossible de renommer l'exécutable original. >> "%log_file%"
    exit /b 1
)

:: Remplacer l'exécutable original par le nouveau
move /Y "%path_to_new_executable%" "%original_executable_path%"

:: Vérifier si le remplacement a réussi
if %ERRORLEVEL% neq 0 (
    echo Erreur lors de la mise à jour : Impossible de remplacer l'exécutable original. >> "%log_file%"
    exit /b 1
) else (
    echo Mise à jour réussie. >> "%log_file%"
)

:: Tuer l'ancienne instance de l'application
taskkill /IM "%original_executable_path%" /F

:: Attendre un peu pour s'assurer que l'application est bien fermée
timeout /t 5

:: Lancer la nouvelle instance de l'application
start "" "%original_executable_path%"

:: Le script se termine ici
endlocal
