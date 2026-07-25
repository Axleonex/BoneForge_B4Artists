@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem BoneForge B4Artists 8.5.1 publish script (blendshape-safe FBX export).
rem Runs INSIDE the real repo checkout. Verifies the five patched files by
rem SHA-256 before doing anything, then: name_scan -> build_release ->
rem git add (only the intended files) -> commit -> plain push (NO force).
rem Targets ONLY Axleonex/BoneForge_B4Artists with the Axlbot identity.

set "REPO=F:\Scripting Attempts\B4Artists_Tools\BoneForge_B4Artists_github"
set "EXPECT_REMOTE=https://github.com/Axleonex/BoneForge_B4Artists.git"
set "PRIMARY_NAME=Axlbot"
set "PRIMARY_EMAIL=axleonex@gmail.com"
set "FALLBACK_EMAIL=57645501+Axleonex@users.noreply.github.com"

cd /d "%REPO%" || (echo ERROR: repo folder not found: %REPO% & goto :fail)

rem F: does not record ownership (exFAT) - whitelist the repo for git,
rem same as the open-Blender push script does for its staging repo.
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
echo Step 1/6 - verifying patched files by SHA-256...
call :check "boneforge\__init__.py" 5E37F9274EDFDDEEEC93232DDFA4D41D7B23937192B816D46F6C837308CF7F52
call :check "boneforge\vrchat\export\vrchat_export.py" C633929E96ED69881F0F50D0FDBEBDCBBD1B465AB254FD5F2020E8632BBA2A49
call :check "boneforge\io_hub\game_export.py" 39260E68385E265B4B256AA39D7E6ADE7DBB478FAAFC41CD3ED31E5BF9C28D9C
call :check "boneforge\io_hub\panel.py" 39A9FEBE510A666A128FF5966B75DB65E34F62D8C021AF6E5C779EEEC92E871C
call :check "boneforge\vrm\exporter.py" 9A346DB78F43DD283662AF796B681403C4BF0BC28286D9D67EB2B767F139DD17
echo   All five files verified.

echo.
echo Step 2/6 - BFA exclusivity markers...
if not exist "boneforge\bfa_guard.py" (echo ERROR: bfa_guard.py missing & goto :fail)
if not exist "boneforge\BFA_EXCLUSIVE.md" (echo ERROR: BFA_EXCLUSIVE.md missing & goto :fail)
echo   OK.

echo.
echo Step 3/6 - name_scan (must stay clean)...
python scripts\name_scan.py .
if errorlevel 1 (echo ERROR: name_scan flagged something & goto :fail)

echo.
echo Step 4/6 - building release zip via scripts\build_release.py...
python scripts\build_release.py
if errorlevel 1 (echo ERROR: build_release failed & goto :fail)
if not exist "releases\BoneForge-BFA-8.5.1.zip" (
    echo ERROR: releases\BoneForge-BFA-8.5.1.zip was not produced.
    echo Check that boneforge\__init__.py bl_info version is 8, 5, 1.
    goto :fail
)

echo.
echo Step 5/6 - git commit (only the intended files)...
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

git add "boneforge\__init__.py" "boneforge\vrchat\export\vrchat_export.py" "boneforge\io_hub\game_export.py" "boneforge\io_hub\panel.py" "boneforge\vrm\exporter.py" "releases\BoneForge-BFA-8.5.1.zip"
if errorlevel 1 goto :git_fail

git diff --cached --quiet
if errorlevel 1 (
    git commit -m "Publish BoneForge B4Artists 8.5.1 exclusive build - blendshape-safe FBX export"
    if errorlevel 1 goto :git_fail
) else (
    echo No staged changes to commit - already committed.
)

echo.
echo Step 6/6 - push to !RURL!
echo This is a normal push of main (NOT a force push).
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
echo DONE. BoneForge B4Artists 8.5.1 published.
goto :done

:check
set "F=%~1"
set "WANT=%~2"
if not exist "%F%" (echo ERROR: missing %F% & goto :fail)
set "GOT="
for /f "delims=" %%H in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%F%').Hash"') do set "GOT=%%H"
if /I not "!GOT!"=="%WANT%" (
    echo ERROR: %F% hash mismatch - the patched file did not land correctly.
    echo   expected: %WANT%
    echo   actual:   !GOT!
    echo Tell Claude this file failed verification.
    goto :fail
)
echo   OK  %F%
exit /b 0

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
