# -*- coding: utf-8 -*-
"""Service de distribution FluxCEN : dépôt de plugins QGIS privé.

Easy Auth (Entra ID) authentifie en amont : toute requête arrivant ici porte
une identité du tenant validée (sinon 401 avant nous). Dépôt unique, standard
communautaire : les préversions sont des entrées ``experimental`` du
catalogue, pas un canal séparé. Ce handler sert le blob en 200 direct
(jamais de 3xx, contrat http-delivery.md).
"""
import logging
import os

import azure.functions as func
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

import logic

app = func.FunctionApp()

_blob_service: BlobServiceClient | None = None


def _container():
    """Client du conteneur `plugins`, construit une fois par instance."""
    global _blob_service  # pylint: disable=global-statement
    if _blob_service is None:
        _blob_service = BlobServiceClient(
            os.environ["STORAGE_ACCOUNT_URL"], credential=DefaultAzureCredential()
        )
    return _blob_service.get_container_client("plugins")


@app.route(route="{channel}/{filename}", auth_level=func.AuthLevel.ANONYMOUS,
           methods=["GET"])
def serve(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/{channel}/{filename} : catalogue ou zip, en 200 direct."""
    channel = req.route_params.get("channel", "")
    filename = req.route_params.get("filename", "")

    blob_path = logic.resolve_blob(channel, filename)
    if blob_path is None:
        return func.HttpResponse(status_code=404)

    try:
        payload = _container().download_blob(blob_path).readall()
    except ResourceNotFoundError:
        return func.HttpResponse(status_code=404)

    logging.info("Servi %s (%d octets)", blob_path, len(payload))
    return func.HttpResponse(payload, status_code=200,
                             mimetype=logic.content_type(filename))
