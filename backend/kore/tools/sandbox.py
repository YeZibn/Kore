"""Filesystem sandbox helpers for file tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathCheck:
    """Result of resolving a user-provided path against the workspace sandbox."""

    requested_path: str
    resolved_path: Path
    workspace_root: Path
    inside_workspace: bool


class ConfirmationRequiredError(PermissionError):
    """Raised when a tool wants to access a path outside the workspace."""

    def __init__(self, check: PathCheck) -> None:
        super().__init__(
            f"Path '{check.resolved_path}' is outside workspace '{check.workspace_root}' "
            "and requires user confirmation."
        )
        self.check = check


class FileSandbox:
    """First-layer filesystem boundary based on a user-selected workspace root."""

    def __init__(self, workspace_root: Path | str) -> None:
        self.workspace_root = Path(workspace_root).expanduser().resolve()

    def check_path(self, path: str | Path, *, require_confirmation: bool = True) -> PathCheck:
        """Resolve a path and optionally require confirmation if it leaves the workspace."""
        requested_path = str(path)
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate

        resolved = candidate.resolve()
        inside_workspace = self._is_relative_to(resolved, self.workspace_root)
        check = PathCheck(
            requested_path=requested_path,
            resolved_path=resolved,
            workspace_root=self.workspace_root,
            inside_workspace=inside_workspace,
        )
        if require_confirmation and not inside_workspace:
            raise ConfirmationRequiredError(check)
        return check

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
