# Production
## Mise a jour du software PPU
1. Verifier que les deux icones (PPU et HMI) sont vertes. Si ce n'est pas le cas, il faut verifier la connexion de la fibre.
2. Verifier que l'icone en haut a droite est bien "PPU" sinon cliquer dessus pour obtenir "PPU"
3. Aller dans le menu "Commissioning"
4. Choisir le fichier "**cross-dfnet-os-al700-ppu-2.0.7-os-only-update.fnh**" et cliquer sur "Full update"
5. Attendre environ 10 minutes sans toucher a la station jusqu'a ce que l'icone PPU passe du rouge au vert
6. Choisir ensuite le fichier "cross-dfnet-os-al700-ppu-2.0.7-update.fnh" et cliquer sur "Full update"
7. Attendre 20 minutes sans toucher a la station jusqu'a ce que l'icone PPU passe du rouge au vert
8. Le PPU est a jour

## Mise a jour du software HMI Server
1. Verifier que les deux icones (PPU et HMI) sont vertes. Si ce n'est pas le cas, il faut verifier la connexion de la fibre.
2. Verifier que l'icone en haut a droite est bien "HMI" sinon cliquer dessus pour obtenir "HMI"
3. Aller dans le menu "Commissioning"
4. Choisir le fichier "**cross-dfnet-os-al700-hmi-2.0.7-os-only-update.fnh**" et cliquer sur "Full update"
5. Attendre environ 10 minutes sans toucher au HMI jusqu'a ce que l'icone PPU passe du rouge au vert
6. Choisir ensuite le fichier "cross-dfnet-os-al700-hmi-2.0.7-update.fnh" et cliquer sur "Full update"
7. Attendre 20 minutes sans toucher au HMI jusqu'a ce que l'icone HMI passe du rouge au vert
8. Le HMI Server est a jour

## Insertion du Stanag ID sur le PPU
1. Verifier que les deux icones (PPU et HMI) sont vertes. Si ce n'est pas le cas, il faut verifier la connexion de la fibre.
2. Verifier que l'icone en haut au a droite est bien "PPU" sinon cliquer dessus pour obtenir "PPU"
3. Aller dans le menu "Status" puis dans "Software" et lire la valeur du Stanag ID
4. Si le Stanag ID est a 0xffffffff, continuer la procedure sinon tout est en ordre
5. Aller dans le menu "Programmation" puis dans "Software"
6. Memoriser le S/N ecrit sur la plaquette du boitier du PPU
7. Entre ce S/N dans la section STANAG ID
8. Cliquer sur "Start"
9. Le Stanag ID est ok

## Insertion du Stanag ID sur le HMI Server
1. Verifier que les deux icones (PPU et HMI) sont vertes. Si ce n'est pas le cas, il faut verifier la connexion de la fibre.
2. Verifier que l'icone en haut au a droite est bien "HMI" sinon cliquer dessus pour obtenir "HMI"
3. Aller dans le menu "Status" puis dans "Software" et lire la valeur du Stanag ID
4. Si le Stanag ID est a 0xffffffff, continuer la procedure sinon tout est en ordre
5. Aller dans le menu "Programmation" puis dans "Software"
6. Memoriser le S/N ecrit sur la plaquette du boitier du HMI Server
7. Entre ce S/N dans la section STANAG ID
8. Cliquer sur "Start"
9. Le Stanag ID est ok

## Insertion de la position PARK de la station
1. Verifier que les deux icones (PPU et HMI) sont vertes. Si ce n'est pas le cas, il faut verifier la connexion de la fibre.
2. Verifier que l'icone en haut au a droite est bien "PPU" sinon cliquer dessus pour obtenir "PPU"
3. Aller dans le menu "Low level tools" puis dans "LRU Tools"
4. Chercher la section "PARK position"
5. Cliquer sur "Start"
6. Le systeme redemarre et la rosace doit être en zero/zero
