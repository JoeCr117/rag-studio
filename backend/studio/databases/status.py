"""Whether a source's content in a database matches the source on disk."""

from enum import StrEnum


class AssignmentStatus(StrEnum):
    SYNCED = "synced"
    CHANGED = "changed"
    NEVER_SYNCED = "never_synced"
    MISSING = "missing"
    DISCONNECTED = "disconnected"


def assignment_status(
    connected: bool, found: bool, source_fingerprint: str, synced_fingerprint: str
) -> AssignmentStatus:
    if not connected:
        return AssignmentStatus.DISCONNECTED
    if not found or not source_fingerprint:
        return AssignmentStatus.MISSING
    if not synced_fingerprint:
        return AssignmentStatus.NEVER_SYNCED
    return AssignmentStatus.SYNCED if synced_fingerprint == source_fingerprint else AssignmentStatus.CHANGED


def database_warnings(needs_rebuild: bool, statuses: list[AssignmentStatus]) -> list[str]:
    """Why a database's contents no longer match its connected sources, in the order to act on them."""
    warnings = []
    if needs_rebuild:
        warnings.append("Settings changed since the vectors were built: Sync all rebuilds this database.")
    if AssignmentStatus.DISCONNECTED in statuses:
        warnings.append("A disconnected source still has chunks here: Sync all removes them.")
    if any(status in (AssignmentStatus.CHANGED, AssignmentStatus.NEVER_SYNCED) for status in statuses):
        warnings.append("Some connected sources are not synced.")
    return warnings
