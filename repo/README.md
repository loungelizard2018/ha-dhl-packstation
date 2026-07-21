# DHL Packstation Capacity

Home Assistant custom integration for the DHL Location Finder capacity forecast. The data is a weekday-based statistical forecast, not a live fill level.

## Install with HACS
1. HACS → Custom repositories.
2. Add `https://github.com/loungelizard2018/ha-dhl-packstation` as **Integration**.
3. Download, restart Home Assistant, then add **DHL Packstation Capacity** under Devices & services.

## Card views
```yaml
type: custom:dhl-packstation-card
entity: sensor.YOUR_CAPACITY_SENSOR
view: full
```
Use `view: compact` or `view: row` for the other layouts.
