"""
Fetcher для UN Security Council Consolidated Sanctions
Источник: https://scsanctions.un.org/resources/xml/en/consolidated.xml
"""

import logging
import xml.etree.ElementTree as ET

import requests

from apps.tcc_data.models import SanctionEntry

logger = logging.getLogger(__name__)

UN_SANCTIONS_URL = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"


def _map_entity_type(un_type: str) -> str:
    un_type = (un_type or "").lower()
    if "individual" in un_type:
        return "individual"
    if "entity" in un_type:
        return "company"
    return "company"


def fetch_un_sanctions(source, log) -> dict:
    url = source.base_url or UN_SANCTIONS_URL
    logger.info("Fetching UN sanctions from %s", url)

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    # UN XML: <INDIVIDUALS><INDIVIDUAL>... and <ENTITIES><ENTITY>...
    individuals = root.findall(".//INDIVIDUAL") or root.findall(".//{*}INDIVIDUAL")
    entities = root.findall(".//ENTITY") or root.findall(".//{*}ENTITY")

    fetched = 0
    new = 0
    updated = 0
    seen_ids = set()

    def _text(parent, tag):
        el = parent.find(tag)
        if el is None:
            el = parent.find(f"{{*}}{tag}")
        return (el.text or "").strip() if el is not None else ""

    def process_entry(entry, entity_type_str):
        nonlocal fetched, new, updated

        dataid = _text(entry, "DATAID")
        if not dataid:
            return

        seen_ids.add(dataid)
        fetched += 1

        # Name
        if entity_type_str == "individual":
            first = _text(entry, "FIRST_NAME")
            second = _text(entry, "SECOND_NAME")
            third = _text(entry, "THIRD_NAME")
            name = " ".join(filter(None, [first, second, third])) or f"UN-{dataid}"
        else:
            name = _text(entry, "FIRST_NAME") or f"UN-{dataid}"

        # Aliases
        aliases = []
        for alias_el in entry.findall(".//ALIAS") + entry.findall(".//{*}ALIAS"):
            alias_name = _text(alias_el, "ALIAS_NAME")
            if alias_name:
                aliases.append(alias_name)

        # Programme / listed under
        un_list = _text(entry, "UN_LIST_TYPE")

        # Nationality
        countries = []
        for nat_el in entry.findall(".//NATIONALITY") + entry.findall(".//{*}NATIONALITY"):
            val_el = nat_el.find("VALUE") or nat_el.find("{*}VALUE")
            if val_el is not None and val_el.text:
                countries.append(val_el.text.strip())

        listing_date_str = _text(entry, "LISTED_ON")
        listing_date = None
        if listing_date_str:
            from datetime import datetime
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b. %Y"):
                try:
                    listing_date = datetime.strptime(listing_date_str, fmt).date()
                    break
                except ValueError:
                    continue

        obj, created = SanctionEntry.objects.update_or_create(
            source=source,
            external_id=dataid,
            defaults={
                "entity_type": entity_type_str,
                "name_primary": name[:500],
                "name_aliases": aliases,
                "countries": countries,
                "program": un_list[:300],
                "listing_date": listing_date,
                "is_active": True,
            },
        )
        if created:
            new += 1
        else:
            updated += 1

    for ind in individuals:
        process_entry(ind, "individual")
    for ent in entities:
        process_entry(ent, "company")

    deactivated = (
        SanctionEntry.objects.filter(source=source, is_active=True)
        .exclude(external_id__in=seen_ids)
        .update(is_active=False)
    )
    if deactivated:
        logger.info("Deactivated %d removed UN entries", deactivated)

    return {"fetched": fetched, "new": new, "updated": updated}
