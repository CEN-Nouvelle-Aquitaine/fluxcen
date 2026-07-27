# Feature Specification: Support des liens de partage SharePoint et restriction de l'auth Microsoft

**Feature Branch**: `001-sharepoint-share-urls`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "On aimerait permettre le support d'url sharepoint de partage plutôt que des url
graphs que les utilisateurs ne peuvent pas gérer directement. Ainsi c'est l'auth, portée par QGIS qui gère la
création du lien de DL et qui dl le fichier. Par ailleurs, on veut recentrer l'auth microsoft uniquement sur
les url sharepoint ou graph, éviter les fuites de jetons."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurer une ressource avec un lien de partage SharePoint (Priority: P1)

Un administrateur du plugin (agent DSI du CEN) veut héberger une ressource du plugin (le catalogue de flux
`flux.csv`, un style, le changelog…) sur le SharePoint du CEN. Il ouvre SharePoint dans son navigateur,
clique sur « Partager » / « Copier le lien » sur le fichier, et colle ce lien tel quel dans la configuration
du plugin. Au prochain usage, le plugin télécharge le fichier de façon transparente : la résolution du lien
de partage en téléchargement effectif est prise en charge par le plugin, en s'appuyant sur
l'authentification Microsoft déjà configurée dans QGIS. L'administrateur n'a jamais besoin de construire ou
de comprendre une URL technique (Graph).

**Why this priority**: c'est le besoin fonctionnel central. Aujourd'hui, seule une URL Graph construite à la
main fonctionne ; un lien de partage collé naïvement renvoie une page web au lieu du fichier, ce qui rend la
configuration inaccessible aux utilisateurs et casse le plugin en pratique.

**Independent Test**: configurer le catalogue de flux avec un lien de partage SharePoint copié depuis
l'interface web, démarrer le plugin, vérifier que la liste des catégories de flux se remplit correctement.

**Acceptance Scenarios**:

1. **Given** une configuration contenant un lien de partage SharePoint valide vers `flux.csv` et une
   authentification Microsoft opérationnelle dans QGIS, **When** le plugin charge son catalogue, **Then** le
   fichier est téléchargé et les catégories de flux s'affichent, sans aucune manipulation d'URL par
   l'utilisateur.
2. **Given** une configuration contenant une URL Graph existante (format historique), **When** le plugin
   charge son catalogue, **Then** le comportement actuel est préservé (rétrocompatibilité).
