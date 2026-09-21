$ErrorActionPreference = "Stop"
$dir = "C:\Users\Usuario\AppData\Local\Temp\claude\C--Users-Usuario-local-ai-harness\a0d9fc63-a1ae-4e45-8c1e-47a5c51cb176\scratchpad\stress_project"
$files = Get-ChildItem $dir -Filter "*.py" | Sort-Object Name
$question = "`n`n# QUESTION`nBased only on the Python code above, answer in ONE short sentence: what is the exact integer value of MAX_TASKS_PER_USER, and in which file is it defined?"

# realistic-looking filler: repeated CRUD boilerplate unrelated to the planted fact
$fillerUnit = @"

class Entity{0}:
    def __init__(self, id, name, created_by):
        self.id = id
        self.name = name
        self.created_by = created_by

    def rename(self, new_name):
        self.name = new_name

    def to_dict(self):
        return {{"id": self.id, "name": self.name, "created_by": self.created_by}}

"@

$paddingLevels = @(30, 90, 180)  # repeats of filler unit -> roughly small/medium/large padding
$results = @()

foreach ($reps in $paddingLevels) {
    $filler = 1..$reps | ForEach-Object { $fillerUnit -f $_ } | Out-String
    $body = ($files | ForEach-Object { "# FILE: $($_.Name)`n" + (Get-Content $_.FullName -Raw) }) -join "`n`n"
    # insert filler AFTER file 1 (where the fact lives) and before the rest, to bury the fact under growing unrelated context
    $parts = $body -split "(?=# FILE: 02_storage.py)", 2
    $prompt = $parts[0] + "`n# FILE: 09_generated_entities.py`n" + $filler + "`n`n" + $parts[1] + $question

    $payload = @{ model="phi3"; prompt=$prompt; stream=$false; options=@{ num_predict=80; temperature=0 } } | ConvertTo-Json -Depth 5

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 500
    $sw.Stop()

    $correct = $resp.response -match "47"
    $result = [PSCustomObject]@{
        FillerReps        = $reps
        CharCount         = $prompt.Length
        RealPromptTokens  = $resp.prompt_eval_count
        TotalTime_seconds = [math]::Round($resp.total_duration/1e9,2)
        PromptEvalTime_s  = [math]::Round($resp.prompt_eval_duration/1e9,2)
        MentionsCorrect47 = $correct
        ModelAnswer       = ($resp.response -replace "`n"," ").Trim()
    }
    $results += $result
    $result | Format-List
}

$results | Format-Table -AutoSize
