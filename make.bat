@echo off
setlocal
set PY=.venv-win\Scripts\python.exe
if not exist %PY% set PY=python

if "%1"=="" goto help
if "%1"=="help" (
    echo Available targets: features, folds, baselines, verify, lane2a, check, test
    exit /b 0
)
if "%1"=="features" (
    %PY% scripts\05_features.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="folds" (
    %PY% scripts\06_folds.py --approved %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="baselines" (
    %PY% scripts\07_baselines.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="verify" (
    %PY% scripts\08_verify_lane2a.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="site" (
    %PY% scripts\09_build_site.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="test" (
    %PY% -m pytest tests\test_features.py -p no:cacheprovider %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="lane2a" (
    %PY% scripts\run_lane2a.py
    exit /b %errorlevel%
)
if "%1"=="check" (
    %PY% scripts\00_env.py
    exit /b %errorlevel%
)
if "%1"=="harmonize" (
    %PY% scripts\harmonize.py --country USA
    exit /b %errorlevel%
)
echo Unknown target: %1
exit /b 1
