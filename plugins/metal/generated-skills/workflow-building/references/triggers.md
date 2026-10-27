# Workflow Triggers

Use this reference when configuring how a workflow starts with `configure_workflow_trigger`. A workflow has exactly one trigger. Switching trigger type can destroy provisioned resources; see Provisioning Side-Effects.

## Trigger Types

### manual

The default. The workflow runs on demand, and `configure_workflow_input` fields are the run form. No trigger context is injected.

### email

Provisions an inbound email address; `emailPrefix` requests the local part. An incoming email injects a fixed input context: `input` (the body), `subject`, `from`, and `attachments` (data entity IDs for the attachments). Reference these as `.Input.input`, `.Input.subject`, and so on.

### event

Fires on a platform event. `eventName` is the event to listen for (for example `deal_create`); query `list_workflow_building_options` kind `events` for the valid names and the filter fields each supports. An optional `eventFilter` has `match` (`all` or `any`) and `conditions` (each currently an `eq` on an event field). `triggerer` assigns the org member to whom event runs are attributed; omit it to preserve the saved value or use `null` to clear it. The event injects context addressable as `.Input.event.name`, `.Input.event.resourceId`, and `.Input.event.resourceType`. `.Input.event.changes` appears when the source event carries changes; it is an ordered array of `{field, old?, new}` objects. A workflow that a workflow run triggered does not re-trigger itself.

### schedule

Runs on a cadence. `schedules` contains one to 25 schedules; edit a schedule by its `id` to preserve it. Each schedule has its own cadence, static per-run `input`, `triggerer`, and `enabled` flag. Each schedule sets either `intervalMinutes` or a `frequency` of `hourly`, `daily`, or `weekly` with `timeOfDay` (`HH:MM`, required for daily and weekly), `dayOfWeek` (required for weekly), and `timezone` (IANA, default UTC). Declared input fields (`configure_workflow_input`) plus a schedule's static `input` are the supported way to give each schedule its own input values with manual-run defaults. Configure fields directly under the schedule trigger; no trigger flip is needed.

`intervalMinutes` passes a shape check of 5 to 525600. A second gate rejects values below 30 for every org except one specifically exempted, so treat 30 as the general floor. A smaller value is rejected with a message that states the 30-minute floor and does not identify the exempt org.

### webhook

Provisions an authenticated HTTP endpoint at `POST /webhooks/workflows/:slug`. The URL and a secret preview are returned as transient fields on the trigger (`webhookUrl`, `webhookSecretPreview`); they are not persisted on the definition. The request injects input at `.Input.webhook.payload`, `.Input.webhook.headers`, and `.Input.webhook.query`.

- `signatureScheme` is `shared_secret` (default) or `hmac_sha256`. `signatureHeader` selects a custom authentication header.
- Shared-secret authentication defaults to `X-Metal-Webhook-Secret`; with that default header, `Authorization: Bearer <secret>` also works.
- HMAC authentication defaults to `X-Hub-Signature` and verifies the raw request body with HMAC-SHA256. The canonical header value is `sha256=<hex digest>`.
- Editing authentication while staying on `webhook` keeps the endpoint and updates its auth configuration.

## Pausing

An enabled automatic trigger on a non-deprecated organization workflow can dispatch when its normal trigger conditions or schedule timing are satisfied.

- `enabled` is a tri-state. Absent or `true` means the trigger fires; only an explicit `false` pauses it. Omitting the field on a write leaves the stored value unchanged.
- For `email`, `event`, and `webhook`, `enabled` sits on the trigger. For `schedule`, it sits on each element of `schedules`, so pausing one schedule leaves its siblings running. A schedule trigger has no trigger-level `enabled`.
- Pausing does not block a manual run and does not change `isExecutable`, which reports deprecation only.
- When every schedule is paused, or a non-schedule trigger is paused, saving surfaces the advisory `trigger_paused`. This reports stored state, not a defect; do not clear it by re-enabling unless the user asks.
- Global workflows never fire automatically, regardless of their trigger and pause flags.

## Provisioning Side-Effects

- Switching away from `email` or `webhook` deletes the inbound address or webhook endpoint. Switching back provisions a fresh one with a new address, or a new URL and secret, so external callers and senders must be updated.
- Staying on the same trigger type keeps the linked resource.
- An email prefix already in use surfaces as `address_in_use` on `trigger.emailPrefix`.
- Switching away from `schedule` deletes its schedules; switching back mints new schedule ids and clears per-schedule triggerers and static input.
- Re-submitting an unchanged trigger is a no-op success.

## Trigger Context And Templates

A template that references trigger context the current trigger does not provide surfaces `trigger_context_mismatch` (an error code; see `building-tools.md`). Match the referenced `.Input` keys to the trigger type: manual inputs, the email fields, the event context, or the webhook payload paths above.
