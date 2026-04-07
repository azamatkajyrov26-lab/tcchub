"""
Fetcher для EU Consolidated Sanctions List
Источник: https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content
"""

import logging
import xml.etree.ElementTree as ET

import requests

from apps.tcc_data.models import SanctionEntry

logger = logging.getLogger(__name__)

EU_SANCTIONS_URL = (
    "https://webgate.ec.europa.eu/fsd/fsf/public/files/"
    "xmlFullSanctionsList_1_1/content"
)


def _map_entity_type(eu_type: str) -> str:
    eu_type = (eu_type or "").lower()
    if "person" in eu_type or "individual" in eu_type:
        return "individual"
    if "enterprise" in eu_type or "entity" in eu_type:
        return "company"
    return "company"


def fetch_eu_sanctions(source, log) -> dict:
    url = source.base_url or EU_SANCTIONS_URL
    logger.info("Fetching EU sanctions from %s", url)

    response = requests.get(url, timeout=180)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    # EU XML uses varying tag names
    entities = (
        root.findall(".//{*}sanctionEntity")
        or root.findall(".//sanctionEntity")
        or root.findall(".//{*}entity")
    )

    fetched = 0
    new = 0
    updated = 0
    seen_ids = set()

    for entity in entities:
        # Extract logicalId or EU reference number
        eid = entity.get("logicalId") or entity.get("euReferenceNumber") or ""
        if not eid:
            # Try child element
            ref_el = entity.find("{*}euReferenceNumber") or entity.find("euReferenceNumber")
            eid = (ref_el.text or "").strip() if ref_el is not None else ""
        if not eid:
            continue

        seen_ids.add(eid)
        fetched += 1

        # Name
        name_parts = []
        for name_el in entity.findall(".//{*}wholeName") + entity.findall(".//wholeName"):
            if name_el.text:
                name_parts.append(name_el.text.strip())
        if not name_parts:
            for name_el in entity.findall(".//{*}lastName") + entity.findall(".//lastName"):
                if name_el.text:
                    name_parts.append(name_el.text.strip())
        name = name_parts[0] if name_parts else f"EU-{eid}"
        aliases = name_parts[1:] if len(name_parts) > 1 else []

        # Entity type
        subj_type_el = entity.find("{*}subjectType") or entity.find("subjectType")
        subj_type = (subj_type_el.text or "").strip() if subj_type_el is not None else ""

        # Programme
        programme_el = entity.find(".//{*}programme") or entity.find(".//programme")
        programme = ""
        if programme_el is not None:
            programme = (programme_el.text or "").strip()

        # Countries
        countries = []
        for citizen_el in entity.findall(".//{*}countryIso2Code") + entity.findall(".//countryIso2Code"):
            if citizen_el.text:
                countries.append(citizen_el.text.strip().upper())
        countries = list(set(countries))

        obj, created = SanctionEntry.objects.update_or_create(
            source=source,
            external_id=eid,
            defaults={
                "entity_type": _map_entity_type(subj_type),
                "name_primary": name[:500],
                "name_aliases": aliases,
                "countries": countries,
                "program": programme[:300],
                "is_active": True,
            },
        )
        if created:
            new += 1
        else:
            updated += 1

    deactivated = (
        SanctionEntry.objects.filter(source=source, is_active=True)
        .exclude(external_id__in=seen_ids)
        .update(is_active=False)
    )
    if deactivated:
        logger.info("Deactivated %d removed EU entries", deactivated)

    return {"fetched": fetched, "new": new, "updated": updated}
