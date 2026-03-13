# Committing Motadata as files (not submodule) in m-coder

## Goal

- **Locally:** Keep `ml/training/src/sources/Motadata` as its own git repo (you can `cd` there, commit, push to its own remote).
- **In m-coder:** When you commit in the outer repo, Motadata is recorded as **file contents**, not as a submodule/gitlink, so clones of m-coder get the actual Phase-6 and other files.

## Why this is needed

If Motadata contains a `.git` directory, running `git add -A` or `git add ml/training/src/sources/Motadata` in m-coder makes Git add it as a **gitlink** (submodule reference), not as normal files. To have m-coder track the **files**, the outer repo must not see a `.git` inside Motadata when you add.

## Workflow (every time you want to commit Motadata changes into m-coder)

From the **m-coder repo root**:

1. **Hide Motadata’s .git**  
   ```bash
   ./scripts/prepare-motadata-for-m-coder-commit.sh
   ```

2. **Stage and commit in m-coder**  
   ```bash
   git add ml/training/src/sources/Motadata
   # add any other paths you want
   git commit -m "Your message"
   ```

3. **Restore Motadata’s .git**  
   ```bash
   ./scripts/restore-motadata-git.sh
   ```

After step 3, Motadata is again a normal git repo and you can work inside it as usual.

## Fixing the current broken commit (Motadata added as gitlink)

If you already committed and Motadata was added as a submodule/gitlink:

1. **Remove the gitlink from the index and undo the last commit** (keeps your other changes):  
   ```bash
   git rm --cached ml/training/src/sources/Motadata
   git reset --soft HEAD~1
   ```

2. **Re-add Motadata as files** using the workflow above:  
   ```bash
   ./scripts/prepare-motadata-for-m-coder-commit.sh
   git add ml/training/src/sources/Motadata
   git add .   # or only the paths you want
   git commit -m "Add Phase-6 and Motadata sources as files"
   ./scripts/restore-motadata-git.sh
   ```

Result: m-coder’s history contains the real files; clones get them; locally Motadata stays a separate repo.
