<!-- BEGIN GENERATED FIGURES -->

The figures in this block are written by `python -m care_roi` from `assumptions.yaml` and the Bitext intent file. Currency is KES (illustrative). Every input is an illustrative placeholder, not a real operator figure. Per-contact costs are shown to 4 decimal places. Annual amounts are the exact product, then rounded to the cent, so a hand product of the rounded unit costs can differ by a few cents.

### Headline scenario results

Baseline voice-agent cost per contact: 111.0476 KES (illustrative).
Baseline annual operating cost: 13,325,714.29 KES (illustrative).

Bot programme at base containment, cost per contact: 76.5173 KES (illustrative).
Bot programme annual operating saving versus the voice baseline: 4,143,640.00 KES (illustrative).
Bot programme net annual benefit after the annual licence: 3,543,640.00 KES (illustrative).
Bot programme payback: 8.47 months.
Bot programme year-1 ROI: 0.4175.
Bot programme year-1 net cash (net annual benefit minus build cost): 1,043,640.00 KES (illustrative).

Low containment (base minus the delta in assumptions.yaml), payback: 14.24 months. Year-1 ROI: -0.1571.
High containment (base plus the delta), payback: 5.92 months. Year-1 ROI: 1.0278.

Triage routing treats the public MULTI-HEAD urgency label `emergency` as the urgent class. Precision and recall are assumptions. That repository documents no accuracy figure, and none is used here as a measurement.

Assumed emergency prevalence 0.0800, recall 0.7500, precision 0.4000.
Per contact, the implied rates are true positive 0.0600, false positive 0.0900, false negative 0.0200, true negative 0.8300, predicted emergency 0.1500.
On the assumed annual volume, that is 7,200 true positives, 10,800 false positives, 2,400 false negatives, and 18,000 contacts sent to a senior agent.
Triage scenario cost per contact: 95.1468 KES (illustrative). Assumed quality value for the year: 1,200,000.00 KES (illustrative). Net annual benefit: 2,328,094.00 KES (illustrative). Payback: 14.95 months. Year-1 ROI: -0.1972.
The same triage path with the assumed quality value set to zero has net annual benefit 1,128,094.00 KES (illustrative) and payback 30.85 months.

### Cost to serve one completed contact

These are unit costs with no spill. A contained bot contact pays only the bot unit cost. A miss pays the bot unit cost and one voice-agent contact. Staffed chat is the chat channel in the unit-cost table. The chat bot row is the unstaffed platform cost used when a contact is contained on chat.

| Channel | Cost per contact (KES (illustrative)) |
| --- | ---: |
| Agent (voice) | 111.0476 |
| IVR | 4.4000 |
| USSD bot | 1.2000 |
| Chat (staffed) | 133.0000 |
| Chat bot (unstaffed) | 3.0000 |
| Senior agent | 200.7143 |

### Which Bitext intents the rule marks as automation candidates

Rule, applied in this order:

- 1. If the Bitext category is COMPLAINTS, the class is human_required (clause category_complaints).
- 2. If the intent is customer_service, human_agent, activate_phone, deactivate_phone, install_internet, cancel_plan, or change_provider, or the intent name starts with dispute_, the class is human_required (clause explicit_human_or_dispute).
- 3. If the intent name starts with check_, or the intent is invoices or payment_methods, the class is lookup (clause lookup_name).
- 4. If the intent is pay, schedule_payments, set_usage_limits, activate_roaming, activate_call_management_services, deactivate_call_management_services, change_plan, or sign_up_for_plan, the class is structured_transaction (clause explicit_transaction).
- 5. Any other intent raises an error. A new Bitext intent is not classified by a default.

The taxonomy file has 26 intents and 26000 training examples, 1000 per intent. That balance is how the Bitext training set was built. It is not demand. Demand shares below come from `demand_weight_by_intent` in assumptions.yaml.

Upstream file sha256 recorded in `data/bitext_meta.json`: `0905820a880783d1a00f92d4f519488479f9eefe770cbfb5737f9462135d6c12`.

| Automation class | Intents | Share of intent names | Assumed demand share | Cost per contact under base routing |
| --- | ---: | ---: | ---: | ---: |
| lookup | 7 | 0.2692 | 0.4000 | 40.3467 |
| structured_transaction | 8 | 0.3077 | 0.2650 | 86.9067 |
| human_required | 11 | 0.4231 | 0.3350 | 111.4876 |

Intent detail is in [reports/intent_classification.csv](reports/intent_classification.csv). `n_examples` in that file is the training-set count. `demand_share` is the assumption weight divided by the sum of weights.

### Scenario table

