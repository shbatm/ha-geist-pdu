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

from .entity import GeistPDUEntity, GeistPDUOutletEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from . import GeistPDUConfigEntry
    from .coordinator import GeistPDUDataUpdateCoordinator

# Measurement Key Mappings:
# 0: Voltage (V)
# 4: Current (A)
# 8: Real Power (W)
# 9: Apparent Power (VA)
# 10: Power Factor (%)
# 11: Energy (kWh)

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

    entities: list[SensorEntity] = []
    data = coordinator.data.get(device_id, {})

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
    for ent_key, ent_data in data.get("entity", {}).items():
        if ent_key.startswith("breaker") and "measurement" in ent_data:
            entities.append(
                GeistPDUSensor(coordinator, ent_key, "4", SensorEntityDescription(
                    key=f"{device_id}_{ent_key}_current",
                    name=f"Circuit {ent_key.replace('breaker', '')} Current",
                    native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                    device_class=SensorDeviceClass.CURRENT,
                    state_class=SensorStateClass.MEASUREMENT,
                ))
            )

    # --- Outlets ---
    outlets = data.get("outlet", {})
    for o_idx in outlets:
        entities.extend([
            GeistPDUOutletSensor(coordinator, o_idx, "8", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_power",
                name="Real Power",
                native_unit_of_measurement=UnitOfPower.WATT,
                device_class=SensorDeviceClass.POWER,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUOutletSensor(coordinator, o_idx, "9", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_apparent_power",
                name="Apparent Power",
                native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
                device_class=SensorDeviceClass.APPARENT_POWER,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUOutletSensor(coordinator, o_idx, "10", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_power_factor",
                name="Power Factor",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.POWER_FACTOR,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUOutletSensor(coordinator, o_idx, "11", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_energy",
                name="Energy",
                native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
            )),
            GeistPDUOutletSensor(coordinator, o_idx, "0", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_voltage",
                name="Voltage",
                native_unit_of_measurement=UnitOfElectricPotential.VOLT,
                device_class=SensorDeviceClass.VOLTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            )),
            GeistPDUOutletSensor(coordinator, o_idx, "4", SensorEntityDescription(
                key=f"{device_id}_outlet_{o_idx}_current",
                name="Current",
                native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                device_class=SensorDeviceClass.CURRENT,
                state_class=SensorStateClass.MEASUREMENT,
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
        if not data:
            return None

        # Path is either 'total0' or 'breaker0' etc.
        val_data = data.get("entity", {}).get(self._path, {})
        if not val_data:
            return None

        val = val_data.get("measurement", {}).get(self._measurement_key, {}).get("value")
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        return None

class GeistPDUOutletSensor(GeistPDUOutletEntity, SensorEntity):
    """Representation of a Geist PDU outlet sensor."""

    def __init__(
        self,
        coordinator: GeistPDUDataUpdateCoordinator,
        outlet_id: str,
        measurement_key: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the outlet sensor."""
        super().__init__(coordinator, outlet_id)
        self.entity_description = description
        self._measurement_key = measurement_key
        self._attr_unique_id = description.key

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        device_id = self.coordinator.device_id
        if not device_id:
            return None

        data = self.coordinator.data.get(device_id, {})
        if not data:
            return None

        val_data = data.get("outlet", {}).get(self._outlet_id, {})
        if not val_data:
            return None

        val = val_data.get("measurement", {}).get(self._measurement_key, {}).get("value")
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        return None
