"""
Fetcher для OFAC SDN List (Specially Designated Nationals)
Источник: https://www.treasury.gov/ofac/downloads/sdn.xml
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from apps.tcc_data.models import SanctionEntry

logger = logging.getLogger(__name__)

OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"
NS = {"sdn": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML"}


def _parse_entity_type(sdn_type: str) -> str:
    mapping = {
        "Individual": "individual",
        "Entity": "company",
        "Vessel": "vessel",
        "Aircraft": "aircraft",
    }
    return mapping.get(sdn_type, "company")


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def fetch_ofac_sdn(source, log) -> dict:
    """
    Скачивает SDN XML, парсит, upsert в SanctionEntry.
    Возвращает: {fetched, new, updated}
    """
    url = source.base_url or OFAC_SDN_URL
    logger.info("Fetching OFAC SDN from %s", url)

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    # OFAC XML может иметь namespace или нет
    # Пробуем без namespace сначала
    entries = root.findall(".//sdnEntry")
    if not entries:
        entries = root.findall(".//{*}sdnEntry")

    fetched = 0
    new = 0
    updated = 0
    seen_ids = set()

    for entry in entries:
        uid_el = entry.find("uid") or entry.find("{*}uid")
        if uid_el is None:
            continue

        uid = uid_el.text.strip()
        seen_ids.add(uid)
        fetched += 1

        # Основное имя
        first_name_el = entry.find("firstName") or entry.find("{*}firstName")
        last_name_el = entry.find("lastName") or entry.find("{*}lastName")
        first_name = (first_name_el.text or "").strip() if first_name_el is not None else ""
        last_name = (last_name_el.text or "").strip() if last_name_el is not None else ""
        name = f"{first_name} {last_name}".strip() or f"OFAC-{uid}"

        # Тип
        sdn_type_el = entry.find("sdnType") or entry.find("{*}sdnType")
        sdn_type = (sdn_type_el.text or "Entity").strip() if sdn_type_el is not None else "Entity"

        # Программа
        programs = []
        for prog_el in entry.findall(".//program") + entry.findall(".//{*}program"):
            if prog_el.text:
                programs.append(prog_el.text.strip())
        program = "; ".join(programs)

        # Псевдонимы
        aliases = []
        for aka in entry.findall(".//aka") + entry.findall(".//{*}aka"):
            aka_name_parts = []
            for child in aka:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag in ("firstName", "lastName") and child.text:
                    aka_name_parts.append(child.text.strip())
            if aka_name_parts:
                aliases.append(" ".join(aka_name_parts))

        # Страны из адресов
        countries = []
        for addr in entry.findall(".//address") + entry.findall(".//{*}address"):
            country_el = addr.find("country") or addr.find("{*}country")
            if country_el is not None and country_el.text:
                countries.append(country_el.text.strip())
        countries = list(set(countries))

        # Upsert
        obj, created = SanctionEntry.objects.update_or_create(
            source=source,
            external_id=uid,
            defaults={
                "entity_type": _parse_entity_type(sdn_type),
                "name_primary": name[:500],
                "name_aliases": aliases,
                "countries": countries,
                "program": program[:300],
                "is_active": True,
                "raw_data": {"sdn_type": sdn_type, "uid": uid},
            },
        )
        if created:
            new += 1
        else:
            updated += 1

    # Деактивируем удалённые записи
    deactivated = (
        SanctionEntry.objects.filter(source=source, is_active=True)
        .exclude(external_id__in=seen_ids)
        .update(is_active=False)
    )
    if deactivated:
        logger.info("Deactivated %d removed OFAC entries", deactivated)

    return {"fetched": fetched, "new": new, "updated": updated}
