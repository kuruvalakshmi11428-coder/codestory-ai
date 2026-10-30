import streamlit as st
import git
import pandas as pd
from pathlib import Path
# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="CodeStory AI",
    page_icon="📖",
    layout="wide"
)
# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("📖 CodeStory AI")
st.subheader("Understand your codebase through evidence, not guesses.")
st.markdown(
    """
    CodeStory AI explores Git repositories to help developers understand
    how their projects have evolved.
    Explore commit history, inspect code changes, and examine the evidence
    behind software development decisions.
    """
)
st.divider()
# --------------------------------------------------
# REPOSITORY INPUT
# --------------------------------------------------
st.header("🔍 Repository Analyzer")
repo_path = st.text_input(
    "Enter the full path to a local Git repository",
    placeholder="/Users/yourname/Desktop/your-project"
)
analyze_button = st.button(
    "Analyze Repository",
    type="primary"
)
# --------------------------------------------------
# REPOSITORY ANALYSIS
# --------------------------------------------------
if analyze_button:
    if not repo_path.strip():
        st.warning("Please enter a repository path.")
    else:
        folder = Path(repo_path).expanduser().resolve()
        if not folder.exists():
            st.error(
                "The folder does not exist. Please check the path."
            )
        elif not folder.is_dir():
            st.error(
                "The path must point to a folder."
            )
        else:
            try:
                repo = git.Repo(
                    str(folder),
                    search_parent_directories=False
                )
                st.success("Git repository detected successfully!")
                # ------------------------------------------
                # LOAD COMMITS
                # ------------------------------------------
                commits = list(
                    repo.iter_commits(max_count=100)
                )
                if not commits:
                    st.warning(
                        "This repository does not contain any commits."
                    )
                else:
                    # --------------------------------------
                    # REPOSITORY OVERVIEW
                    # --------------------------------------
                    st.header("📊 Repository Overview")
                    contributors = {
                        commit.author.email or commit.author.name
                        for commit in commits
                    }
                    branches = list(repo.branches)
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Commits analyzed",
                        len(commits)
                    )
                    col2.metric(
                        "Contributors",
                        len(contributors)
                    )
                    col3.metric(
                        "Local branches",
                        len(branches)
                    )
                    # --------------------------------------
                    # COMMIT HISTORY
                    # --------------------------------------
                    st.header("🕒 Recent Commit History")
                    commit_rows = []
                    for commit in commits:
                        commit_rows.append({
                            "Commit": commit.hexsha[:8],
                            "Date": commit.committed_datetime.strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "Author": commit.author.name,
                            "Message": (
                                commit.message.strip().splitlines()[0]
                                if commit.message.strip()
                                else "(No commit message)"
                            )
                        })
                    commit_df = pd.DataFrame(commit_rows)
                    st.dataframe(
                        commit_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    # --------------------------------------
                    # SELECT A COMMIT
                    # --------------------------------------
                    st.header("🔬 Investigate a Commit")
                    def get_commit_label(commit):
                        message = commit.message.strip().splitlines()
                        first_line = (
                            message[0]
                            if message
                            else "(No commit message)"
                        )
                        return (
                            f"{commit.hexsha[:8]} — "
                            f"{first_line[:80]}"
                        )
                    commit_options = {
                        get_commit_label(commit): commit
                        for commit in commits
                    }
                    selected_label = st.selectbox(
                        "Select a commit to investigate",
                        list(commit_options.keys())
                    )
                    selected_commit = commit_options[selected_label]
                    # --------------------------------------
                    # COMMIT DETAILS
                    # --------------------------------------
                    st.subheader("📝 Commit Details")
                    st.write(
                        f"**Full commit hash:** "
                        f"`{selected_commit.hexsha}`"
                    )
                    st.write(
                        f"**Author:** {selected_commit.author.name}"
                    )
                    st.write(
                        f"**Date:** "
                        f"{selected_commit.committed_datetime}"
                    )
                    st.write("**Commit message:**")
                    st.code(
                        selected_commit.message.strip() or
                        "(No commit message)"
                    )
                    if selected_commit.parents:
                        st.write(
                            "**Parent commit:** "
                            f"`{selected_commit.parents[0].hexsha[:8]}`"
                        )
                    else:
                        st.write(
                            "**Parent commit:** None. "
                            "This is the initial commit."
                        )
                    # --------------------------------------
                    # CHANGED FILES
                    # --------------------------------------
                    st.subheader("📂 Files Changed")
                    changed_files = selected_commit.stats.files
                    if changed_files:
                        file_rows = []
                        for filename, details in changed_files.items():
                            file_rows.append({
                                "File": filename,
                                "Lines Added": details["insertions"],
                                "Lines Deleted": details["deletions"],
                                "Lines Changed": details["lines"]
                            })
                        files_df = pd.DataFrame(file_rows)
                        st.dataframe(
                            files_df,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info(
                            "No file changes were detected for this commit."
                        )
                    # --------------------------------------
                    # EVIDENCE-BASED EXPLANATION
                    # --------------------------------------
                    st.header("🧾 Evidence Report")
                    st.markdown("### What we can verify")
                    st.write(
                        "The selected Git commit provides evidence about "
                        "its identifier, author information, timestamp, "
                        "commit message, and changed files."
                    )
                    st.markdown("### What the evidence suggests")
                    st.write(
                        "The commit message can indicate the change's "
                        "intended purpose. However, a message alone does "
                        "not prove the developer's original motivation."
                    )
                    st.markdown("### Evidence limitations")
                    st.warning(
                        "This version does not independently verify the "
                        "developer's intentions. Additional evidence, "
                        "such as linked issues, pull requests, tests, "
                        "or project documentation, may be required."
                    )
                    st.caption(
                        "CodeStory AI prototype — explanations are based "
                        "on observable repository evidence."
                    )
            except git.InvalidGitRepositoryError:
                st.error(
                    "This folder is not a Git repository. "
                    "Choose a folder containing a valid .git directory."
                )
            except git.NoSuchPathError:
                st.error(
                    "Git could not find the selected repository."
                )
            except Exception as error:
                st.error(
                    f"An unexpected error occurred: {error}"
                )
# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "CodeStory AI | Evidence-first codebase exploration"
)