| Scenario | Cost per contact | Annual operating saving | Assumed quality value | Net annual benefit | Payback (months) | Year-1 ROI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline: every contact on a voice agent | 111.0476 | 0.00 | 0.00 | 0.00 | not defined | not defined |
| Bot programme, low containment | 88.4882 | 2,707,128.00 | 0.00 | 2,107,128.00 | 14.24 | -0.1571 |
| Bot programme, base containment | 76.5173 | 4,143,640.00 | 0.00 | 3,543,640.00 | 8.47 | 0.4175 |
| Bot programme, high containment | 63.8023 | 5,669,434.29 | 0.00 | 5,069,434.29 | 5.92 | 1.0278 |
| Bot programme plus emergency routing, with assumed quality value | 95.1468 | 1,908,094.00 | 1,200,000.00 | 2,328,094.00 | 14.95 | -0.1972 |
| Bot programme plus emergency routing, quality value set to zero | 95.1468 | 1,908,094.00 | 0.00 | 1,128,094.00 | 30.85 | -0.6110 |

Full columns, including licence and build cost, are in [reports/scenarios.csv](reports/scenarios.csv).

### Sensitivity

The chart swings one assumption at a time by `sensitivity_relative_swing` and recomputes year-1 net cash for the bot programme at base containment. Lookup USSD offer moves against the voice-agent share of that class so the shares still sum to 1. A move that would push a share outside [0, 1] is clamped, and the clamp is flagged in [reports/sensitivity.csv](reports/sensitivity.csv).

Base year-1 net cash on the chart: 1,043,640.00 KES (illustrative).

![Tornado chart of year-1 net cash when each assumption moves on its own](reports/charts/roi_sensitivity_tornado.png)

The same chart as HTML: [reports/charts/roi_sensitivity_tornado.html](reports/charts/roi_sensitivity_tornado.html).

The cash columns are the result at the low input and the result at the high input. For wages, handle time, build cost, and licence, a higher input produces lower year-1 net cash.

| Assumption moved | Input low | Input high | Clamped | Year-1 net cash at low input | Year-1 net cash at high input |
| --- | ---: | ---: | --- | ---: | ---: |
| Voice-agent handle time | 6.4 | 9.6 | no | 188,262.40 | 1,899,017.60 |
| Annual contacts | 96000 | 144000 | no | 214,912.00 | 1,872,368.00 |
| Monthly productive hours | 112 | 168 | no | 1,997,320.00 | 407,853.33 |
| Voice-agent monthly wage | 64000 | 96000 | no | 280,696.00 | 1,806,584.00 |
| Lookup USSD containment | 0.56 | 0.84 | no | 446,648.00 | 1,640,632.00 |
| Bot build cost | 2000000 | 3000000 | no | 1,543,640.00 | 543,640.00 |
| Lookup USSD offer share | 0.64 | 0.85 | high input | 455,864.00 | 1,227,320.00 |
| Wage burden rate | 0.24 | 0.36 | no | 867,576.00 | 1,219,704.00 |
| Bot annual licence | 480000 | 720000 | no | 1,163,640.00 | 923,640.00 |
| Transaction USSD containment | 0.32 | 0.48 | no | 958,888.46 | 1,128,391.54 |
| USSD cost per session | 0.8 | 1.2 | no | 1,055,145.60 | 1,032,134.40 |

### Assumptions

Every number in this file is an illustrative placeholder, not a real operator figure.

Currency code: KES. Currency label: KES (illustrative).

