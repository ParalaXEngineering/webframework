#!/bin/bash

# Activer le mode verbeux pour le débogage
set -x

# Paramètres du script
NEW_EXECUTABLE="$1"
ORIGINAL_EXECUTABLE="$2"
LOG_FILE="BTL_log.txt"

# Fonction pour gérer les signaux d'arrêt
cleanup() {
    echo "Script terminé par un signal d'arrêt" >> "$LOG_FILE"
    exit 1
}

# Attraper les signaux d'arrêt
trap cleanup SIGTERM SIGINT

# Journalisation du démarrage
echo "Démarrage du script de mise à jour" >> "$LOG_FILE"
echo "Nouveau exécutable : $NEW_EXECUTABLE" >> "$LOG_FILE"
echo "Exécutable original : $ORIGINAL_EXECUTABLE" >> "$LOG_FILE"

# Vérifier l'existence des fichiers
if [ ! -f "$NEW_EXECUTABLE" ]; then
    echo "Erreur : Le nouveau exécutable $NEW_EXECUTABLE n'existe pas." >> "$LOG_FILE"
    exit 1
fi

if [ ! -f "$ORIGINAL_EXECUTABLE" ]; then
    echo "Erreur : L'exécutable original $ORIGINAL_EXECUTABLE n'existe pas." >> "$LOG_FILE"
    exit 1
fi

# Renommer l'exécutable original pour backup
echo "Renommage de l'exécutable original pour backup" >> "$LOG_FILE"
mv "$ORIGINAL_EXECUTABLE" "${ORIGINAL_EXECUTABLE}.bck"
if [ $? -ne 0 ]; then
    echo "Erreur lors de la mise à jour : Impossible de renommer l'exécutable original." >> "$LOG_FILE"
    exit 1
fi

# Remplacer l'exécutable original par le nouveau
echo "Remplacement de l'exécutable original par le nouveau" >> "$LOG_FILE"
mv "$NEW_EXECUTABLE" "$ORIGINAL_EXECUTABLE"
if [ $? -ne 0 ]; then
    echo "Erreur lors de la mise à jour : Impossible de remplacer l'exécutable original." >> "$LOG_FILE"
    exit 1
else
    echo "Mise à jour réussie." >> "$LOG_FILE"
fi

OLD_PIDS=$(pgrep -f "${ORIGINAL_EXECUTABLE}" | grep -v $$)

# Lancer le nouveau terminal avec le nouvel exécutable
echo "Lancer la nouvelle instance de l'application dans un nouveau terminal" >> "$LOG_FILE"
gnome-terminal -- bash -c "cd $(pwd); ./launch.sh; exec bash" &
NEW_TERMINAL_PID=$!
sleep 1  # Attendre que le nouveau terminal soit lancé

# Tuer l'ancienne instance de l'application
echo "Tuer l'ancienne instance de l'application" >> "$LOG_FILE"

if [ -z "$OLD_PIDS" ];then
    echo "Aucune ancienne instance trouvée." >> "$LOG_FILE"
else
    echo "Anciennes instances trouvées : $OLD_PIDS" >> "$LOG_FILE"
    for PID in $OLD_PIDS; do
        if [ "$PID" != "$$" ] && [ "$PID" != "$NEW_TERMINAL_PID" ]; then
            echo "Killing process $PID" >> "$LOG_FILE"
            kill $PID
            if [ $? -ne 0 ];then
                echo "Erreur lors de l'arrêt de l'ancienne instance de l'application (PID $PID)." >> "$LOG_FILE"
            fi
        fi
    done
fi

# Journalisation de la fin du script
echo "Fin du script de mise à jour" >> "$LOG_FILE"

# Désactiver le mode verbeux
set +x

# Le script se termine ici
exit 0
