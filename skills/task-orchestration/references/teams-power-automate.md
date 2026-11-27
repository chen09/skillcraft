# Teams and Power Automate pilot

Use one internal standard Teams channel, a control store, and one business ledger. Power Automate captures selected messages and optionally sends the original-thread reply. The operator or agent uses the skill to control task state and ledger updates.

## Set up the environment

Record the Microsoft 365 tenant, target Power Platform environment, allowed team/channel IDs, flow owners and connection identities, control store, and ledger destination. Use scoped connections and storage approved for the message content. Keep credentials and tenant-specific values out of the skill.

Create the selected-message flow in the target tenant's Default environment. Check that Power Automate Actions is allowed and that the flow is shared with intended internal users. Test with an intended operator. The connector has restrictions for guests and external users. [Selected-message setup](https://learn.microsoft.com/en-us/power-automate/trigger-flow-teams-message), [Teams connector](https://learn.microsoft.com/en-us/connectors/teams/).

If you have a solution-aware deployment package, import into the target environment and rebind its connections and environment values. Otherwise build the two flows below. This skill includes a configuration recipe. [Flow solutions](https://learn.microsoft.com/en-us/power-automate/create-flow-solution), [Environment variables](https://learn.microsoft.com/en-us/power-automate/environment-variables).

## Flow A: capture

1. Create an instant flow with the Teams **For a selected message** trigger. Map the direct source link, sender and selecting operator when available, and permitted plain-text excerpt.
2. Inspect an actual test trigger run or approved message details to resolve tenant, team, channel, selected message ID, and thread root ID. In the first pilot, select top-level channel messages so the selected ID is the root ID. Enable selecting replies for automatic return only after verifying how the root is obtained. Preserve the source link and use manual routing when there is no verified root.
3. Check the channel allowlist and submit the source event to the control store or the serialized writer's staging inbox. Use source type, tenant, team, channel, and selected message ID as key components. Repeated capture should return or retain the same intake event. This flow does not decide which task to create.
4. Have the controller triage the event and create or link the chosen ledger record. Verify the completed work, then read back the ledger update before preparing the reply.

## Flow B: reply

1. Create a restricted instant flow for approved reply operations. Read the exact authorized body, destination, and operation key from the control store or have the controller pass an approved immutable snapshot. Verify the allowlist, thread root, and any required ledger writeback receipt. Gate the Teams action with a one-time dispatch claim for the approved operation. In an atomic store, Flow B claims and posts only when its conditional transition succeeds. With a single writer, have that writer reserve and invoke the send once. If the flow cannot independently reject a replay, restrict invocation to that writer and reconcile from there. Do not enable a standalone rerunnable send entry point in this profile.
2. Use **Reply with a message in a channel** (`ReplyWithMessageToConversation`). Select the approved sender identity and bind the team, channel, root message ID, and approved text. Use the root ID for the original thread rather than the ID of a selected child reply. Disable automatic retry for the send action when supported.
3. Return or record the Flow run ID and Teams reply ID/link when available. Verify the visible original thread, the expected text, and any task link. Persist verification through the controller. If the run times out or no receipt is available, reconcile the run and original thread before retrying.
4. If the original thread cannot be addressed through the connector, hand the approved draft and source link to an authorized operator for manual reply and receipt capture. Do not fall back to a new channel post. [Teams reply action](https://learn.microsoft.com/en-us/connectors/teams/#reply-with-a-message-in-a-channel).

## Verify the first environment

With an approved sample in a sandbox, select the same message twice and check that it yields one intake event. Triage it, create or link one ledger item, pause and resume, and verify writeback to that same item. Send one approved reply and check its location and task link. Submit the same output again through the controller or guarded Flow B entry point, and verify no second reply appears. Test a missing thread ID and an uncertain send state without sending another message.

Record the flow runs, source link, task ID/link, reply receipt, and who verified each step. Keep simulated recovery evidence separate from live delivery evidence.