3. **Given** un lien de partage collé avec des paramètres superflus ajoutés par SharePoint (paramètres de
   suivi, variantes d'affichage), **When** le plugin le résout, **Then** le téléchargement aboutit malgré ces
   variantes.

---

### User Story 2 - L'auth Microsoft ne sort jamais du périmètre Microsoft (Priority: P1)

Le responsable sécurité du CEN veut la garantie qu'un jeton d'accès Microsoft (Entra ID) n'est jamais
transmis à un service tiers. Actuellement, l'authentification Microsoft configurée est appliquée à tous les
téléchargements de ressources, y compris vers des domaines non Microsoft (hébergement des styles, du
changelog…) : le jeton part vers des serveurs qui n'ont pas à le voir. Après l'évolution, l'authentification
Microsoft n'est appliquée qu'aux requêtes à destination des domaines SharePoint/Microsoft Graph ; toute
autre destination est appelée sans cette authentification.

**Why this priority**: fuite de secret avérée — un jeton donnant accès en lecture aux fichiers SharePoint du
CEN est actuellement envoyé à des tiers. Enjeu de sécurité au même niveau de priorité que le besoin
fonctionnel.

**Independent Test**: avec une configuration mélangeant URL SharePoint et URL non Microsoft, inspecter les
requêtes émises et vérifier que seules celles vers les domaines Microsoft portent l'authentification.

**Acceptance Scenarios**:

1. **Given** une configuration avec une ressource SharePoint et une ressource hébergée hors Microsoft,
   **When** le plugin télécharge les deux, **Then** seule la requête vers SharePoint porte
   l'authentification Microsoft ; l'autre est anonyme.
2. **Given** un catalogue de flux dont une ligne référence un style hébergé hors Microsoft, **When** le
   style est téléchargé, **Then** aucune authentification Microsoft n'accompagne la requête, même si le nom
   du fichier provient du catalogue distant.
3. **Given** une URL de destination non Microsoft déguisée (ex. domaine contenant « sharepoint » en
   sous-chaîne, `sharepoint.com.attacker.tld`), **When** le plugin évalue la destination, **Then** elle est
   traitée comme hors périmètre Microsoft et ne reçoit pas l'authentification.
4. **Given** le chargement d'une couche WMS/WFS du catalogue vers un domaine tiers (IGN, BRGM…), **When**
   la couche est ajoutée au projet, **Then** aucune configuration d'authentification Microsoft ne lui est
   attachée ; seules les couches dont la destination appartient au périmètre Microsoft peuvent porter
   cette authentification.
5. **Given** le chargement d'une couche base de données (PostGIS) alors que la configuration
   d'authentification Microsoft existe dans QGIS (voire est définie comme configuration par défaut du
   plugin), **When** la connexion est établie, **Then** la configuration Microsoft n'est jamais attachée à
   la connexion : seules les configurations d'authentification adaptées aux bases de données
   (identifiant/mot de passe, certificat) sont proposées ou appliquées. *(Amendement 2026-07-27 :
   l'attachement de la configuration Microsoft à une connexion PostGIS échoue systématiquement et
   déclenche une fenêtre d'identification déroutante exposant l'URI de connexion.)*
6. **Given** une couche WFS/WMS du catalogue dont la destination est le service sécurisé du CEN
   (`opendata.cen-nouvelle-aquitaine.org`, ex. couches foncières), **When** la couche est ajoutée au
   projet, **Then** une configuration d'authentification adaptée (non web) lui est attachée — jamais la
   configuration Microsoft. *(Amendement 2026-07-27 : le geoserver CEN est authentifié, confirmé par
   l'utilisateur.)*

---

### User Story 3 - Diagnostic clair en cas d'échec (Priority: P2)

Un utilisateur du plugin dont le lien de partage configuré est invalide, expiré, ou dont le compte n'a pas
accès au fichier, obtient un message d'erreur en français qui distingue la cause (lien invalide, accès
refusé, problème réseau, authentification à configurer) et lui indique quoi faire. Le plugin reste utilisable
pour tout ce qui ne dépend pas de la ressource en échec, et QGIS démarre normalement.

**Why this priority**: le support à distance des postes CEN repose sur des messages exploitables ; un échec
de téléchargement ne doit jamais rendre QGIS ou le plugin inutilisable.

**Independent Test**: configurer successivement un lien invalide, un lien vers un fichier non partagé, et
couper le réseau ; vérifier que chaque cas produit un message distinct et que le plugin se charge quand même.

**Acceptance Scenarios**:

1. **Given** un lien de partage invalide ou expiré, **When** le plugin tente le téléchargement, **Then** un
   message explicite identifie le lien en cause et la nature du problème, sans exposer de jeton ni d'URL
   complète contenant des secrets.
2. **Given** une ressource distante inaccessible (réseau coupé, serveur en panne), **When** QGIS démarre,
   **Then** le plugin se charge, signale l'indisponibilité, et les fonctions ne dépendant pas de cette
   ressource restent utilisables.
3. **Given** aucune authentification Microsoft configurée dans QGIS et un lien SharePoint dans la
   configuration, **When** le téléchargement échoue pour cause d'authentification, **Then** le message
   oriente l'utilisateur vers la configuration de l'authentification.

---

### Edge Cases

- Lien de partage vers un fichier supprimé ou déplacé depuis le partage : erreur « accès impossible »
  distincte d'un problème réseau.
