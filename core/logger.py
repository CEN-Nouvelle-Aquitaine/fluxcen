from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox

TAG = "FluxCEN"

# Icône QMessageBox correspondant à chaque niveau de gravité QGIS.
# Qgis.MessageLevel.Success n'a pas d'équivalent dédié dans QMessageBox.
_LEVEL_TO_ICON = {
    Qgis.MessageLevel.Info: QMessageBox.Information,
    Qgis.MessageLevel.Success: QMessageBox.Information,
    Qgis.MessageLevel.Warning: QMessageBox.Warning,
    Qgis.MessageLevel.Critical: QMessageBox.Critical,
}

def log(
    message: str,
    level: Qgis.MessageLevel = Qgis.MessageLevel.Info,
    display: bool = False,
    duration: int = 5
) -> None :
    """
    Journalise le message et, optionnellement,
    l'affiche dans la barre de messages de l'interface.
    -> Non bloquant. A utiliser pour journaliser ou informer.

    Tous les messages sont regroupés sous le tag TAG ("FluxCEN") : 
    - nom de l'onglet dédié dans le "Journal des messages" de QGIS
    - titre affiché dans la barre de messages

    Args:
        message: str - Texte du message à journaliser.
        level: Qgis.MessageLevel - Niveau de gravité (Info, Success, Warning, Critical).
            Par défaut Qgis.MessageLevel.Info.
        display: bool - Si True, affiche également le message dans la barre de
            messages de l'interface QGIS (iface.messageBar()).
            Par défaut False.
        duration: int - Durée d'affichage du message dans la barre de messages,
            en secondes. Ignoré si display est False.
            Par défaut 5 secondes.
    """

    QgsMessageLog.logMessage(
        message,
        TAG,
        level
    )
    
    if display:
        iface.messageBar().pushMessage(
            TAG,
            message,
            level,
            duration
        )

def alert(
    message: str,
    level: Qgis.MessageLevel = Qgis.MessageLevel.Info,
    buttons: QMessageBox.StandardButton = QMessageBox.Ok | QMessageBox.Cancel,
    parent = None,
    detail: str = None,
    title: str = None,
) -> QMessageBox:
    """
    Journalise le message puis affiche une popup bloquante à l'utilisateur.
    -> Bloquant. À utiliser pour solliciter l'attention, l'action ou le consentement de l'utilisateur.
    
    La popup peut contenir un ou plusieurs boutons et le code appelant peut comparer le bouton cliqué.
    La popup peut s'addosser à la fenêtre parente du plugin afin de passer en premier plan,
    contrairement à log() inhérent à la fenêtre principale de QGIS.

    Args:
        message: str - Texte affiché dans la popup et journalisé.
        level: Qgis.MessageLevel - Niveau de gravité, détermine l'icône le dictionnaire `_LEVEL_TO_ICON`
            Par défaut Qgis.MessageLevel.Info
        buttons: QMessageBox.StandardButton - Bouton(s) affiché(s) dans la popup. 
            Par défaut QMessageBox.Ok | QMessageBox.Cancel
        parent: QWidget - Parent de la popup. 
            Par défaut iface.mainWindow(), fenêtre principale de QGIS.
        detail: str - Texte complémentaire affiché dans la section "Détails" de la popup.
            Par défaut None, pas de section "Détails".
        title: str - Titre de la fenêtre. 
            Par défaut TAG ("FluxCEN")

    Returns:
        Widget popup QMessageBox. 
        Le code appelant peut comparer le bouton cliqué avec les boutons passés en argument
        (ex: if alert() == QMessageBox.Ok: do_something()).
    """

    log(message, level)

    box = QMessageBox(
        _LEVEL_TO_ICON.get(level, QMessageBox.Information),
        title or TAG,
        message,
        buttons,
        parent or iface.mainWindow()
    )
    box.setDetailedText(detail)
    return box.exec_()