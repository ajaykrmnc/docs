## Git Command Sheet

- Complete documentation can be found here: [Pro Git Book](https://git-scm.com/book/en/v2)
- Install `lazygit` for nice TUI experience.

## Basics

1. `git clone url [new repo name]`
2. Created a alias `git config --global alias.glog "log --graph --pretty=format:'%C(yellow)%h%C(reset) - %C(cyan)%an%C(reset) - %C(blue)%ad%C(reset) - %s' --date=short"`.

   Use `git glog` now

3. To check the remote servers (eg GitHub): `git remote -v`.

   If you clone a repository, the command automatically adds that remote repository under the name “origin”. If your current branch is set up to track a remote branch, you can use the `git pull` command to automatically fetch and then merge that remote branch into your current branch. By default, the `git clone` command automatically sets up your local master branch to track the remote master branch (or whatever the default branch is called) on the server you cloned from. Running `git pull` generally fetches data from the server you originally cloned from and automatically tries to merge it into the code you’re currently working on.

4. Pushing branch to remote: `git push <remote> <branch>`

5. Inspecting a remote in detail: `git remote show <origin>`

## Branches

1. Create a new branch and checkout to it: `git checkout -b <newbranchname>`

2. Merge a branch to master: `git checkout master && git merge <branch to be merged>`

3. See all branches: `git branch --all -vv`

4. Pushing to new remote branch name: you could run `git push origin serverfix:awesomebranch` to push your local serverfix branch to the awesomebranch branch on the remote project.

5. `git checkout -b <branch> <remote>/<branch>` : Create a local tracking branch for a remote branch

6. For pt 5, shortcut is `git checkout <branch>` (If the branch name you’re trying to checkout (a) doesn’t exist and (b) exactly matches a name on only one remote, Git will create a tracking branch for you)

## Stashing

1. `git stash`

2. `git stash list`

3. `git stash apply / pop`
