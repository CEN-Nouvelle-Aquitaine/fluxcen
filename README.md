# FluxCEN
 
Le plugin QGIS FluxCEN permet d'accéder en un clic à un large éventail de flux WFS/WMS organisés par catégories et interrogeables sous forme de mots-clés. Les flux mis à disposition sont issus des données du Conservatoire d'Espaces Naturels de Nouvelle-Aquitaine via son serveur cartographique mais aussi des producteurs nationaux (IGN, BRGM, INPN, SANDRE, GISSOL, GéoPortail, etc.), régionaux ou départementaux

 Ces flux sont centralisés dans le fichier *flux.csv* qui permet de mixer les sources :
  * données en opendata des acteurs publics (IGN, INPN, BRGM, etc.)
  * données avec authentification de flux techniques (données foncières du CEN NA par exemple)
 
 Le dossier *styles_couches* stocke les styles QGIS au format .qml (nommés par le nom technique) afin d'appliquer par défaut ce style à l'ouverture de la couche dans QGIS.
 
  
  ## Composition du fichier .csv
  
  * Service : type de service utilisé (WFS ou WMS)
  * Nom_Clé_Partagée : nom de la couche qui s'affichera dans le plugin
  * Nom_commercial : nom technique qui sert pour l'accès à la couche (caché dans le plugin)
  * URL d'accès : URL pour accéder à la donnée
  * Source : Source de la donnée
