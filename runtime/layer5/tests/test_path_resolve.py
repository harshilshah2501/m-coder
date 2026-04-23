from runtime.layer5.retrieval.path_resolve import paths_match_workspace, resolve_owner_path_in_index


def test_paths_match_workspace_repeated_motadata_prefix():
    assert paths_match_workspace("motadata/motadata/src/Main.java", "src/Main.java")


def test_resolve_owner_path_in_index_basename_fallback():
    ps = {"legacy/pkg/Special.java"}
    assert resolve_owner_path_in_index(
        "motadata/src/org/x/Special.java",
        ps,
        owner_class=None,
    ) == "legacy/pkg/Special.java"