- Lien de partage d'un autre tenant SharePoint que celui du CEN : le téléchargement est tenté avec
  l'authentification (domaine SharePoint légitime), l'échec d'autorisation éventuel est remonté clairement.
- URL non HTTPS dans la configuration : refusée (jamais de jeton sur un canal non chiffré).
- Domaine ressemblant à un domaine Microsoft (`sharepoint.com.evil.tld`, `notsharepoint.com`,
  `graph.microsoft.com.evil.tld`) : hors périmètre, pas d'authentification.
- Ressource volumineuse ou serveur lent : l'interface de QGIS ne doit pas se figer pendant le
  téléchargement au démarrage.
- Lien de partage exigeant une connexion alors que le jeton est expiré : la ré-authentification est portée
  par l'infrastructure QGIS (comportement standard), pas par le plugin.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le plugin DOIT accepter, pour toute ressource distante configurable (catalogue de flux et
  styles — le changelog et l'information de version ont été retirés du plugin par la simplification du
  versionning menée sur `main`, PR #48/#49, intégrée le 2026-07-27), une URL de partage SharePoint telle
  que copiée depuis l'interface web
  (« Copier le lien »), sans transformation manuelle par l'utilisateur. Pour l'emplacement des styles
  (ressource « répertoire »), un lien de partage vers un **dossier** SharePoint est accepté : les fichiers
  de style sont résolus par leur nom à l'intérieur de ce dossier.
- **FR-002**: Le plugin DOIT résoudre automatiquement un lien de partage SharePoint en téléchargement
  effectif du fichier cible, en s'appuyant exclusivement sur l'infrastructure d'authentification de QGIS
  pour porter les identifiants Microsoft.
- **FR-003**: Les URL Microsoft Graph déjà en place DOIVENT continuer de fonctionner à l'identique
  (rétrocompatibilité de la configuration existante).
- **FR-004**: L'authentification Microsoft NE DOIT être appliquée qu'aux requêtes dont la destination
  appartient au périmètre Microsoft : domaines SharePoint (`*.sharepoint.com`) et Microsoft Graph
  (`graph.microsoft.com`). Toute requête vers une autre destination DOIT être émise sans authentification
  Microsoft.
- **FR-005**: L'appartenance au périmètre Microsoft DOIT être évaluée sur le nom d'hôte exact de l'URL
  (correspondance de domaine stricte), résistante aux domaines trompeurs contenant « sharepoint » ou
  « microsoft » en sous-chaîne.
- **FR-006**: Les URL de ressources DOIVENT être en HTTPS : une URL `http:` est rejetée avec un message
  explicite, sans émission de requête. Exception : les URL à contenu embarqué (`data:`), qui n'atteignent
  aucun serveur, restent tolérées et sont toujours traitées sans authentification. Aucune authentification
  n'est jamais appliquée à une URL non HTTPS.
- **FR-007**: Aucun jeton, aucune URL complète susceptible de contenir un secret, NE DOIT apparaître dans
  les messages d'erreur ni dans les journaux.
- **FR-008**: Un échec de téléchargement d'une ressource distante (lien invalide, accès refusé, réseau
  indisponible) NE DOIT PAS empêcher le chargement du plugin ni le démarrage de QGIS ; l'erreur est
  signalée à l'utilisateur avec sa cause (lien invalide / accès refusé / réseau / authentification à
  configurer) et les fonctions indépendantes restent disponibles.
- **FR-009**: Le téléchargement des ressources au démarrage NE DOIT PAS figer l'interface de QGIS.
- **FR-010**: La restriction du périmètre Microsoft s'applique aussi aux couches ajoutées au projet
  (WMS/WFS) : une configuration d'authentification Microsoft NE DOIT être attachée à une couche que si sa
  destination appartient au périmètre Microsoft ; l'attachement indiscriminé de la première configuration
  d'authentification disponible à toute couche est supprimé.