| Assumption | Value | Label |
| --- | ---: | --- |
| `volume.annual_contacts` | 120000 | illustrative placeholder, not a real operator figure |
| `wages.voice_agent_monthly_wage` | 80000 | illustrative placeholder, not a real operator figure |
| `wages.chat_agent_monthly_wage` | 70000 | illustrative placeholder, not a real operator figure |
| `wages.senior_agent_monthly_wage` | 120000 | illustrative placeholder, not a real operator figure |
| `wages.burden_rate` | 0.30 | illustrative placeholder, not a real operator figure |
| `wages.monthly_productive_hours` | 140 | illustrative placeholder, not a real operator figure |
| `handle_time_minutes.voice_agent` | 8 | illustrative placeholder, not a real operator figure |
| `handle_time_minutes.senior_agent` | 10 | illustrative placeholder, not a real operator figure |
| `handle_time_minutes.live_chat` | 12 | illustrative placeholder, not a real operator figure |
| `handle_time_minutes.ivr` | 3 | illustrative placeholder, not a real operator figure |
| `channel_variable.voice_telco_per_minute` | 1.50 | illustrative placeholder, not a real operator figure |
| `channel_variable.ivr_per_minute` | 0.80 | illustrative placeholder, not a real operator figure |
| `channel_variable.ivr_platform_per_contact` | 2.00 | illustrative placeholder, not a real operator figure |
| `channel_variable.ussd_per_session` | 1.00 | illustrative placeholder, not a real operator figure |
| `channel_variable.ussd_sessions_per_contact` | 1.20 | illustrative placeholder, not a real operator figure |
| `channel_variable.live_chat_platform_per_contact` | 3.00 | illustrative placeholder, not a real operator figure |
| `channel_variable.chat_bot_platform_per_contact` | 3.00 | illustrative placeholder, not a real operator figure |
| `routing_share.lookup.ussd_bot` | 0.80 | illustrative placeholder, not a real operator figure |
| `routing_share.lookup.chat_bot` | 0.10 | illustrative placeholder, not a real operator figure |
| `routing_share.lookup.ivr` | 0.05 | illustrative placeholder, not a real operator figure |
| `routing_share.lookup.voice_agent` | 0.05 | illustrative placeholder, not a real operator figure |
| `routing_share.structured_transaction.ussd_bot` | 0.30 | illustrative placeholder, not a real operator figure |
| `routing_share.structured_transaction.chat_bot` | 0.20 | illustrative placeholder, not a real operator figure |
| `routing_share.structured_transaction.ivr` | 0.10 | illustrative placeholder, not a real operator figure |
| `routing_share.structured_transaction.voice_agent` | 0.40 | illustrative placeholder, not a real operator figure |
| `routing_share.human_required.ussd_bot` | 0.00 | illustrative placeholder, not a real operator figure |
| `routing_share.human_required.chat_bot` | 0.00 | illustrative placeholder, not a real operator figure |
| `routing_share.human_required.ivr` | 0.10 | illustrative placeholder, not a real operator figure |
| `routing_share.human_required.voice_agent` | 0.90 | illustrative placeholder, not a real operator figure |
| `containment_rate.lookup.ussd_bot` | 0.70 | illustrative placeholder, not a real operator figure |
| `containment_rate.lookup.chat_bot` | 0.65 | illustrative placeholder, not a real operator figure |
| `containment_rate.lookup.ivr` | 0.50 | illustrative placeholder, not a real operator figure |
| `containment_rate.structured_transaction.ussd_bot` | 0.40 | illustrative placeholder, not a real operator figure |
| `containment_rate.structured_transaction.chat_bot` | 0.45 | illustrative placeholder, not a real operator figure |
| `containment_rate.structured_transaction.ivr` | 0.20 | illustrative placeholder, not a real operator figure |
| `containment_rate.human_required.ussd_bot` | 0.00 | illustrative placeholder, not a real operator figure |
| `containment_rate.human_required.chat_bot` | 0.00 | illustrative placeholder, not a real operator figure |
| `containment_rate.human_required.ivr` | 0.00 | illustrative placeholder, not a real operator figure |
| `containment_scenario_delta` | 0.20 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.check_usage` | 140 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.invoices` | 90 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.check_mobile_payments` | 50 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.payment_methods` | 30 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.check_excess_data_charges` | 40 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.check_signal_coverage` | 35 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.check_cancellation_fee` | 15 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.pay` | 100 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.schedule_payments` | 25 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.set_usage_limits` | 20 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.change_plan` | 45 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.sign_up_for_plan` | 30 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.activate_roaming` | 20 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.activate_call_management_services` | 15 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.deactivate_call_management_services` | 10 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.report_problem` | 80 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.report_poor_signal_coverage` | 40 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.dispute_invoice` | 35 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.get_compensation` | 20 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.human_agent` | 45 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.customer_service` | 30 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.cancel_plan` | 25 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.change_provider` | 15 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.activate_phone` | 15 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.deactivate_phone` | 10 | illustrative placeholder, not a real operator figure |
| `demand_weight_by_intent.install_internet` | 20 | illustrative placeholder, not a real operator figure |
| `triage.prevalence` | 0.08 | illustrative placeholder, not a real operator figure |
| `triage.recall` | 0.75 | illustrative placeholder, not a real operator figure |
| `triage.precision` | 0.40 | illustrative placeholder, not a real operator figure |
| `triage.value_per_true_positive` | 250 | illustrative placeholder, not a real operator figure |
| `triage.penalty_per_false_negative` | 250 | illustrative placeholder, not a real operator figure |
| `investment.bot_build_cost` | 2500000 | illustrative placeholder, not a real operator figure |
| `investment.bot_annual_licence` | 600000 | illustrative placeholder, not a real operator figure |
| `investment.triage_build_cost` | 400000 | illustrative placeholder, not a real operator figure |
| `investment.triage_annual_licence` | 180000 | illustrative placeholder, not a real operator figure |
| `sensitivity_relative_swing` | 0.20 | illustrative placeholder, not a real operator figure |

<!-- END GENERATED FIGURES -->
