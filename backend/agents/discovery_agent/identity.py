"""Conservative dataset identity: source IDs and equivalent reference URLs.

Names/descriptions alone are not identity evidence. Keep the first record so
the coordinator can prefer curated catalog metadata over inferred live metadata.
"""
from collections.abc import Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def canonical_dataset_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        parsed = urlsplit(url.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        # Authenticated URLs must not be treated as public dataset identities.
        if parsed.username is not None or parsed.password is not None:
            return None
        host = parsed.hostname.lower()
        port = parsed.port
    except ValueError:
        return None
    # These dataset providers serve the same pages on www and bare hosts,
    # and redirect HTTP to HTTPS. Do not assume this for arbitrary sites.
    providers = {"kaggle.com", "openml.org", "huggingface.co"}
    bare_host = host.removeprefix("www.")
    provider = bare_host in providers and (port is None or
        parsed.scheme.lower() == "http" and port == 80 or
        parsed.scheme.lower() == "https" and port == 443)
    if provider:
        host = bare_host
    elif port is not None and not (
        parsed.scheme.lower() == "http" and port == 80
        or parsed.scheme.lower() == "https" and port == 443
    ):
        host = f"[{host}]:{port}" if ":" in host else f"{host}:{port}"
    elif ":" in host:
        host = f"[{host}]"
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"gclid", "fbclid"}]
    path = parsed.path or "/"
    if provider:
        path = path.rstrip("/") or "/"
    # Known dataset pages use section anchors. Unknown sites may use hash
    # routing to identify entirely different records, so retain their fragment.
    dataset_page = provider and ((host in {"kaggle.com", "huggingface.co"} and path.startswith("/datasets/"))
                                 or (host == "openml.org" and path.startswith("/d/")))
    return urlunsplit(("https" if provider else parsed.scheme.lower(), host,
                       path, urlencode(query), "" if dataset_page else parsed.fragment))


def deduplicate_records(records: Iterable[Mapping]) -> list[dict]:
    groups: list[tuple[dict, set[tuple]]] = []
    for record in records:
        keys = set()
        if record.get("source") is not None and record.get("id") is not None:
            keys.add(("source_id", record["source"], str(record["id"])))
        url = canonical_dataset_url(record.get("url"))
        if url:
            keys.add(("url", url))
        overlaps = [i for i, (_, existing) in enumerate(groups) if keys & existing]
        if not overlaps:
            groups.append((dict(record), keys))
            continue
        first = overlaps[0]
        groups[first][1].update(keys)
        # A record can bridge a source ID seen without a URL and a catalog
        # URL seen without that source ID. Reconcile both groups transitively.
        for i in reversed(overlaps[1:]):
            groups[first][1].update(groups[i][1])
            del groups[i]
    return [record for record, _ in groups]
