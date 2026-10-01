# Emergency triage escalation (n8n export)

A contact labelled `emergency` should leave the automation path and reach a senior agent. `n8n_emergency_escalation.json` is a prototype export shaped for n8n's import. It was written in this repository. It has not been imported into a running n8n instance, and it has not been executed against a live queue, a live classifier, or any contact-centre platform.

## What it does

1. A webhook named `Triage webhook` accepts `POST` on the path `triage-emergency-escalation`.
2. An IF node reads `urgency` from the JSON body (`$json.body.urgency`, or `$json.urgency` if the payload is already the object).
3. When that label equals `emergency`, a Set node writes `queue = senior_agent`.
4. Otherwise a Set node writes `queue = standard_automation_path`.

`emergency` is the urgent class in the public [MULTI-HEAD](https://github.com/ChristopherKiokoStrathmore/MULTI-HEAD-) label set (`low`, `medium`, `emergency`). The workflow does not call that model. A caller would POST a label the caller already has.

The file's `active` flag is `false`. Importing it does not turn the webhook on.

## Example payload shape

This is a shape example, not a record of a classification that was run for this repo:

```json
{"urgency": "emergency", "issue": "example_issue", "sentiment": "negative"}
```

## How to import

In n8n: menu, Import from File, choose `n8n_emergency_escalation.json`. The nodes use only the built-in Webhook, IF, and Set types, plus a sticky note. There are no credentials in the file.

Precision, recall, and the senior-agent cost live in `assumptions.yaml` as illustrative placeholders. This workflow does not apply those rates. It only branches on the label.
