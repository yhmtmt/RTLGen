"""Shared enums for the control-plane relational model."""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    pass


class LayerName(_StrEnum):
    LAYER1 = "layer1"
    LAYER2 = "layer2"
    META = "meta"


class FlowName(_StrEnum):
    OPENROAD = "openroad"


class WorkItemState(_StrEnum):
    DRAFT = "draft"
    READY = "ready"
    LEASED = "leased"
    RUNNING = "running"
    ARTIFACT_SYNC = "artifact_sync"
    AWAITING_REVIEW = "awaiting_review"
    MERGED = "merged"
    FAILED = "failed"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"


class LeaseStatus(_StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    REVOKED = "revoked"


class ExecutorType(_StrEnum):
    INTERNAL_WORKER = "internal_worker"
    EXTERNAL_PR = "external_pr"
    AGENT_ASSISTED_WORKER = "agent_assisted_worker"


class RunStatus(_StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    TIMED_OUT = "timed_out"


class ArtifactStorageMode(_StrEnum):
    TRANSIENT = "transient"
    REPO = "repo"


class GitHubLinkState(_StrEnum):
    NONE = "none"
    BRANCH_CREATED = "branch_created"
    PR_OPEN = "pr_open"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"


class QueueReconciliationDirection(_StrEnum):
    IMPORT = "import"
    EXPORT = "export"


class QueueReconciliationStatus(_StrEnum):
    APPLIED = "applied"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
    ERROR = "error"
