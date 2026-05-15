$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "review_app.py"

$pythonCommands = @()

$hardcoded = "C:\Users\ahuja\AppData\Local\Programs\Python\Python312\python.exe"
if (Test-Path -LiteralPath $hardcoded) {
  $pythonCommands += ,@($hardcoded)
}

$pyCmd = Get-Command py -ErrorAction SilentlyContinue
if ($pyCmd) {
  $pythonCommands += ,@($pyCmd.Source, "-3")
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd -and $pythonCmd.Source -notlike "*WindowsApps*") {
  $pythonCommands += ,@($pythonCmd.Source)
}

foreach ($command in $pythonCommands) {
  try {
    $args = @()
    if ($command.Length -gt 1) {
      $args = @($command[1..($command.Length - 1)])
    }
    & $command[0] @args $scriptPath
    exit $LASTEXITCODE
  }
  catch {
    continue
  }
}

throw "Could not find a working Python interpreter to launch review_app.py."
