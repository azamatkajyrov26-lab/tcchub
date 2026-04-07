"""
Fetcher для World Bank Open Data API.
Обновляет Country.wb_stability_index и Country.imf_gdp_growth.
"""

import logging

import requests

from apps.tcc_core.models import Country

logger = logging.getLogger(__name__)

WB_API_BASE = "https://api.worldbank.org/v2"

# Political Stability and Absence of Violence/Terrorism
STABILITY_INDICATOR = "PV.EST"
# GDP growth (annual %)
GDP_GROWTH_INDICATOR = "NY.GDP.MKTP.KD.ZG"


def fetch_worldbank_indicators(source, log):
    """Загружает индикаторы World Bank для всех стран коридоров"""
    countries = Country.objects.all()
    iso3_map = {c.iso3: c for c in countries}
    iso_codes = ";".join(iso3_map.keys())

    updated = 0

    # Fetch Political Stability — one country at a time (WGI API has limits on multi-country)
    for iso3, country in iso3_map.items():
        try:
            url = f"{WB_API_BASE}/country/{iso3}/indicator/{STABILITY_INDICATOR}"
            resp = requests.get(url, params={"format": "json", "per_page": 5, "mrnev": 1}, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if len(data) > 1 and data[1]:
                for item in data[1]:
                    if item.get("value") is not None:
                        country.wb_stability_index = round(float(item["value"]), 3)
                        country.save(update_fields=["wb_stability_index", "last_updated"])
                        updated += 1
                        break
        except Exception as e:
            logger.warning("Failed to fetch WB stability for %s: %s", iso3, e)

    # Fetch GDP Growth
    try:
        url = f"{WB_API_BASE}/country/{iso_codes}/indicator/{GDP_GROWTH_INDICATOR}"
        resp = requests.get(url, params={"format": "json", "per_page": 100, "mrnev": 1}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if len(data) > 1 and data[1]:
            for item in data[1]:
                if item.get("value") is not None:
                    iso3 = item["countryiso3code"]
                    country = iso3_map.get(iso3)
                    if country:
                        country.imf_gdp_growth = round(float(item["value"]), 2)
                        country.save(update_fields=["imf_gdp_growth", "last_updated"])
                        updated += 1
    except Exception as e:
        logger.error("Failed to fetch WB GDP growth: %s", e)

    return {"fetched": updated, "new": 0, "updated": updated}
