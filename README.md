# <p align="center">FluxCEN</p>

<img align="left" src=https://raw.githubusercontent.com/CEN-Nouvelle-Aquitaine/fluxcen/main/icons/icon.png  width="220"/>
<br>
<br>
<br>
Le plugin QGIS FluxCEN permet d'accéder rapidement à un large éventail de flux WFS/WMS organisés par catégories et interrogeables sous forme de mots-clés. 
<br>
<br>
Il rend également possible l'édition de "couches SIG collaboratives" grâce à la prise en charge de l'édition de tables du SGBD PostgreSQL/PostGIS.
<br>
<br>
<br>
Il évite ainsi d'avoir à gérer dans QGIS une multitude de connexions et simplifie grandement l'accès aux données dans un système d'information.
<br>


<br>

## 🧐 Features

- Sélection rapide des ressources par autocomplétion
- Regroupement des flux au sein de catégories
- Gestion des styles par défaut à l'ouverture dans QGIS pour les données WFS
- Centralisation  et gestion des flux simplifiée dans un fichier .csv
- Prise en charge des flux Geoserver et Mapserver
- Lien direct vers la fiche de métadonnées de la ressource
- Fonction d'édition : accès à des tables PostgreSQL/PostGIS pour l'édition collaborative avec gestion du formulaire de saisie
- Code et ressources attachées gérées directement via le git

## Composition du fichier .csv
  
  * service : type de service utilisé (WFS ou WMS)
  * categorie : categorie de la couche pour affichage et recherche dans le plugin
  * Nom_couche_plugin : nom de la couche qui s'affichera dans le plugin
  * nom_technique : nom technique de la couche utilisé sur le serveur source (caché dans le plugin)
  * url : URL du serveur pour accéder à la couche
  * source : Source de la donnée
  * style : nom du fichier de style pour affichage à l'ouverture dans QGIS
  * metadonnees : URL d'accès à la fiche de métadonnées liée à la resource
 
 Exemple pour accéder à la BD ORTHO® :
 
 | service | categorie | Nom_couche_plugin | nom_technique | url | source | style |
| -------- | -------- | -------- | -------- | -------- |-------- | -------- |
| WMS Raster| Fonds cartos | BD ORTHO® | HR.ORTHOIMAGERY.ORTHOPHOTOS |https://wxs.ign.fr/ortho/geoportail/r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities| IGN  | |

 
 
## Style des couches
 
 Le dossier *styles_couches* stocke les styles QGIS au format .qml afin d'appliquer par défaut ce style à l'ouverture de la couche dans QGIS. L'ajout d'un style dans ce dossier nécessite de reporter le nom du fichier .qml dans le champ "style" du csv.
 
  
## Accès aux données protégées

Si l'accès à la majorité des ressources reste public, certaines peuvent être protégées par un mot de passe (données métier confidentielles par exemple).

 Cette authentification est gérée via le serveur cartographique qui génère les flux.
Pour y accéder, il faut créer en amont une authentification dans QGIS. L'ouverture des données protégées se fera alors à partir de la première authentification enregistrée dans QGIS (pas de gestion multi-authentification pour le moment)

## Interface du plugin:

<img align="center" src=https://raw.githubusercontent.com/CEN-Nouvelle-Aquitaine/fluxcen/main/icons/fluxcen_interface.PNG  width="600"/>



