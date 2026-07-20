from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface

TAG = "FluxCEN"

def log(
    message: str,
    level: Qgis.MessageLevel = Qgis.MessageLevel.Info,
    display: bool = False,
    duration: int = 5
) -> None :
    """
    Écrit un message dans le journal QGIS et, optionnellement,
    l'affiche dans la barre de messages de l'interface.

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