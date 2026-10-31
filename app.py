import re
from pathlib import Path
import git
import streamlit as st
import pandas as pd
# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="CodeStory AI",
    page_icon="📖",
    layout="wide",
)
st.title("📖 CodeStory AI")
st.subheader("Understand your codebase through evidence, not guesses.")
st.write(
    "Investigate Git history, inspect code changes, and find evidence "
    "to understand how a codebase evolved."
)
st.caption(
    "Evidence-first repository investigation | No paid AI API required"
)
# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------
MAX_COMMITS = 200
MAX_SOURCE_FILES = 3000
MAX_FILE_SIZE = 500_000
MAX_DIFF_CHARS = 100_000
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "build",
    "coverage",
    ".idea",
    ".vscode",
}
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".c", ".cpp", ".h", ".hpp",
    ".go", ".rs", ".php", ".rb", ".swift",
    ".kt", ".kts", ".cs", ".html", ".css",
    ".scss", ".json", ".yaml", ".yml",
    ".toml", ".md", ".sql", ".sh",
    ".xml", ".gradle", ".txt",
}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)(api[_-]?key|secret|password|access[_-]?token)"
        r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    ),
]
# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def get_repository(path_text):
    """Open a local Git repository without searching parent folders."""
    folder = Path(path_text).expanduser().resolve()
    if not folder.is_dir():
        raise ValueError("The supplied path is not an existing folder.")
    try:
        repository = git.Repo(
            str(folder),
            search_parent_directories=False,
        )
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        raise ValueError(
            "This folder is not a Git repository. "
            "Choose a folder containing a valid .git directory."
        )
    if repository.bare:
        raise ValueError("Bare Git repositories are not supported.")
    return repository
def safe_commit_message(commit):
    """Return the commit message without surrounding whitespace."""
    return commit.message.strip()
def get_commit_table(commits):
    """Create a table of observable commit metadata."""
    rows = []
    for commit in commits:
        rows.append(
            {
                "Short hash": commit.hexsha[:8],
                "Date": commit.committed_datetime.strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "Author": commit.author.name or "Unknown",
                "Message": safe_commit_message(commit),
            }
        )
    return pd.DataFrame(rows)
def get_commit_diff(repository, commit):
    """
    Return the commit's patch against its first parent.
    The initial commit is compared with an empty tree.
    """
    if commit.parents:
        parent = commit.parents[0]
        diff_text = repository.git.diff(
            "--no-ext-diff",
            "--no-color",
            "--find-renames",
            parent.hexsha,
            commit.hexsha,
            "--",
        )
    else:
        # Show the files introduced by the initial commit.
        diff_text = repository.git.show(
            "--format=",
            "--no-ext-diff",
            "--no-color",
            "--root",
            "--find-renames",
            "--format=fuller",
            "--patch",
            commit.hexsha,
        )
    return diff_text[:MAX_DIFF_CHARS]
def get_changed_files(commit):
    """Summarize changed files for a commit."""
    rows = []
    for file_path, details in commit.stats.files.items():
        rows.append(
            {
                "File": file_path,
                "Insertions": details.get("insertions", 0),
                "Deletions": details.get("deletions", 0),
                "Lines changed": details.get("lines", 0),
            }
        )
    return pd.DataFrame(rows)
def is_ignored_path(path):
    """Ignore common generated, dependency, and environment directories."""
    return any(part in IGNORED_DIRS for part in path.parts)
def contains_possible_secret(text):
    """Conservative check for a few common secret patterns."""
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)
def scan_source_files(repository):
    """
    Scan tracked files only.
    Skip large files, common generated folders, and likely secret files.
    """
    results = []
    skipped = 0
    try:
        tracked_paths = repository.git.ls_files(
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        )
        paths = [
            item for item in tracked_paths.split("\0") if item
        ]
    except git.GitCommandError:
        return results, 0
    root = Path(repository.working_tree_dir)
    for relative_path in paths:
        if len(results) >= MAX_SOURCE_FILES:
            break
        relative = Path(relative_path)
        if is_ignored_path(relative):
            continue
        if relative.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        full_path = root / relative
        try:
            if not full_path.is_file():
                continue
            if full_path.stat().st_size > MAX_FILE_SIZE:
                skipped += 1
                continue
            content = full_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            if contains_possible_secret(content):
                skipped += 1
                continue
            results.append(
                {
                    "path": relative.as_posix(),
                    "content": content,
                }
            )
        except (OSError, UnicodeError):
            skipped += 1
    return results, skipped
def search_source_files(source_files, query):
    """Find case-insensitive text matches with line numbers."""
    results = []
    query_lower = query.lower()
    for source_file in source_files:
        lines = source_file["content"].splitlines()
        for line_number, line in enumerate(lines, start=1):
            if query_lower in line.lower():
                results.append(
                    {
                        "File": source_file["path"],
                        "Line": line_number,
                        "Code": line.strip()[:500],
                    }
                )
                if len(results) >= 300:
                    return results
    return results
