"""Evaluador local LIMITADO de expresiones para comprobaciones estáticas.

No implementa Power Automate ni valida su motor. Rechaza cualquier sintaxis
o función no enumerada. Se usa con casos sintéticos, sin peticiones de red.
"""
import json
import re
from urllib.parse import unquote, urlsplit

TOKEN = re.compile(r"\s*(?:(?P<string>'(?:[^']|'')*')|(?P<number>-?\d+)|(?P<name>[A-Za-z_][A-Za-z_0-9]*)|(?P<punct>[(),?\[\]]))")


def texto(valor):
    if valor is None:
        return ""
    if isinstance(valor, (dict, list, bool)):
        return json.dumps(valor, ensure_ascii=False, separators=(",", ":"))
    return str(valor)


def evaluar(expresion, outputs=None, actions=None):
    if not isinstance(expresion, str) or not expresion.startswith("@"):
        return expresion
    source = expresion[1:]
    tokens, offset = [], 0
    while offset < len(source):
        match = TOKEN.match(source, offset)
        if match is None:
            raise ValueError(f"Sintaxis no soportada en posición {offset}")
        tokens.append((match.lastgroup, match.group(match.lastgroup)))
        offset = match.end()
    pos = 0

    def consumir(valor):
        nonlocal pos
        if pos >= len(tokens) or tokens[pos][1] != valor:
            raise ValueError(f"Se esperaba {valor}")
        pos += 1

    def leer():
        nonlocal pos
        clase, valor = tokens[pos]
        pos += 1
        if clase == "string":
            result = valor[1:-1].replace("''", "'")
        elif clase == "number":
            result = int(valor)
        elif valor in ("true", "false", "null"):
            result = {"true": True, "false": False, "null": None}[valor]
        elif clase == "name":
            consumir("(")
            args = []
            if tokens[pos][1] != ")":
                args.append(leer())
                while tokens[pos][1] == ",":
                    consumir(",")
                    args.append(leer())
            consumir(")")
            funciones = {
                "outputs": lambda k: (outputs or {})[k],
                "actions": lambda k: (actions or {})[k],
                "trim": lambda s: s.strip(), "string": texto, "toLower": lambda s: s.lower(),
                "empty": lambda v: v is None or v == "" or v == [] or v == {},
                "contains": lambda v, item: item in v,
                "equals": lambda a, b: a == b, "and": lambda *v: all(v), "or": lambda *v: any(v),
                "not": lambda v: not v, "if": lambda c, a, b: a if c else b,
                "greaterOrEquals": lambda a, b: a >= b, "less": lambda a, b: a < b,
                "int": int, "coalesce": lambda *v: next((x for x in v if x is not None), None),
                "take": lambda v, n: v[:n], "concat": lambda *v: "".join(v),
                "decodeUriComponent": unquote,
                "uriScheme": lambda v: urlsplit(v).scheme,
                "uriHost": lambda v: urlsplit(v).hostname or "",
                "uriPath": lambda v: urlsplit(v).path,
                "uriQuery": lambda v: ("?" + urlsplit(v).query) if urlsplit(v).query else "",
            }
            if valor not in funciones:
                raise ValueError(f"Función no soportada: {valor}")
            result = funciones[valor](*args)
        else:
            raise ValueError("Expresión no soportada")
        while pos < len(tokens) and tokens[pos][1] in ("?", "["):
            opcional = tokens[pos][1] == "?"
            if opcional:
                consumir("?")
            consumir("[")
            key = leer()
            consumir("]")
            result = (result or {}).get(key) if opcional else result[key]
        return result

    result = leer()
    if pos != len(tokens):
        raise ValueError("Tokens sobrantes")
    return result


def evaluar_objeto(objeto, outputs=None, actions=None):
    if isinstance(objeto, dict):
        return {k: evaluar_objeto(v, outputs, actions) for k, v in objeto.items()}
    if isinstance(objeto, list):
        return [evaluar_objeto(v, outputs, actions) for v in objeto]
    return evaluar(objeto, outputs, actions)
