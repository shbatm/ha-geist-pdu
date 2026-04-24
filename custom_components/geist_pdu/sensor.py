"""Support for Geist PDU sensors."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)

from .entity import GeistPDUEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import GeistPDUConfigEntry
    from .coordinator import GeistPDUDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: GeistPDUConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Geist PDU sensors based on a config entry."""
    coordinator = entry.runtime_data
    device_id = coordinator.device_id
    if not device_id:
        return

    entities: list[GeistPDUSensor] = []
    data = coordinator.data[device_id]

    # --- Totals ---
    total_data = data.get("entity", {}).get("total0", {})
    if total_data:
        entities.extend([
            GeistPDUSensor(coordinator, "total0", "0", SensorEntityDescription(
                key=f"{device_id}_total_power",
                name="Total Real Power",
                native_unit_of_measurement=UnitOfPower.WATT,
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUSensor(coordinator, "total0", "1", SensorEntityDescription(
                key=f"{device_id}_total_apparent_power",
                name="Total Apparent Power",
                native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
                device_class=SensorDeviceClass.APPARENT_POWER,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUSensor(coordinator, "total0", "2", SensorEntityDescription(
                key=f"{device_id}_total_power_factor",
                name="Total Power Factor",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.POWER_FACTOR,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUSensor(coordinator, "total0", "3", SensorEntityDescription(
                key=f"{device_id}_total_energy",
                name="Total Energy",
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
            )),
        ])

    # --- Phase ---
    phase_data = data.get("entity", {}).get("phase0", {})
    if phase_data:
        entities.extend([
            GeistPDUSensor(coordinator, "phase0", "0", SensorEntityDescription(
                key=f"{device_id}_voltage",
                name="Voltage",
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                device_class=SensorDeviceClass.VOLTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUSensor(coordinator, "phase0", "4", SensorEntityDescription(
                key=f"{device_id}_current",
                name="Current",
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
            )),
        ])

    # --- Breakers ---
    for b_idx in range(4): # Check for up to 4 breakers
        b_key = f"breaker{b_idx}"
        if b_key in data.get("entity", {}):
            entities.append(
                GeistPDUSensor(coordinator, b_key, "4", SensorEntityDescription(
                    key=f"{device_id}_{b_key}_current",
                    name=f"Circuit {b_idx + 1} Current",
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    device_class=SensorDeviceClass.CURRENT,
                    state_class=SensorStateClass.MEASUREMENT,
                ))
            )

    # --- Outlets ---
    outlets = data.get("outlet", {})
    for o_idx, o_data in outlets.items():
        label = o_data.get("label", f"Outlet {int(o_idx) + 1}")
        entities.extend([
            GeistPDUSensor(coordinator, f"outlet/{o_idx}", "8", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_power",
                name=f"{label} Power",
                native_unit_of_measurement=UnitOfPower.WATT,
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUSensor(coordinator, f"outlet/{o_idx}", "11", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_energy",
                name=f"{label} Energy",
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
            )),
        ])

    async_add_entities(entities)

class GeistPDUSensor(GeistPDUEntity, SensorEntity):
    """Representation of a Geist PDU sensor."""

    def __init__(
        self,
        coordinator: GeistPDUDataUpdateCoordinator,
        path: str,
        measurement_key: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._path = path
        self._measurement_key = measurement_key
        self._attr_unique_id = description.key

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        device_id = self.coordinator.device_id
        if not device_id:
            return None

        data = self.coordinator.data.get(device_id, {})

        # Path is either 'entity/total0' or 'outlet/0'
        parts = self._path.split("/")
        if len(parts) == 1:
            # entity case (e.g. breaker0)
            val_data = data.get("entity", {}).get(parts[0], {})
        else:
            # outlet case
            val_data = data.get(parts[0], {}).get(parts[1], {})

        val = val_data.get("measurement", {}).get(self._measurement_key, {}).get("value")
        if val is not None:
            try:
                return float(val)
            except ValueError:
                return None
        return None
