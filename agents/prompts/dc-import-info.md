# Ground dc-import-info investigations

Use the `dc-import-info` skill for this investigation.

Before presenting or executing a command:

1. Select the operation from the skill's route table.
2. Read the exact linked recipe during this turn.
3. Use only command forms, filenames, fields, and semantics established by that
   recipe or a reference it links.
4. Substitute placeholders only with values from the selected manifest,
   environment configuration, user prompt, or observed evidence.
5. If a required value is unresolved, stop and report it as `unresolved`.
   Never invent a resource, filename, field, or meaning from memory or a generic
   cloud convention.
6. Keep ET-output status separate from loader and serving status.
7. For each command, state the recipe ID or repository path that grounds it.
