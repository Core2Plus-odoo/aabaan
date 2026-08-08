# Part of the Aabaan Odoo build by C2P Consultants FZC LLC.
{
    'name': 'Aabaan Field Operations',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Guard-railed visit execution: dispatch, start/complete flow, auto follow-ups, SLA escalation',
    'description': """
The execution layer over the Aabaan visit schedule, designed to be fool-proof:

- Preferred technician on the contract; every generated visit is auto-assigned.
- Start Visit is blocked until a technician is assigned and stamps the check-in.
- Complete Visit is blocked until the field report (treatment, chemicals) is
  filled, stamps the check-out, and — when infestation is found — raises the
  unbilled follow-up visit with its SLA automatically (the 3-day rule).
- Cancelling requires a reason; dragging a visit straight to Completed or
  Cancelled on the kanban is intercepted.
- A daily cron escalates SLA breaches and visits a day past plan as activities
  on the technician (once per visit).
- Dispatch Board (grouped by technician) and Today's Visits menus under
  Field Service.

Rebuilt from the fm_fsm concepts of the previous Aabaan-Services suite,
standard-first on native FSM tasks.
""",
    'author': 'C2P Consultants FZC LLC',
    'license': 'OPL-1',
    'depends': [
        'aabaan_visit_schedule',
    ],
    'data': [
        'data/cron.xml',
        'views/project_task_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
