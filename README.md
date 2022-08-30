# FluxCEN
 
Le plugin QGIS FluxCEN permet d'accéder en un clic à un large éventail de flux WFS/WMS organisés par catégories et interrogeables sous forme de mots-clés. Les flux mis à disposition sont issus des données du Conservatoire d'Espaces Naturels de Nouvelle-Aquitaine via son serveur cartographique (Geoserver) mais aussi des producteurs nationaux (IGN, BRGM, INPN, SANDRE, GISSOL, GéoPortail, etc.), régionaux ou départementaux.
Il évite ainsi d'avoir à gérer dans QGIS une multitude de connexions et permet aux utilisateurs d'avoir accès facilement à un même endroit à toutes les ressources SIG dont ils ont besoin pour travailler.
Il rend également plus facile la gestion des styles par défaut pour les données vecteur. 

 Ces flux sont centralisés dans le fichier *flux.csv*.
 
## Composition du fichier .csv
  
  * Service : type de service utilisé (WFS ou WMS)
  * categorie : categorie de la couche pour affichage et recherche dans le plugin
  * Nom_couche_plugin : nom de la couche qui s'affichera dans le plugin
  * nom_technique : nom technique de la couche utilisé sur le serveur source (caché dans le plugin)
  * url : URL du serveur pour accéder à la couche
  * source : Source de la donnée
  * style : nom du fichier de style pour affichage à l'ouverture dans QGIS
 
 
## Style des couches
 
 Le dossier *styles_couches* stocke les styles QGIS au format .qml afin d'appliquer par défaut ce style à l'ouverture de la couche dans QGIS. L'ajout d'un style dans ce dossier nécessite de reporter le nom du fichier .qml dans le champ "style" du csv.
 
  