- **FR-011** *(amendement 2026-07-27)*: Une configuration d'authentification de type web (OAuth2, dont
  Microsoft Entra ID) NE DOIT jamais être appliquée à une connexion base de données (PostGIS). Le choix
  d'une authentification pour une connexion base de données (sélection automatique, dialogue de choix,
  configuration par défaut mémorisée) NE DOIT proposer ou appliquer que des méthodes adaptées aux bases de
  données ; une configuration par défaut mémorisée devenue inadaptée est ignorée avec un message journalisé.
- **FR-012** *(amendement 2026-07-27, revue de code)*: Les couches du catalogue dont la destination est le
  service cartographique sécurisé du CEN (`opendata.cen-nouvelle-aquitaine.org`) DOIVENT recevoir une
  configuration d'authentification adaptée (méthode non web : identifiant/mot de passe ou certificat),
  choisie par le même mécanisme filtré que pour PostGIS (FR-011). Les couches vers toute autre destination
  restent sans authentification (FR-010) ; la configuration Microsoft n'est jamais candidate.

### Key Entities

- **Ressource distante configurée** : fichier nécessaire au plugin (catalogue de flux, style de couche,
  changelog, information de version), identifié par une URL dans la configuration ; peut être hébergé sur
  SharePoint (avec authentification) ou ailleurs (sans authentification Microsoft).
- **Lien de partage SharePoint** : URL produite par la fonction « Partager » de SharePoint, manipulable par
  un utilisateur non technique ; pointe vers un fichier mais n'est pas directement un lien de
  téléchargement.
- **Périmètre d'authentification Microsoft** : ensemble des destinations autorisées à recevoir
  l'authentification Microsoft (domaines SharePoint et Microsoft Graph), évalué à chaque requête.
- **Configuration d'authentification** : référence (identifiant opaque) vers les identifiants Microsoft
  stockés de façon chiffrée par QGIS ; le plugin ne manipule jamais les secrets eux-mêmes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un administrateur non technique configure une ressource en copiant-collant un lien de partage
  SharePoint, sans documentation technique ni assistance, en moins de 2 minutes.
- **SC-002**: 100 % des requêtes émises par le plugin portant l'authentification Microsoft ont pour
  destination un domaine du périmètre Microsoft (vérifiable par inspection des requêtes en test).
- **SC-003**: Aucun jeton ni secret n'apparaît dans les journaux ou messages du plugin, quel que soit le
  scénario d'erreur provoqué.
- **SC-004**: QGIS démarre et le plugin se charge dans 100 % des scénarios d'indisponibilité des ressources
  distantes testés (lien invalide, accès refusé, réseau coupé).
- **SC-005**: Les configurations existantes (URL Graph, ressources hors Microsoft) fonctionnent sans aucune
  modification après mise à jour du plugin.
- **SC-006**: Chaque famille d'échec (lien invalide, accès refusé, réseau, authentification manquante)
  produit un message distinct et actionnable en français.

## Assumptions

- Les liens de partage concernés proviennent du tenant SharePoint du CEN Nouvelle-Aquitaine ; les liens
  d'autres tenants sont traités comme SharePoint (authentification appliquée) mais leur succès dépend des
  droits du compte.
- L'authentification Microsoft existante (OAuth2 Entra ID configurée dans QGIS) reste le mécanisme
  d'authentification ; cette évolution n'introduit aucun nouveau mode d'authentification.
- Les utilisateurs finaux disposent d'un compte Microsoft du CEN avec droit de lecture sur les fichiers
  partagés ; la gestion des droits se fait côté SharePoint, hors périmètre du plugin.
- Les ressources hébergées hors Microsoft (styles, changelog aujourd'hui sur un hébergement public)
  restent accessibles sans authentification ; leur migration éventuelle vers SharePoint est une décision de
  configuration, pas une exigence de cette évolution.
- La résolution d'un lien de partage en téléchargement s'appuie sur les capacités standard de la plateforme
  Microsoft ; aucun service intermédiaire n'est introduit.
