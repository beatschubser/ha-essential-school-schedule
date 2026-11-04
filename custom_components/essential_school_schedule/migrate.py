"""One-time takeover from the former integration "Sleek School Schedule" (domain sleek_school_schedule).

When a child is added here with the same name as a child of the old integration:
- its timetable is copied from .storage/sleek_school_schedule,
- the old config entry is removed, so its sensors free their entity IDs
  (the new sensors get the same IDs and automations keep working),
- after the last old child the old storage file and the old dashboard resource are removed.

Can be deleted in a later major version.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .logic import normalize_plan
from .store import PlanStore

_LOGGER = logging.getLogger(__name__)

OLD_DOMAIN = "sleek_school_schedule"
OLD_STORAGE_VERSION = 1
OLD_FRONTEND_URL = "/sleek_school_schedule_files"


async def async_take_over(hass: HomeAssistant, entry: ConfigEntry, store: PlanStore) -> None:
    old = next((e for e in hass.config_entries.async_entries(OLD_DOMAIN) if e.unique_id == entry.unique_id), None)
    if old is None:
        return

    old_store: Store[dict] = Store(hass, OLD_STORAGE_VERSION, OLD_DOMAIN)
    plan = ((await old_store.async_load() or {}).get("plans") or {}).get(old.entry_id)
    if plan is not None:
        await store.async_set(entry.entry_id, normalize_plan(plan))
        _LOGGER.info("Timetable of %s taken over from Sleek School Schedule", entry.title)

    await hass.config_entries.async_remove(old.entry_id)
    if not hass.config_entries.async_entries(OLD_DOMAIN):
        await old_store.async_remove()


async def async_remove_old_resource(resources) -> None:
    """Dashboard resource of the old card (only left over if the old integration was not running)."""
    for item in [i for i in resources.async_items() if str(i.get("url") or "").startswith(OLD_FRONTEND_URL + "/")]:
        await resources.async_delete_item(item["id"])
