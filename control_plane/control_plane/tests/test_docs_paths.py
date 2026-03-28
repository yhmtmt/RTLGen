from pathlib import Path

from control_plane.services.docs_paths import canonicalize_proposal_path, resolve_proposal_dir, resolve_proposal_file


def test_resolve_proposal_prefers_canonical_path_when_available(tmp_path: Path) -> None:
    repo_root = tmp_path
    legacy_dir = repo_root / "docs" / "developer_loop" / "prop_demo_v1"
    canonical_dir = repo_root / "docs" / "proposals" / "prop_demo_v1"
    legacy_dir.mkdir(parents=True)
    canonical_dir.mkdir(parents=True)
    (legacy_dir / "proposal.json").write_text('{"proposal_id":"prop_demo_v1","title":"legacy"}\n', encoding="utf-8")
    (canonical_dir / "proposal.json").write_text('{"proposal_id":"prop_demo_v1","title":"canonical"}\n', encoding="utf-8")

    proposal_file = resolve_proposal_file(repo_root, proposal_id="prop_demo_v1")
    proposal_dir = resolve_proposal_dir(repo_root, proposal_id="prop_demo_v1")

    assert proposal_file == (canonical_dir / "proposal.json").resolve()
    assert proposal_dir == canonical_dir.resolve()


def test_resolve_proposal_maps_legacy_path_to_canonical_when_legacy_is_missing(tmp_path: Path) -> None:
    repo_root = tmp_path
    canonical_dir = repo_root / "docs" / "proposals" / "prop_demo_v2"
    canonical_dir.mkdir(parents=True)
    (canonical_dir / "proposal.json").write_text('{"proposal_id":"prop_demo_v2"}\n', encoding="utf-8")

    proposal_file = resolve_proposal_file(
        repo_root,
        proposal_path="docs/developer_loop/prop_demo_v2/proposal.json",
    )

    assert proposal_file == (canonical_dir / "proposal.json").resolve()


def test_canonicalize_proposal_path_returns_canonical_relative_file(tmp_path: Path) -> None:
    repo_root = tmp_path
    canonical_dir = repo_root / "docs" / "proposals" / "prop_demo_v3"
    canonical_dir.mkdir(parents=True)
    (canonical_dir / "proposal.json").write_text('{"proposal_id":"prop_demo_v3"}\n', encoding="utf-8")

    normalized = canonicalize_proposal_path(
        repo_root,
        proposal_path="docs/developer_loop/prop_demo_v3/proposal.json",
        proposal_id="prop_demo_v3",
    )

    assert normalized == "docs/proposals/prop_demo_v3/proposal.json"
