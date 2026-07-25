@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Generic BoneForge B4Artists publisher.
rem Publishes WHATEVER version the repo currently holds - the bl_info
rem version drives the zip name and the commit message, so this script
rem never needs editing between releases.
rem Flow: version -> BFA checks -> name_scan -> build zip -> commit ->
rem rebase-sync with GitHub -> confirm -> plain push (NO force).
rem Targets ONLY Axleonex/BoneForge_B4Artists with the Axlbot identity.

set "REPO=F:\Scripting Attempts\B4Artists_Tools\BoneForge_B4Artists_github"
set "EXPECT_REMOTE=https://github.com/Axleonex/BoneForge_B4Artists.git"
set "PRIMARY_NAME=Axlbot"
set "PRIMARY_EMAIL=axleonex@gmail.com"
set "FALLBACK_EMAIL=57645501+Axleonex@users.noreply.github.com"

cd /d "%REPO%" || (echo ERROR: repo folder not found: %REPO% & goto :fail)
git config --global --add safe.directory "F:/Scripting Attempts/B4Artists_Tools/BoneForge_B4Artists_github"

where git >nul 2>nul || (echo ERROR: git not on PATH & goto :fail)
where python >nul 2>nul || (echo ERROR: python not on PATH & goto :fail)

for /f "delims=" %%N in ('git config --global user.name 2^>nul') do set "GN=%%N"
for /f "delims=" %%E in ('git config --global user.email 2^>nul') do set "GE=%%E"
echo !GN! !GE! !GIT_AUTHOR_NAME! !GIT_AUTHOR_EMAIL! !GIT_COMMITTER_NAME! !GIT_COMMITTER_EMAIL! | findstr /I "jonvilario" >nul
if not errorlevel 1 (
    echo ERROR: Jonvilario git identity detected. Aborting.
    goto :fail
)

echo.
echo Step 1/7 - reading version from bl_info...
set "VERSION="
for /f "delims=" %%V in ('python scripts\print_version.py 2^>nul') do set "VERSION=%%V"
if not defined VERSION (echo ERROR: could not read bl_info version & goto :fail)
echo   Publishing BoneForge B4Artists !VERSION!

echo.
echo Step 2/7 - BFA exclusivity checks...
if not exist "boneforge\bfa_guard.py" (echo ERROR: bfa_guard.py missing & goto :fail)
if not exist "boneforge\BFA_EXCLUSIVE.md" (echo ERROR: BFA_EXCLUSIVE.md missing & goto :fail)
findstr /C:"BoneForge BFA" "boneforge\__init__.py" >nul
if errorlevel 1 (echo ERROR: package does not identify as BoneForge BFA & goto :fail)
echo   OK.

echo.
echo Step 3/7 - name_scan must stay clean...
python scripts\name_scan.py .
if errorlevel 1 (echo ERROR: name_scan flagged something & goto :fail)

echo.
echo Step 4/7 - building release zip...
python scripts\build_release.py
if errorlevel 1 (echo ERROR: build_release failed & goto :fail)
if not exist "releases\BoneForge-BFA-!VERSION!.zip" (echo ERROR: expected zip for !VERSION! was not produced & goto :fail)

echo.
echo Step 5/7 - git commit...
git config user.name "%PRIMARY_NAME%"
git config user.email "%PRIMARY_EMAIL%"
git config credential.username "Axleonex"

for /f "delims=" %%R in ('git remote get-url origin') do set "RURL=%%R"
if /I not "!RURL!"=="%EXPECT_REMOTE%" (
    echo ERROR: origin remote mismatch.
    echo Expected: %EXPECT_REMOTE%
    echo Actual:   !RURL!
    goto :fail
)

rem Self-heal: the index is a disposable cache; if unreadable, rebuild from HEAD.
git status --porcelain >nul 2>&1
if errorlevel 1 (
    echo Git index unreadable - rebuilding it from HEAD...
    del /q ".git\index" 2>nul
    git read-tree HEAD
    if errorlevel 1 goto :git_fail
)

git add -u
if errorlevel 1 goto :git_fail
git add "releases\BoneForge-BFA-!VERSION!.zip"
if errorlevel 1 goto :git_fail

echo   Staged changes:
git diff --cached --stat

git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Publish BoneForge B4Artists !VERSION! exclusive build"
    if errorlevel 1 goto :git_fail
) else (
    echo   Nothing new to commit - already committed.
)

echo.
echo Step 6/7 - syncing with GitHub before push...
git pull --rebase --autostash origin main
if errorlevel 1 (echo ERROR: rebase against origin/main failed - resolve manually & goto :fail)

echo.
echo Step 7/7 - push to !RURL!
echo Latest local commit:
git log --oneline -1
echo This is a normal push of main, NOT a force push.
set /p CONFIRM=Type PUSH_BFA_BONEFORGE to push, or anything else to stop here:
if /I not "!CONFIRM!"=="PUSH_BFA_BONEFORGE" (
    echo Push skipped. The commit stays local until you push.
    goto :done
)

git push origin main
if errorlevel 1 (
    echo Push failed. Retrying once with the Axleonex noreply email...
    git config user.email "%FALLBACK_EMAIL%"
    git commit --amend --reset-author --no-edit
    if errorlevel 1 goto :git_fail
    git push origin main
    if errorlevel 1 goto :git_fail
)

echo.
echo DONE. BoneForge B4Artists !VERSION! published.
goto :done

:git_fail
echo ERROR: git operation failed.

:fail
echo.
echo Publish aborted - nothing was pushed.
pause
exit /b 1

:done
pause
exit /b 0
