param([int]$Port = 11435)
$ErrorActionPreference = 'Stop'
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Choose a valid nonprivileged local port.' }
$taskRuntime = Join-Path $env:LOCALAPPDATA 'Programs\AnythingLLM\resources\ollama\llm.exe'
$taskModels = Join-Path $env:APPDATA 'anythingllm-desktop\storage\models\ollama'
if (-not (Test-Path -LiteralPath $taskRuntime -PathType Leaf) -or -not (Test-Path -LiteralPath $taskModels -PathType Container)) {
    throw 'The inspected local runtime/model store is missing. Nothing will be downloaded.'
}
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
    throw 'This port is occupied. Verify the existing service; this script will not replace it.'
}
$env:OLLAMA_HOST = "127.0.0.1:$Port"
$env:OLLAMA_MODELS = $taskModels
$env:OLLAMA_CONTEXT_LENGTH = '2048'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$taskProcess = Start-Process -FilePath $taskRuntime -ArgumentList 'serve' -WindowStyle Hidden -PassThru
Write-Output "Started local Ollama PID $($taskProcess.Id) on 127.0.0.1:$Port. No model selected, downloaded or invoked."
Write-Output "Stop your server later with: Stop-Process -Id $($taskProcess.Id)"
