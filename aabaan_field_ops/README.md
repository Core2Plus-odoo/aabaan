# Aabaan Field Operations (`aabaan_field_ops`)

The guard-railed execution layer over `aabaan_visit_schedule` — rebuilt from
the `fm_fsm` concepts of the previous Aabaan-Services suite, standard-first on
native FSM tasks. "Fool-proof" here means: **the easy path is the correct
path, and the wrong path is blocked with a reason.**

## Dispatch

- **Preferred Technician** on the contract (sale order) — auto-assigned to
  every generated visit, routine and ad-hoc alike.
- **Field Service → Today's Visits** — the day list, grouped by technician.
- **Field Service → Dispatch Board** — open visits grouped by technician;
  the *Unassigned* filter catches visits without an owner.

## Guard-railed visit flow (buttons on the visit)

| Action | Blocked until | What it does |
|---|---|---|
| **Start Visit** | a technician is assigned | stamps Check-in, stage → In Progress |
| **Complete Visit** | started + *Treatment Carried Out* filled | stamps Check-out; if *Infestation Found* → auto-raises the unbilled follow-up (3-day rule) and stage → Follow-up Required, else → Completed |
| **Cancel Visit** | a cancellation reason is written | stage → Cancelled, reason logged to chatter |

Dragging a visit straight to Completed / In Progress / Cancelled on the
kanban (or a mass stage edit) is intercepted with a message pointing to the
right button. Guards apply only to typed Aabaan visits — imports and ordinary
tasks are untouched. Time on site is computed from the stamps.

## Escalation (daily cron)

Open visits past their SLA deadline (`x_sla_due`) or a day past their planned
start with no check-in get a To-Do activity on the technician (or project
manager) — once per visit, flagged `sla_escalated` and filterable.

## Field report

The *Field Report* tab on the visit holds findings (infestation flag,
treatment, chemicals/materials — what the municipality return needs),
check-in/out times, and the linked follow-up.

## What was deliberately NOT rebuilt (per the previous suite's own rule)

Worksheets (Studio-built, Priority 2), materials billing
(`industry_fsm_sale`/`industry_fsm_stock`), and timesheet billing are native
Odoo — configure, don't re-code.
