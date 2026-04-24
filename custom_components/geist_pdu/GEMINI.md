# Geist PDU Implementation Details

## API Polling Strategy
- **Endpoints**:
  - `/api/sys`: Contains static system info (serial number, model, etc.). Call once during initialization.
  - `/api/dev` and `/api/state`: Contain dynamic sensor data. Poll repeatedly (default 30s).
- **Alarm Handling**: If `warnCount` or `alarmCount` in the `/api/state` response is greater than 0, detailed alarm trigger information can be fetched from `/api/alarm/trigger`.
- **Connection**: HTTP connections can offer significantly quicker response times than HTTPS for these devices. It is best practice to allow users to configure the full URL (e.g., using `CONF_URL`) rather than just the hostname.