def search_commit_history(commits, query):
    """Search observable commit messages and author metadata."""
    query_lower = query.lower()
    results = []
    for commit in commits:
        searchable = " ".join(
            [
                safe_commit_message(commit),
                commit.author.name or "",
                commit.author.email or "",
                commit.hexsha,
            ]
        )
        if query_lower in searchable.lower():
            results.append(
                {
                    "Hash": commit.hexsha[:8],
                    "Date": commit.committed_datetime.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "Author": commit.author.name or "Unknown",
                    "Commit message": safe_commit_message(commit),
                    "Full hash": commit.hexsha,
                }
            )
    return results
def search_commit_diffs(repository, commits, query):
    """Search commit patches for matching text."""
    query_lower = query.lower()
    results = []
    for commit in commits:
        try:
            diff_text = get_commit_diff(repository, commit)
        except git.GitCommandError:
            continue
        for line_number, line in enumerate(
            diff_text.splitlines(),
            start=1,
        ):
            if query_lower in line.lower():
                results.append(
                    {
                        "Commit": commit.hexsha[:8],
                        "Message": safe_commit_message(commit),
                        "Patch line": line_number,
                        "Matching line": line[:500],
                        "Full hash": commit.hexsha,
                    }
                )
                if len(results) >= 200:
                    return results
    return results
# --------------------------------------------------
# REPOSITORY INPUT
# --------------------------------------------------
st.header("🔍 Repository Analyzer")
repo_path = st.text_input(
    "Enter the full path to a local Git repository",
    placeholder="/Users/yourname/Desktop/your-project",
)
analyze = st.button(
    "Analyze Repository",
    type="primary",
    use_container_width=True,
)
if "repository_path" not in st.session_state:
    st.session_state.repository_path = ""
if analyze:
    st.session_state.repository_path = repo_path.strip()
active_path = st.session_state.repository_path
if not active_path:
    st.info(
        "Enter a repository path and click Analyze Repository to begin."
    )
    st.stop()
try:
    repo = get_repository(active_path)
except ValueError as error:
    st.error(str(error))
    st.stop()
st.success("Git repository detected successfully!")
if repo.is_dirty(untracked_files=True):
    st.warning(
        "This working tree contains uncommitted or untracked changes. "
        "Git history describes committed changes; working-tree files may "
        "differ from the latest commit."
    )
try:
    commits = list(repo.iter_commits(max_count=MAX_COMMITS))
except git.GitCommandError as error:
    st.error(f"Unable to read commit history: {error}")
    st.stop()
if not commits:
    st.warning("This repository has no commits yet.")
    st.stop()
source_files, skipped_files = scan_source_files(repo)
# --------------------------------------------------
# REPOSITORY OVERVIEW
# --------------------------------------------------
st.header("📊 Repository Overview")
contributors = {
    (commit.author.name, commit.author.email)
    for commit in commits
}
branches = list(repo.branches)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Commits analyzed", len(commits))
col2.metric("Contributors", len(contributors))
col3.metric("Local branches", len(branches))
col4.metric("Source files scanned", len(source_files))
st.caption(
    f"Commit history is limited to the latest {MAX_COMMITS} commits. "
    f"Source scanning may skip large files or files matching "
    f"the secret-detection rules ({skipped_files} skipped)."
)
if branches:
    with st.expander("View local branches"):
        for branch in branches:
            st.write(f"• {branch.name}: `{branch.commit.hexsha[:8]}`")
# --------------------------------------------------
# COMMIT HISTORY
# --------------------------------------------------
st.header("🕒 Recent Commit History")
commit_df = get_commit_table(commits)
st.dataframe(
    commit_df,
    use_container_width=True,
    hide_index=True,
)
# --------------------------------------------------
# COMMIT INVESTIGATION
# --------------------------------------------------
st.header("🔬 Investigate a Commit")
commit_options = {
    (
        f"{commit.hexsha[:8]} — "
        f"{safe_commit_message(commit)[:90] or '(no message)'}"
    ): commit
    for commit in commits
}
selected_label = st.selectbox(
    "Select a commit to investigate",
    list(commit_options.keys()),
)
selected_commit = commit_options[selected_label]
st.subheader("📝 Commit Details")
detail1, detail2 = st.columns(2)
detail1.write(f"**Full commit hash:** `{selected_commit.hexsha}`")
detail1.write(
    f"**Author:** {selected_commit.author.name or 'Unknown'}"
)
detail1.write(
    f"**Author email:** {selected_commit.author.email or 'Unknown'}"
)
detail2.write(
    f"**Date:** {selected_commit.committed_datetime}"
)
detail2.write(
    f"**Commit message:** {safe_commit_message(selected_commit) or '(empty)'}"
)
if selected_commit.parents:
    st.write("**Parent commit(s):**")
    for parent in selected_commit.parents:
        st.code(parent.hexsha)
