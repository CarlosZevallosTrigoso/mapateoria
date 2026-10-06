#!/usr/bin/env python3
"""Fusiona los JSON de la carpeta nodos/ en un único grafo.json y registra advertencias.

Uso: python scripts/fusionar.py --entrada nodos --salida _site
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ORDEN_ESTADO = {"pendiente": 0, "indexado": 1, "seleccionado": 2, "desarrollado": 3}
PREFIJOS = {
    "concepto": "concepto", "enfoque": "enfoque", "autor": "autor", "obra": "obra",
    "definicion": "def", "cita": "cita", "metafora": "metafora", "caso": "caso",
    "lectura_caso": "lectura", "campo": "campo",
}
ARISTAS_ESTRUCTURALES = {
    "pertenece_a", "escribe", "formula", "define", "fuente_de", "sostiene", "usa_modelo",
    "aplica", "sobre", "contraconcepto_de", "vecino_de", "indexado_en",
}
ARISTAS_INTERPRETATIVAS = {"antagonismo", "resonancia", "filiacion", "variacion", "recepcion"}
RE_ID = re.compile(r"^[a-z_]+:[a-z0-9][a-z0-9\-:]*$")


def normalizar(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def clave_arista(a):
    return "|".join(str(a.get(k) or "") for k in ("origen", "tipo", "destino", "eje", "segun"))


class Fusion:
    def __init__(self):
        self.nodos, self.aristas, self.ejes = {}, {}, {}
        self.archivos, self.advertencias = [], []

    def avisar(self, nivel, tipo, mensaje, archivo=None, ident=None):
        self.advertencias.append({"nivel": nivel, "tipo": tipo, "mensaje": mensaje,
                                  "archivo": archivo, "id": ident})

    def combinar(self, destino, nuevo, archivo, etiqueta):
        """Completa campos vacíos; ante valores distintos gana el archivo más reciente y se avisa."""
        for k, v in nuevo.items():
            if k.startswith("_"):
                continue
            if k == "estado":
                actual = destino.get("estado")
                if ORDEN_ESTADO.get(v, -1) > ORDEN_ESTADO.get(actual, -1):
                    destino["estado"] = v
                continue
            if k not in destino or destino[k] in (None, "", []):
                destino[k] = v
            elif destino[k] != v and v not in (None, "", []):
                self.avisar("aviso", "conflicto",
                            f"«{k}» difiere entre archivos; se conserva la versión de {archivo}.",
                            archivo, etiqueta)
                destino[k] = v
        destino.setdefault("_fuentes", [])
        if archivo not in destino["_fuentes"]:
            destino["_fuentes"].append(archivo)

    def cargar(self, ruta):
        nombre = ruta.name
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.avisar("error", "json_invalido", f"No se pudo leer: {e}", nombre)
            return
        if not isinstance(datos, dict) or not isinstance(datos.get("nodos"), list):
            self.avisar("error", "estructura", "El archivo no tiene una lista «nodos».", nombre)
            return
        expl = datos.get("exploracion") or {}
        self.archivos.append({"nombre": nombre, "exploracion": expl,
                              "nodos": len(datos.get("nodos", [])),
                              "aristas": len(datos.get("aristas", []))})
        for e in datos.get("ejes") or []:
            if not e.get("id"):
                self.avisar("aviso", "eje_sin_id", "Eje sin identificador.", nombre)
                continue
            self.combinar(self.ejes.setdefault(e["id"], {}), e, nombre, e["id"])
        for n in datos["nodos"]:
            ident = n.get("id")
            if not ident:
                self.avisar("error", "nodo_sin_id", f"Nodo sin identificador: {str(n)[:80]}", nombre)
                continue
            if not RE_ID.match(ident):
                self.avisar("aviso", "id_mal_formado",
                            "El identificador tiene mayúsculas, tildes o espacios.", nombre, ident)
            pref = PREFIJOS.get(n.get("tipo"))
            if pref is None:
                self.avisar("aviso", "tipo_desconocido", f"Tipo de nodo desconocido: {n.get('tipo')}", nombre, ident)
            elif not ident.startswith(pref + ":"):
                self.avisar("aviso", "prefijo", f"El tipo «{n.get('tipo')}» debería usar el prefijo «{pref}:».", nombre, ident)
            self.combinar(self.nodos.setdefault(ident, {}), n, nombre, ident)
        for a in datos.get("aristas") or []:
            if a.get("tipo") not in ARISTAS_ESTRUCTURALES | ARISTAS_INTERPRETATIVAS:
                self.avisar("aviso", "arista_desconocida", f"Tipo de arista desconocido: {a.get('tipo')}", nombre)
            self.combinar(self.aristas.setdefault(clave_arista(a), {}), a, nombre, clave_arista(a))

    def validar(self):
        for clave, a in list(self.aristas.items()):
            faltan = [x for x in (a.get("origen"), a.get("destino")) if x not in self.nodos]
            if faltan:
                self.avisar("error", "arista_colgante",
                            f"La arista {a.get('tipo')} apunta a nodos inexistentes: {', '.join(map(str, faltan))}. Se descartó.",
                            ", ".join(a.get("_fuentes", [])), clave)
                del self.aristas[clave]
                continue
            if a.get("eje") and a["eje"] not in self.ejes:
                self.avisar("aviso", "eje_desconocido", f"Eje no declarado: {a['eje']}",
                            ", ".join(a.get("_fuentes", [])), clave)
            if a.get("segun") and a["segun"] not in self.nodos:
                self.avisar("aviso", "segun_desconocido", f"«segun» apunta a un nodo inexistente: {a['segun']}",
                            ", ".join(a.get("_fuentes", [])), clave)
        conectados = {a["origen"] for a in self.aristas.values()} | {a["destino"] for a in self.aristas.values()}
        for ident, n in self.nodos.items():
            if ident not in conectados:
                self.avisar("aviso", "aislado", "Nodo sin aristas.", ", ".join(n.get("_fuentes", [])), ident)
        vistos = {}
        for ident, n in self.nodos.items():
            if n.get("tipo") not in ("autor", "concepto", "obra", "enfoque"):
                continue
            clave = (n.get("tipo"), normalizar(n.get("etiqueta")))
            if clave[1] and clave in vistos and vistos[clave] != ident:
                self.avisar("aviso", "posible_duplicado",
                            f"Misma etiqueta que {vistos[clave]}; ¿es la misma entidad con dos identificadores?",
                            None, ident)
            vistos.setdefault(clave, ident)

    def resultado(self):
        return {
            "esquema": "glosario-grafo/1",
            "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "archivos": self.archivos,
            "ejes": list(self.ejes.values()),
            "nodos": list(self.nodos.values()),
            "aristas": list(self.aristas.values()),
            "advertencias": self.advertencias,
        }


def fecha_de(ruta):
    try:
        return (json.loads(ruta.read_text(encoding="utf-8")).get("exploracion") or {}).get("fecha") or ""
    except Exception:
        return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--entrada", default="nodos")
    p.add_argument("--salida", default=".")
    args = p.parse_args()

    rutas = sorted(Path(args.entrada).glob("*.json"), key=lambda r: (fecha_de(r), r.name))
    f = Fusion()
    for r in rutas:
        f.cargar(r)
    f.validar()
    res = f.resultado()

    os.makedirs(args.salida, exist_ok=True)
    Path(args.salida, "grafo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    resumen = [f"Archivos: {len(rutas)}  Nodos: {len(res['nodos'])}  Aristas: {len(res['aristas'])}  "
               f"Advertencias: {len(res['advertencias'])}"]
    resumen += [f"- [{a['nivel']}] {a['tipo']}: {a['mensaje']} ({a.get('id') or ''} {a.get('archivo') or ''})"
                for a in res["advertencias"]]
    print("\n".join(resumen))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as s:
            s.write("## Grafo del glosario\n\n" + "\n".join(resumen) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
