# get root folder in trunk
$ROOT_FOLDER = Resolve-Path -Path  "$PSScriptRoot\..\"
Set-Location $ROOT_FOLDER

# Look for standard install location for python, otherwise
# switch to location as specified in file `BASE_DIR_PYTHON`
$BASE_DIR_PYTHON_FROM_FILE = Get-Content -Path "$ROOT_FOLDER\BASE_DIR_PYTHON"
$BASE_DIR_DEFAULT_PYTHON = "$env:LOCALAPPDATA\Programs\Python\Python312"

if (Test-Path -Path "$BASE_DIR_DEFAULT_PYTHON\python.exe"){
    $BASE_DIR_PYTHON = $BASE_DIR_DEFAULT_PYTHON
    $PYTHON_EXE = "$BASE_DIR_DEFAULT_PYTHON\python.exe"
}
elseif (Test-Path -Path "$BASE_DIR_PYTHON_FROM_FILE\python.exe"){
    $BASE_DIR_PYTHON = $BASE_DIR_PYTHON_FROM_FILE
    $PYTHON_EXE = "$BASE_DIR_PYTHON_FROM_FILE\python.exe"
}
else {
    Write-Host "No Python interpreter found, check the installation instructions in README.pdf!" -ForegroundColor Red
    exit
}

# set paths to the locations for python, poetry and python-venv
$PYTHON_EXE = "$BASE_DIR_PYTHON\python.exe"
$POETRY_EXE = "$BASE_DIR_PYTHON\Scripts\poetry.exe"
$VENV_INSTALL_LOCATION = Resolve-Path -Path "$ROOT_FOLDER"
$VENV_FOLDER = "$VENV_INSTALL_LOCATION\.venv"
$PYTHON_VENV_EXE = "$VENV_FOLDER\Scripts\python.exe"

# get version of python interpreter
$cmd = (get-item -Path $PYTHON_EXE).VersionInfo | Format-List -Force | findstr ProductVersion
$cmd_split = $cmd -split ": "
$PYTHON_VERSION = $cmd_split[1]

# check if python version is 3.12
if ($PYTHON_VERSION -like "*3.12*"){
    Write-Host "Found a compatible Python version (=$PYTHON_VERSION) in $PYTHON_EXE!!" -ForegroundColor Green
}
else{
    Write-Host "Python version does not match required version (=$PYTHON_VERSION), should be 3.12.x" -ForegroundColor Red
    exit
}


# first delete existing .venv folder
if (Test-Path -Path $VENV_FOLDER) {
    Get-ChildItem -Path $VENV_INSTALL_LOCATION -Directory -Filter ".venv" | Remove-Item -Recurse -Confirm:$false -Force
    Write-Host "deleted already existing .venv in $VENV_INSTALL_LOCATION" -ForegroundColor Yellow
}

# upgrade pip
& $PYTHON_EXE -m pip install --upgrade pip --no-warn-script-location

# install or upgrade poetry
& $PYTHON_EXE -m pip install --upgrade poetry --no-warn-script-location

# configure poetry
& $POETRY_EXE --version
& $POETRY_EXE config virtualenvs.in-project true
& $POETRY_EXE config virtualenvs.options.system-site-packages false
& $POETRY_EXE config --list

# install packages with poetry from pyproject.toml in VENV_FOLDER
& $POETRY_EXE update

Write-Host "Python has been successfully installed in $PYTHON_VENV_EXE" -ForegroundColor Green


