## Creating a local repository
1. Create an empty folder in your system where you want the code to exist.
2. Clone the git repository to that folder space.
    * Click 'File' -> 'Clone/New...'
    * Copy the url into the first input field
    * Select the path to the folder you just created (in step 1)
    * Make sure to use Local Folder: [Root]
3. You're done.

## Making changes
You can make any changes to the files that are within the folder (local repository) or any sub-folder of it. These will automatically be tracked by git and realized those files have changes to them.

## Commiting changes
1. Go to the branch you want to commit changes to.
2. In the top-left click the 'Commit' button.
3. Select all the files you want to commit under the 'Unstaged files' and press 'Stage Selected'.
4. Write a comment about the changes you made.
5. Press the 'Commit' button in the bottom-right.

## Pushing changes
1. Go to the branch you want to push to the server.
2. In the top-left click the 'Push' button (it should have number beside it indicating you haven't pushed something).
3. Select which branch you want to push up and select the destination branch you want to push it to (usually the same name as your local branch).
    * If you have never pushed this branch up to the server before it will create one for you.
4. Click the push button in the bottom-right.

## Creating new branches
1. Go to the branch you want to branch from (create a copy of).
2. In the top-left and click the 'Branch' button.
3. Type in the name of your new branch (should relate to what changes you will make, but has no impact).
4. Click the 'Create Branch' button in the bottom-right.

## Creating pull request
1. Go to github and go to the 3D_Noise_Modelling repository
2. Go to the code tab, looks like '<> Code'
3. Select the 'Branch' drop-down menu.
4. Select the branch you want to commit (generally the branch you just pushed to the server).
5. Select the 'base' branch, this is the branch the changes will be commited to and the 'compare' branch, this is the branch in which you made the changes.
6. Click 'Create pull request'.