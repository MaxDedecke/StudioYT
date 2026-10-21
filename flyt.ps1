# FLYT - FL Studio to YouTube Video Automator
param (
    [string]$AudioPath = "",
    [string]$ImagePath = ""
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       FLYT - Luxury VVS Beat Video Automator           " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = $PSScriptRoot

# 1. FFmpeg finden
$ffmpeg = $null
$wingetFfmpeg = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe"
if (Test-Path $wingetFfmpeg) {
    $ffmpeg = $wingetFfmpeg
} else {
    $cmd = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
    if ($cmd) { $ffmpeg = $cmd.Source }
}

if (-not $ffmpeg) {
    Write-Host "[FEHLER] FFmpeg nicht gefunden!" -ForegroundColor Red
    if (-not $env:FLYT_NON_INTERACTIVE) { Read-Host "Drücke Enter zum Beenden..." }
    exit 1
}

# 2. Audio-Datei ermitteln
if (-not $AudioPath -and $args.Count -gt 0) {
    $AudioPath = $args[0]
}

if (-not $AudioPath) {
    Write-Host "Keine Datei übergeben. Suche neueste MP3 in Musik..." -ForegroundColor Gray
    $latestMp3 = Get-ChildItem -Path "$env:USERPROFILE\Music\*.mp3" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestMp3) {
        $AudioPath = $latestMp3.FullName
    }
}

if (-not $AudioPath -or -not (Test-Path $AudioPath)) {
    Write-Host "[FEHLER] Keine gültige Beat-Datei angegeben!" -ForegroundColor Red
    Write-Host "Tipp: Ziehe deine MP3 einfach per Drag & Drop auf die Datei oder die Desktop-Verknüpfung." -ForegroundColor Yellow
    if (-not $env:FLYT_NON_INTERACTIVE) { Read-Host "Drücke Enter zum Beenden..." }
    exit 1
}

$audioItem = Get-Item $AudioPath
$audioDir = $audioItem.DirectoryName
$baseName = $audioItem.BaseName

Write-Host "[1/3] Beat-Datei erkannt:" -ForegroundColor Green
Write-Host "      $($audioItem.FullName)" -ForegroundColor White
Write-Host ""

# 3. Cover-Bild finden
$coverImg = $ImagePath
if (-not $coverImg) {
    $possibleCovers = @(
        (Join-Path $audioDir "$baseName.jpg"),
        (Join-Path $audioDir "$baseName.png"),
        (Join-Path $audioDir "cover.jpg"),
        (Join-Path $audioDir "cover.png"),
        (Join-Path $audioDir "artwork.jpg"),
        (Join-Path $scriptDir "default_vvs.jpg"),
        (Join-Path $scriptDir "default_cover.jpg")
    )
    foreach ($c in $possibleCovers) {
        if (Test-Path $c) {
            $coverImg = $c
            break
        }
    }
}

if (-not $coverImg -or -not (Test-Path $coverImg)) {
    Write-Host "[FEHLER] Kein Artwork-Bild gefunden!" -ForegroundColor Red
    if (-not $env:FLYT_NON_INTERACTIVE) { Read-Host "Drücke Enter zum Beenden..." }
    exit 1
}

Write-Host "[2/3] VVS Artwork:" -ForegroundColor Green
Write-Host "      $coverImg" -ForegroundColor White
Write-Host ""

# 4. Video-Renderpfad
$outputVideo = Join-Path $audioDir "$($baseName)_YouTube.mp4"
$sparkleLoop = Join-Path $scriptDir "sparkle_loop_20s.mp4"

Write-Host "[3/3] Rendere 1440p QHD Video mit dezentem Diamant-Blinken..." -ForegroundColor Cyan
Write-Host "      Ziel: $outputVideo" -ForegroundColor Gray
Write-Host ""

# Video-Filter zusammenstellen
$ffmpegArgs = @("-y", "-loop", "1", "-r", "30", "-i", $coverImg)

if (Test-Path $sparkleLoop) {
    $ffmpegArgs += @("-stream_loop", "-1", "-i", $sparkleLoop, "-i", $AudioPath)
    $ffmpegArgs += @(
        "-filter_complex", "[0:v]scale=2560:1440,format=gbrp[bg];[1:v]scale=2560:1440,format=gbrp[sp];[bg][sp]blend=all_mode=addition,format=yuv420p[v]",
        "-map", "[v]",
        "-map", "2:a"
    )
} else {
    $ffmpegArgs += @(
        "-i", $AudioPath,
        "-vf", "scale=2560:1440:force_original_aspect_ratio=decrease,pad=2560:1440:(ow-iw)/2:(oh-ih)/2:black",
        "-map", "0:v",
        "-map", "1:a"
    )
}

$ffmpegArgs += @(
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-c:a", "aac",
    "-b:a", "320k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    "-movflags", "+faststart",
    $outputVideo
)

$process = Start-Process -FilePath $ffmpeg -ArgumentList $ffmpegArgs -NoNewWindow -Wait -PassThru

if ($process.ExitCode -eq 0 -and (Test-Path $outputVideo)) {
    $outItem = Get-Item $outputVideo
    $sizeMb = [math]::Round($outItem.Length / 1MB, 2)
    Write-Host ""
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host " FERTIG! Video erfolgreich gerendert ($sizeMb MB)" -ForegroundColor Green
    Write-Host " Speicherort: $outputVideo" -ForegroundColor White
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[FEHLER] Rendern fehlgeschlagen (Code $($process.ExitCode))" -ForegroundColor Red
}

if (-not $env:FLYT_NON_INTERACTIVE) {
    Write-Host "Drücke Enter zum Beenden..." -ForegroundColor Gray
    Read-Host | Out-Null
}
