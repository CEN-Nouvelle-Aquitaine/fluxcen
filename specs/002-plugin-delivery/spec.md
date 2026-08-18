# Feature Specification: Système de delivery privé du plugin FluxCEN

**Feature Branch**: `002-plugin-delivery`

**Created**: 2026-08-18

**Status**: Draft

**Input**: User description: "Rédige la spec du système de delivery complet, en mode IAC. Inclu le script python Intune, la création du projet Azure etc (on a Azure mais jamais exploité hors de Entra ID). On POC la function"

## Contexte

FluxCEN est aujourd'hui livré par une URL publique (`https://sig.dsi-cen.org/qgis/`). Le dépôt GitHub va passer en privé. La cible : une livraison réservée aux identités Microsoft du CEN, avec deux canaux (interne et beta), sans manipulation complexe côté utilisateur. Les postes sont gérés par Intune. L'organisation dispose d'Azure mais ne l'a jamais exploité au-delà d'Entra ID : la création du socle Azure fait partie du périmètre. Toute l'infrastructure est décrite en IaC. Un POC valide d'abord le service de distribution (la « function ») de bout en bout.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mise à jour du plugin avec son compte Microsoft (Priority: P1)

Un agent du CEN ouvre QGIS. Le gestionnaire d'extensions lui signale une mise à jour de FluxCEN. Il clique sur « Mettre à jour ». Le téléchargement s'authentifie avec son compte Microsoft CEN déjà configuré dans QGIS. Il ne saisit aucun identifiant supplémentaire et ne touche à aucun réglage.

**Why this priority**: C'est la valeur cœur du système. Sans ce parcours, la livraison privée n'existe pas.

**Independent Test**: Sur un poste avec la config d'auth en place, ajouter le dépôt interne dans QGIS, constater la détection d'une nouvelle version et réussir l'installation en un clic.

**Acceptance Scenarios**:

1. **Given** un poste avec la config d'auth Microsoft valide et le dépôt interne enregistré, **When** une nouvelle version stable est publiée, **Then** QGIS signale la mise à jour et l'installation aboutit sans saisie d'identifiants.
2. **Given** un jeton d'accès expiré mais un jeton de rafraîchissement valide, **When** l'utilisateur installe la mise à jour, **Then** le renouvellement est silencieux et l'installation aboutit.
3. **Given** une personne extérieure au tenant CEN, **When** elle tente d'accéder à l'URL du dépôt ou d'un artefact, **Then** l'accès est refusé.

---

### User Story 2 - Publication automatique par les mainteneurs (Priority: P2)

Un mainteneur pose un tag de version sur le dépôt GitHub privé. Le pipeline construit l'artefact, met à jour le catalogue du bon canal et publie. Une version de préversion part sur le canal beta, une version finale sur le canal interne. Aucune étape manuelle après le tag.

**Why this priority**: Sans publication automatisée, chaque release exige des manipulations manuelles et le système n'est pas fiable dans la durée.

**Independent Test**: Poser un tag de préversion et un tag final sur un commit de test, vérifier que chaque canal reçoit la bonne version.

**Acceptance Scenarios**:

1. **Given** le dépôt GitHub privé, **When** un mainteneur pose un tag de version finale, **Then** le canal interne expose cette version en moins de 10 minutes.
2. **Given** le même dépôt, **When** un mainteneur pose un tag de préversion, **Then** seule la beta est mise à jour et le canal interne reste inchangé.
3. **Given** le pipeline de publication, **When** il s'authentifie auprès du cloud, **Then** il n'utilise aucun secret stocké de longue durée.

---

### User Story 3 - Accès beta restreint à un groupe (Priority: P2)

Une beta-testeuse, membre du groupe beta, dispose du dépôt beta dans son QGIS. Elle reçoit les préversions avant tout le monde. Un agent hors du groupe ne peut ni lister ni télécharger les préversions, même s'il connaît l'URL du dépôt beta.

**Why this priority**: La distinction interne/beta est une exigence du produit. Elle repose sur un contrôle d'accès, pas sur de la discrétion.

**Independent Test**: Avec deux comptes (membre et non-membre du groupe beta), interroger le dépôt beta et comparer les réponses.

**Acceptance Scenarios**:

1. **Given** un compte membre du groupe beta, **When** QGIS interroge le dépôt beta, **Then** la préversion apparaît et s'installe.
2. **Given** un compte hors du groupe beta, **When** il interroge le dépôt beta, **Then** l'accès est refusé.
3. **Given** une version finale plus récente que la préversion, **When** un membre beta consulte son dépôt, **Then** la version finale lui est proposée.

---

### User Story 4 - Provisioning des postes sans manipulation (Priority: P3)

