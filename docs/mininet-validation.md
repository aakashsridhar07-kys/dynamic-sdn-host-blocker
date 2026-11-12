# Mininet validation record

## Environment

- Mininet subnet: `10.20.0.0/24`
- h1 / Client A: `10.20.0.1`
- h2 / Client B: `10.20.0.2`
- h3 / Server: `10.20.0.10`
- OpenFlow: 1.3
- OS-Ken OpenFlow listener: `127.0.0.1:6653`
- Controller management API: `127.0.0.1:8080`

## Demonstrated results

| Test | Observed result |
|---|---|
| Controller connection | OVS reported `is_connected: true` |
| Mininet connectivity | `pingall` succeeded after controller startup |
| TCP socket request | h1 received an `ok` response from h3 |
| UDP socket request | h1 received an `ok` response from h3 |
| SYN detection | Alert reported source `10.20.0.1` |
| Event logging | Detection record appeared in `data/mininet_events.jsonl` |
| Automatic enforcement | Monitor reported `[BLOCKED] 10.20.0.1` |
| Selective blocking | h1 lost access while h2 remained reachable |
| Temporary rule expiry | h1 connectivity returned after the test block duration |

## Test configuration versus committed configuration

A separate local-only configuration named
`config/mininet-auto-test.json` was used for the short functional
enforcement test. It used a lower SYN threshold and a 30-second block so the
automatic response and recovery could be demonstrated without waiting for
the normal production-style lab settings.

That temporary test file is not part of the repository. The committed
`config/mininet-thresholds.json` remains:

- Lab CIDR: `10.20.0.0/24`
- Ignored IP: `10.20.0.10` (server)
- SYN threshold: 30 per second
- Rolling window: 5 seconds
- Consecutive qualifying windows: 2
- Block duration: 120 seconds
- Controller API: `http://127.0.0.1:8080`

The high-sensitivity test configuration is for controlled functional
verification only. It is not a recommended production threshold.

## Remaining work

- Test UDP explicitly during an active source-IP block and after recovery.
- Run the complete automated unit-test suite on the target VM.
- Capture final screenshots and performance measurements for the report.
- Reconcile SQLite blocklist expiry records with controller state.
