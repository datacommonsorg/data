# Read-only identity and access

Support engineers use their own corporate identities and read-only IAM. Do not
distribute service-account keys or impersonate a service account by default.

Collection can require read/list/get permissions for Cloud Scheduler,
Workflows and executions, Batch jobs/tasks, Cloud Logging, Cloud Run services,
Cloud Storage objects, Cloud Build, Artifact Registry, and Spanner data.

Do not grant roles that permit Scheduler/Workflow/Batch execution, Cloud Run
invocation, Cloud Build mutation, Artifact Registry writes, Storage object
mutation, Spanner writes, Secret Manager access, or service-account token
creation.

Authenticate outside the skill. If `gcloud` or Application Default Credentials
are unavailable, report the missing setup and return partial repository
information. Every request must still use explicit project and location
arguments; ambient `gcloud` configuration is not an infrastructure source.
Application Default Credentials provide identity to Workflow and Spanner SDK
clients; they do not select the project, instance, or database.

Do not use MCP tools, IDE database connections, plugins, connectors, or their
configured resource values as a fallback. Do not modify or disable a user's
tool configuration; simply avoid those tools for this skill.

Skill instructions are defense in depth. IAM and execution-environment
permissions are the security boundary.
