@echo off
setlocal
set PY=.venv-win\Scripts\python.exe
if not exist %PY% set PY=python

if "%1"=="" goto help
if "%1"=="help" (
    echo Available targets: features, folds, baselines, lane2a, check, test
    exit /b 0
)
if "%1"=="features" (
    %PY% scripts\06_features.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="folds" (
    %PY% scripts\06_folds.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="baselines" (
    %PY% scripts\07_baselines.py %2 %3 %4 %5
    exit /b %errorlevel%
)
if "%1"=="lane2a" (
    echo === [1/5] Running make features ===
    %PY% scripts\06_features.py || exit /b 1
    echo === [2/5] Running make folds ===
    %PY% scripts\06_folds.py || exit /b 1
    echo === [3/5] Running tests/test_features.py ===
    %PY% -m pytest tests/test_features.py -p no:cacheprovider || exit /b 1
    echo === [4/5] Running make baselines ===
    %PY% scripts\07_baselines.py || exit /b 1
    echo === [5/5] Running verification gate ===
    %PY% scripts\08_verify_lane2a.py || exit /b 1
    exit /b 0
)
if "%1"=="check" (
    %PY% scripts\00_env.py
    exit /b %errorlevel%
)
if "%1"=="test" (
    %PY% -m pytest -p no:cacheprovider
    exit /b %errorlevel%
)
if "%1"=="harmonize" (
    %PY% scripts\harmonize.py --country USA
    exit /b %errorlevel%
)
echo Unknown target: %1
exit /b 1
