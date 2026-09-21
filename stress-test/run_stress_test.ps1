$ErrorActionPreference = "Stop"
$dir = "C:\Users\Usuario\AppData\Local\Temp\claude\C--Users-Usuario-local-ai-harness\a0d9fc63-a1ae-4e45-8c1e-47a5c51cb176\scratchpad\stress_project"
$files = Get-ChildItem $dir -Filter "*.py" | Sort-Object Name

$checkpoints = @(1,2,4,6,8)
$question = "`n`n# QUESTION`nBased only on the Python code above, answer in ONE short sentence: what is the exact integer value of MAX_TASKS_PER_USER, and in which file is it defined?"

$results = @()

foreach ($n in $checkpoints) {
    $subset = $files | Select-Object -First $n
    $body = ($subset | ForEach-Object {
        "# FILE: $($_.Name)`n" + (Get-Content $_.FullName -Raw)
    }) -join "`n`n"
    $prompt = $body + $question
    $charCount = $prompt.Length

    # crude local estimate for comparison against the real tokenizer count Ollama reports
    $estTokens = [math]::Round($charCount / 4)

    $payload = @{
        model = "phi3"
        prompt = $prompt
        stream = $false
        options = @{ num_predict = 80; temperature = 0 }
    } | ConvertTo-Json -Depth 5

    # sample CPU while the request is in flight
    $cpuSamples = [System.Collections.Generic.List[double]]::new()
    $job = Start-Job -ScriptBlock {
        $s = @()
        for ($i=0; $i -lt 240; $i++) {
            $s += (Get-CimInstance Win32_Processor).LoadPercentage
            Start-Sleep -Milliseconds 500
        }
        return $s
    }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 300
    $sw.Stop()

    Stop-Job $job | Out-Null
    $cpuData = Receive-Job $job
    Remove-Job $job | Out-Null
    $avgCpu = if ($cpuData) { [math]::Round(($cpuData | Measure-Object -Average).Average, 1) } else { $null }
    $maxCpu = if ($cpuData) { [math]::Round(($cpuData | Measure-Object -Maximum).Maximum, 1) } else { $null }

    $ttft_s = [math]::Round($resp.load_duration / 1e9 + $resp.prompt_eval_duration / 1e9, 2)
    $totalGenTime_s = [math]::Round($resp.total_duration / 1e9, 2)
    $tokPerSec = if ($resp.eval_duration -gt 0) { [math]::Round($resp.eval_count / ($resp.eval_duration/1e9), 2) } else { $null }

    $result = [PSCustomObject]@{
        Files             = $n
        CharCount         = $charCount
        EstTokens_chars4  = $estTokens
        RealPromptTokens  = $resp.prompt_eval_count
        ResponseTokens    = $resp.eval_count
        TTFT_seconds      = $ttft_s
        TotalTime_seconds = $totalGenTime_s
        TokensPerSec_gen  = $tokPerSec
        AvgCPU_pct        = $avgCpu
        MaxCPU_pct        = $maxCpu
        ModelAnswer       = ($resp.response -replace "`n"," ").Trim()
    }
    $results += $result
    Write-Output "=== n=$n files done ==="
    $result | Format-List
}

$results | Export-Csv -Path "$($dir)\..\stress_results.csv" -NoTypeInformation
Write-Output "`n`nFULL TABLE:"
$results | Format-Table -AutoSize
