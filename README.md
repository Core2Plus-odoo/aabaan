# aabaan

Custom Odoo 19 addons for the Aabaan Classic Building Cleaning L.L.C. build
(`core2plus-odoo-aabaan.odoo.com`, Odoo.sh), maintained by C2P Consultants
FZC LLC.

| Module | Purpose |
| --- | --- |
| `aabaan_visit_schedule` | Visit Schedule Generator: creates and safely regenerates AMC maintenance visits (Field Service tasks) from confirmed contracts, incl. Dubai LO 11 F&B cadence and unbilled follow-up/complaint visits. |
| `aabaan_quotation_report` | Branded quotation/contract PDF in the Aaban Services letterhead style (angular header, orange line-items table, articles, signatures, offices footer), replacing the default sale report. |
| `aabaan_ceo_dashboard` | Live, drillable CEO dashboard (OWL client action): contract book by service line/emirate, renewal pipeline with past-end-of-term alert, visit SLA metrics, pipeline and receivables — every figure opens its underlying records. |
| `aabaan_field_ops` | Guard-railed field-operations layer: technician dispatch (Dispatch Board, Today's Visits), enforced Start/Complete/Cancel visit flow with field report, automatic follow-up on infestation, daily SLA/overdue escalation cron. |

Secrets policy: API keys are supplied via environment variables (e.g.
`ODOO_API_KEY`) and are never committed to this repository.
