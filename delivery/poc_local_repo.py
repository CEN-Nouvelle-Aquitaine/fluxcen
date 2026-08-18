# -*- coding: utf-8 -*-
"""Simulateur local du dépôt de plugins FluxCEN (POC sans Azure).

Rejoue le contrat http-delivery.md sur 127.0.0.1 : Bearer obligatoire (401),
canal beta restreint (403), catalogue et zip servis en 200 direct. Permet de
valider dans un QGIS local le mécanisme clé (authcfg appliqué au plugins.xml
ET au zip, détection de mise à jour) avant tout déploiement Azure.

Usage :
    python3 delivery/poc_local_repo.py --zip FluxCEN.5.3.0.zip \
        [--port 8787] [--token poc-interne] [--beta-token poc-beta]

Côté QGIS : authcfg « API Header » avec `Authorization: Bearer poc-interne`,
dépôt http://127.0.0.1:8787/stable/plugins.xml. Stdlib uniquement, usage POC.
"""
import argparse
import http.server
import pathlib
import re

CHANNELS = ("stable", "beta")


def build_catalogue(base_url: str, channel: str, version: str, qgis_min: str) -> bytes:
    """plugins.xml minimal conforme au format du dépôt de plugins QGIS."""
    return f"""<?xml version="1.0"?>
<plugins>
  <pyqgis_plugin name="FluxCEN" version="{version}">
    <description>Centralisation des flux WFS/WMS du CEN-NA (POC delivery)</description>
    <version>{version}</version>
    <qgis_minimum_version>{qgis_min}</qgis_minimum_version>
    <download_url>{base_url}/{channel}/FluxCEN.{version}.zip</download_url>
    <file_name>FluxCEN.{version}.zip</file_name>
    <author_name>CEN-NA</author_name>
    <experimental>False</experimental>
  </pyqgis_plugin>
</plugins>
""".encode()


def make_handler(zip_path: pathlib.Path, version: str, tokens: dict, qgis_min: str):
    """Handler HTTP appliquant le contrat : 401 sans jeton, 403 beta, 200 sinon."""

    class Handler(http.server.BaseHTTPRequestHandler):
        """Sert /{canal}/plugins.xml et /{canal}/FluxCEN.<version>.zip."""

        def do_GET(self):  # pylint: disable=invalid-name
            """Applique le contrat puis sert le catalogue ou le zip."""
            path = self.path.split("?", 1)[0]  # QGIS ajoute ?qgis=x.y : ignoré
            match = re.fullmatch(r"/(\w+)/(plugins\.xml|FluxCEN\.[\w.\-]+\.zip)", path)
            if not match or match.group(1) not in CHANNELS:
                return self._status(404)
            channel = match.group(1)

            auth = self.headers.get("Authorization", "")
            self.log_message("Authorization reçu : %r", auth or "(absent)")
            if not auth.startswith("Bearer ") or auth[7:] not in tokens.values():
                return self._status(401)
            if channel == "beta" and auth[7:] != tokens["beta"]:
                return self._status(403)

            if match.group(2) == "plugins.xml":
                base = f"http://127.0.0.1:{self.server.server_port}"
                return self._payload(build_catalogue(base, channel, version, qgis_min),
                                     "text/xml")
            return self._payload(zip_path.read_bytes(), "application/zip")

        def _status(self, code):
            self.send_response(code)
            self.end_headers()

        def _payload(self, body, ctype):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=pathlib.Path,
                        help="zip du plugin à servir")
    parser.add_argument("--version", default=None,
                        help="version publiée (défaut : déduite du nom du zip)")
    parser.add_argument("--qgis-min", default="3.34")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--token", default="poc-interne",
                        help="Bearer attendu (canal stable)")
    parser.add_argument("--beta-token", default="poc-beta",
                        help="Bearer attendu pour le canal beta")
    args = parser.parse_args()

    version = args.version or re.sub(r"^FluxCEN\.|\.zip$", "", args.zip.name)
    tokens = {"stable": args.token, "beta": args.beta_token}
    handler = make_handler(args.zip, version, tokens, args.qgis_min)
    print(f"Dépôt simulé : http://127.0.0.1:{args.port}/stable/plugins.xml "
          f"(version {version}, Bearer {args.token} / beta {args.beta_token})")
    http.server.HTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