L'administrateur du parc déploie via Intune un script de provisioning. Au premier lancement de QGIS, le poste dispose de la configuration d'authentification Microsoft et des dépôts de plugins adaptés au profil de l'utilisateur. L'utilisateur n'ouvre jamais les réglages d'authentification.

**Why this priority**: Le provisioning industrialise l'embarquement. Les premiers utilisateurs peuvent être configurés à la main pendant le POC.

**Independent Test**: Exécuter le script sur un poste vierge, ouvrir QGIS et constater que le dépôt est présent et fonctionnel.

**Acceptance Scenarios**:

1. **Given** un poste vierge géré par Intune, **When** le script de provisioning s'exécute, **Then** QGIS dispose de la config d'auth et du dépôt interne au premier lancement.
2. **Given** un poste où le port local de retour d'authentification est occupé par un autre logiciel, **When** le script s'exécute, **Then** il détecte le conflit et bascule sur un port libre.
3. **Given** un poste déjà provisionné, **When** le script se ré-exécute, **Then** il ne casse rien et corrige les écarts éventuels.

---

### User Story 5 - Infrastructure reproductible (Priority: P3)

Un opérateur recrée l'ensemble de l'infrastructure de distribution depuis zéro à partir du code d'infrastructure versionné : socle Azure, service de distribution, stockage, droits d'accès. Aucune configuration manuelle au portail hormis les prérequis documentés.

**Why this priority**: L'organisation n'a jamais exploité Azure au-delà d'Entra ID. Sans IaC, l'infrastructure reposerait sur des clics au portail impossibles à auditer ou à refaire.

**Independent Test**: Détruire l'environnement de POC et le recréer uniquement depuis le code versionné, puis rejouer le scénario P1.

**Acceptance Scenarios**:

1. **Given** une souscription Azure vide et les prérequis documentés, **When** l'opérateur applique le code d'infrastructure, **Then** le système de distribution est opérationnel sans action manuelle au portail.
2. **Given** une dérive de configuration manuelle, **When** le code d'infrastructure est réappliqué, **Then** la configuration revient à l'état décrit.

---

### Edge Cases