else:
    st.info("This is the initial commit; it has no parent commit.")
st.subheader("📂 Files Changed")
changed_df = get_changed_files(selected_commit)
if changed_df.empty:
    st.info("No changed-file statistics are available for this commit.")
else:
    st.dataframe(
        changed_df,
        use_container_width=True,
        hide_index=True,
    )
st.subheader("🔬 Actual Code Diff")
try:
    diff_text = get_commit_diff(repo, selected_commit)
except git.GitCommandError as error:
    diff_text = ""
    st.error(f"Could not load this commit's diff: {error}")
if diff_text.strip():
    st.caption(
        "Lines beginning with + are additions; lines beginning with - "
        "are deletions. The diff is truncated if it exceeds the display limit."
    )
    st.code(diff_text, language="diff", wrap_lines=True)
else:
    st.info(
        "No patch is available for this commit. It may contain no file "
        "changes or the patch may not be available."
    )
# --------------------------------------------------
# EVIDENCE REPORT
# --------------------------------------------------
st.header("🧾 Evidence Report")
st.markdown("### What we can verify")
st.write(
    f"- Commit identifier: `{selected_commit.hexsha}`"
)
st.write(
    f"- Recorded author: {selected_commit.author.name or 'Unknown'}"
)
st.write(
    f"- Recorded timestamp: {selected_commit.committed_datetime}"
)
st.write(
    f"- Commit message: "
    f"{safe_commit_message(selected_commit) or '(empty)'}"
)
if selected_commit.parents:
    st.write(
        f"- Parent commit: `{selected_commit.parents[0].hexsha}`"
    )
else:
    st.write("- This commit has no parent.")
st.markdown("### What the evidence suggests")
st.write(
    "The commit message and code diff can suggest the purpose of a change. "
    "They do not independently prove the author's original motivation."
)
st.markdown("### Evidence limitations")
st.write(
    "This analysis uses observable Git metadata, commit patches, and "
    "searchable source files. It does not independently verify intent, "
    "external discussions, linked issues, or whether a change was correct."
)
# --------------------------------------------------
# REPOSITORY QUESTION SEARCH
# --------------------------------------------------
st.header("🔎 Search for Evidence in Your Repository")
st.write(
    "Search for a function name, variable, error message, feature, "
    "or phrase found in your source code or commit history."
)
with st.form("evidence_search_form"):
    query = st.text_input(
        "What do you want to investigate?",
        placeholder="Example: authentication, database, retry",
    )
    search_source = st.checkbox(
        "Search source code",
        value=True,
    )
    search_history = st.checkbox(
        "Search commit messages",
        value=True,
    )
    search_diffs = st.checkbox(
        "Search commit diffs",
        value=True,
    )
    submitted = st.form_submit_button(
        "Find Evidence",
        type="primary",
    )
if submitted:
    query = query.strip()
    if not query:
        st.warning("Enter a word or phrase to search.")
    elif len(query) > 200:
        st.warning("Please keep the search query under 200 characters.")
    else:
        total_matches = 0
        if search_source:
            st.subheader("📍 Source Code Evidence")
            source_matches = search_source_files(
                source_files,
                query,
            )
            if source_matches:
                st.dataframe(
                    pd.DataFrame(source_matches),
                    use_container_width=True,
                    hide_index=True,
                )
                total_matches += len(source_matches)
            else:
                st.info("No matching source-code lines were found.")
        if search_history:
            st.subheader("🕒 Commit History Evidence")
            history_matches = search_commit_history(
                commits,
                query,
            )
            if history_matches:
                for item in history_matches:
                    with st.expander(
                        f"{item['Hash']} — {item['Commit message'][:100]}"
                    ):
                        st.write(f"**Date:** {item['Date']}")
                        st.write(f"**Author:** {item['Author']}")
                        st.write(
                            f"**Full commit hash:** `{item['Full hash']}`"
                        )
                        st.write(
                            f"**Commit message:** {item['Commit message']}"
                        )
                total_matches += len(history_matches)
            else:
                st.info("No matching commit messages were found.")
        if search_diffs:
            st.subheader("🧩 Commit Diff Evidence")
            diff_matches = search_commit_diffs(
                repo,
                commits,
                query,
            )
            if diff_matches:
                st.dataframe(
                    pd.DataFrame(diff_matches),
                    use_container_width=True,
                    hide_index=True,
                )
                total_matches += len(diff_matches)
            else:
                st.info("No matching lines were found in the scanned diffs.")
        st.divider()
        if total_matches:
            st.success(
                f"Found {total_matches} matching evidence item(s)."
            )
            st.info(
                "These matches show where the searched text occurs. "
                "They do not automatically explain why a developer "
                "made a change."
            )
        else:
            st.warning(
                "No matches were found in the selected evidence sources. "
                "Try a function name, filename, or shorter search phrase."
            )
# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "CodeStory AI | Evidence-first codebase exploration | "
    "Search matches are not proof of developer intent."
)