- Jeton de rafraîchissement expiré ou révoqué : QGIS doit relancer une authentification interactive. Ce cas ne doit jamais se déclencher pendant la vérification des dépôts au démarrage de QGIS (défaut connu de QGIS pouvant provoquer un plantage) : la vérification au démarrage reste désactivée et le provisioning garantit un jeton valide avant l'activation du dépôt.
- Utilisateur retiré du groupe beta entre deux mises à jour : son dépôt beta répond en refus d'accès ; son canal interne continue de fonctionner.
- Ancienne URL publique : les utilisateurs existants doivent être migrés. L'ancienne URL affiche une version finale de transition qui pointe vers la nouvelle procédure, puis est décommissionnée.
- Coupure réseau ou service indisponible pendant une mise à jour : QGIS affiche l'erreur standard du gestionnaire d'extensions, sans corruption de l'installation existante.
- Deux tags publiés à quelques secondes d'intervalle : le catalogue final reflète la version la plus récente, sans écrasement croisé.
- Version de préversion comparée à une version finale : l'ordre des versions est respecté (une préversion de 5.3.0 précède 5.3.0).
- Changement des liens du catalogue de flux : la configuration étant embarquée dans l'artefact (FR-016), le changement passe par une nouvelle release, jamais par une intervention sur les postes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système MUST distribuer le plugin via le gestionnaire d'extensions standard de QGIS (détection de mise à jour et installation en un clic), sans outil tiers côté utilisateur.
- **FR-002**: Tout accès au catalogue et aux artefacts MUST être authentifié par l'identité Microsoft Entra du CEN. Aucun accès anonyme.
- **FR-003**: Le système MUST exposer deux canaux : interne (toutes les identités du tenant autorisées) et beta (membres d'un groupe Entra dédié uniquement).
- **FR-004**: Le refus d'accès au canal beta MUST s'appliquer côté serveur. Un non-membre ne peut ni lister ni télécharger, même avec l'URL exacte.
- **FR-005**: L'utilisateur MUST pouvoir installer et mettre à jour le plugin sans saisir d'identifiants autres que son authentification Microsoft, et sans modifier de réglages QGIS.
- **FR-006**: Le renouvellement de jeton MUST être silencieux tant qu'un jeton de rafraîchissement est valide.
- **FR-007**: La publication MUST être déclenchée par un tag de version sur le dépôt GitHub privé, sans étape manuelle ultérieure. Le canal est déduit du format de version : préversion vers beta, version finale vers interne.
- **FR-008**: Un beta-testeur MUST se voir proposer la version la plus récente entre la dernière préversion et la dernière version finale (via l'enregistrement des deux canaux sur son poste ; chaque canal ne publie que sa propre dernière version).
- **FR-009**: Les versions MUST suivre un format à trois composants avec préversions ordonnées correctement par QGIS.
- **FR-010**: Le pipeline de publication MUST s'authentifier auprès du cloud par fédération d'identité, sans secret de longue durée stocké dans GitHub.
- **FR-011**: Toute l'infrastructure de distribution (socle Azure, service, stockage, droits) MUST être décrite en IaC versionné dans le dépôt. Les seules étapes manuelles admises sont les prérequis de bootstrap, documentés.
- **FR-012**: Le système MUST fournir un script de provisioning des postes, déployable par Intune, qui installe la configuration d'authentification et enregistre les dépôts. Le script MUST être idempotent et MUST détecter un port de retour d'authentification occupé pour basculer sur un port libre.
- **FR-013**: La vérification des dépôts au démarrage de QGIS MUST rester désactivée sur les postes provisionnés tant que le défaut QGIS associé au déclenchement d'une authentification interactive au démarrage n'est pas corrigé.
- **FR-014**: Une phase de POC MUST valider la chaîne complète sur le service de distribution (authentification, catalogue, téléchargement, restriction beta) avant l'industrialisation du provisioning et de la migration.
- **FR-015**: Le système MUST prévoir la migration des utilisateurs de l'ancienne URL publique : version de transition sur l'ancienne URL, puis décommissionnement.
- **FR-016**: Le paquet distribué MUST être auto-suffisant : la configuration applicative nécessaire au fonctionnement (liens du catalogue de flux) est injectée dans l'artefact au moment de la publication, depuis la configuration du pipeline. Elle ne DOIT jamais être versionnée dans le dépôt de code (invariant existant, contrôlé par la CI). Constat du POC : sans elle, le plugin installé ne charge aucun catalogue.

### Key Entities

- **Canal**: interne ou beta. Détermine qui voit quoi. Porte un catalogue et des règles d'accès.
- **Catalogue**: la liste des versions disponibles d'un canal, consommée par le gestionnaire d'extensions de QGIS.
- **Artefact**: l'archive d'une version du plugin, identifiée par son numéro de version.
- **Groupe d'accès**: groupe Entra qui matérialise l'appartenance au canal beta.
- **Configuration de poste**: la config d'authentification Microsoft et les dépôts enregistrés dans QGIS, posées par le provisioning.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un agent installe ou met à jour le plugin en moins de 2 minutes, sans saisir d'identifiants autres que son authentification Microsoft.
- **SC-002**: 100 % des tentatives d'accès sans identité du tenant sont refusées (catalogue et artefacts, deux canaux).
- **SC-003**: 100 % des tentatives d'accès au canal beta par un non-membre du groupe sont refusées.
- **SC-004**: Une version publiée par tag est disponible sur son canal en moins de 10 minutes, sans intervention manuelle.
- **SC-005**: Aucun secret de longue durée n'existe dans la configuration CI (vérifiable par revue des réglages du dépôt).
- **SC-006**: L'environnement de distribution est recréé depuis zéro, uniquement depuis le code versionné, en moins d'une heure, prérequis exclus.
- **SC-007**: Un poste provisionné par Intune est opérationnel au premier lancement de QGIS, sans aucune manipulation de l'utilisateur.
- **SC-008**: À la fin de la migration, plus aucun téléchargement ne transite par l'ancienne URL publique.

## Assumptions

- Le tenant Entra du CEN et l'inscription d'application « QGIS » (client public, flux avec code de vérification) existent et restent la base de l'authentification. Le POC réutilise cette application.
- Une souscription Azure est disponible ou sera créée manuellement avant l'application de l'IaC. La création de la souscription elle-même fait partie des prérequis de bootstrap documentés, pas de l'IaC.
- Le parc des utilisateurs cibles est géré par Intune et peut recevoir un script de déploiement.
- Les utilisateurs disposent de QGIS 3.34 minimum, conformément au plancher technique du plugin.
- Les postes ont accès à Internet et aux services Microsoft du tenant.
- Le canal beta liste aussi les versions finales : un beta-testeur n'a besoin que d'un seul dépôt.
- La beta est une restriction d'accès, pas une obligation : le groupe beta peut être modifié à tout moment sans toucher aux postes.
- Le POC porte sur le service de distribution managé (la « function ») retenu à l'issue de la recherche préalable. Si le POC échoue, l'alternative documentée (distribution directe depuis l'espace documentaire Microsoft 365) est réévaluée.
- La migration depuis l'ancienne URL publique se fait avec une période de transition annoncée ; la durée exacte sera fixée au plan.
