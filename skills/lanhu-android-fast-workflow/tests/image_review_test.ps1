param([Parameter(Mandatory=$true)][string]$WorkDirectory)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$tool=Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/image_review.ps1'
$root=[IO.Path]::GetFullPath($WorkDirectory)
[IO.Directory]::CreateDirectory($root) | Out-Null
$work=Join-Path $root ('image-review-test-'+[guid]::NewGuid().ToString('N'))
$inputDir=Join-Path $work 'input'
$outputDir=Join-Path $work 'output'
[IO.Directory]::CreateDirectory($inputDir) | Out-Null
function Assert([bool]$Condition,[string]$Message) { if(-not $Condition){throw $Message} }
try {
    $fixture=Join-Path $inputDir 'transparent-fixture.png'
    $bitmap=[Drawing.Bitmap]::new(80,350,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $bitmap.SetResolution(144,144)
    $graphics=[Drawing.Graphics]::FromImage($bitmap)
    $brush=[Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(255,17,34,51))
    try { $graphics.Clear([Drawing.Color]::Transparent);$graphics.FillRectangle($brush,3,7,14,18);$bitmap.Save($fixture,[Drawing.Imaging.ImageFormat]::Png) }
    finally {$brush.Dispose();$graphics.Dispose();$bitmap.Dispose()}
    $original=[Convert]::ToBase64String([IO.File]::ReadAllBytes($fixture))
    $inspect=& $tool -Mode inspect -SourcePath $fixture -Points '3,7;0,0' | ConvertFrom-Json
    Assert (($inspect.alpha_bounds -join ',') -eq '3,7,14,18') 'Incorrect alpha bounds'
    Assert ($inspect.samples[0].argb -eq '#FF112233') 'Incorrect opaque pixel'
    Assert ($inspect.samples[1].argb.StartsWith('#00')) 'Transparent pixel lost'
    $tiles=& $tool -Mode tiles -SourcePath $fixture -OutputDirectory $outputDir -TileHeight 128 -Overlap 16 | ConvertFrom-Json
    $manifest=[IO.File]::ReadAllText($tiles.manifest) | ConvertFrom-Json
    Assert ($manifest.regions.Count -eq 3) 'Incorrect tile coverage'
    Assert (($manifest.regions[1].rect -join ',') -eq '0,112,80,128') 'Incorrect overlap coordinates'
    Assert (($manifest.regions[2].rect -join ',') -eq '0,224,80,126') 'Bottom pixels omitted'
    $cached=& $tool -Mode tiles -SourcePath $fixture -OutputDirectory $outputDir -TileHeight 128 -Overlap 16 | ConvertFrom-Json
    Assert $cached.cached 'Repeated run did not reuse cache'
    [IO.File]::WriteAllText($manifest.artifacts[0].path,'corrupted generated preview')
    $repaired=& $tool -Mode tiles -SourcePath $fixture -OutputDirectory $outputDir -TileHeight 128 -Overlap 16 | ConvertFrom-Json
    Assert (-not $repaired.cached) 'Corrupt cache was accepted'
    $crop=& $tool -Mode crop -SourcePath $fixture -OutputDirectory $outputDir -X 3 -Y 7 -Width 14 -Height 18 -Scale 2 | ConvertFrom-Json
    $cropManifest=[IO.File]::ReadAllText($crop.manifest) | ConvertFrom-Json
    $cropInfo=& $tool -Mode inspect -SourcePath $cropManifest.artifacts[0].path -Points '0,0' | ConvertFrom-Json
    Assert ($cropInfo.width -eq 28 -and $cropInfo.height -eq 36) 'Crop scale is incorrect'
    Assert ($cropInfo.samples[0].argb -eq '#FF112233') 'Crop pixel changed'
    $sheet=& $tool -Mode sheet -SourcePath $inputDir -OutputDirectory $outputDir | ConvertFrom-Json
    $sheetManifest=[IO.File]::ReadAllText($sheet.manifest) | ConvertFrom-Json
    Assert ($sheetManifest.regions[0].source -eq $fixture) 'Sheet lost source mapping'
    [IO.File]::WriteAllText((Join-Path $inputDir 'unsupported.svg'),'<svg/>')
    [IO.File]::Copy($fixture,(Join-Path $inputDir 'second.png'))
    $paged=& $tool -Mode sheet -SourcePath $inputDir -OutputDirectory $outputDir -PageSize 1 | ConvertFrom-Json
    Assert ($paged.coverage.pages -eq 2 -and $paged.coverage.next_page -eq 2) 'Missing page coverage'
    Assert ($paged.coverage.omitted_supported_files -eq 1) 'Missing omitted count'
    Assert ($paged.coverage.skipped_files -contains 'unsupported.svg') 'Mixed unsupported file silently omitted'
    Assert ($paged.previews.Count -eq 1 -and $paged.review_status -eq 'generated_not_visually_reviewed') 'Misleading review status'
    $pagedAgain=& $tool -Mode sheet -SourcePath $inputDir -OutputDirectory $outputDir -PageSize 1 | ConvertFrom-Json
    Assert ($pagedAgain.cached -and $pagedAgain.coverage.next_page -eq 2) 'Cached coverage lost'
    $lastPage=& $tool -Mode sheet -SourcePath $inputDir -OutputDirectory $outputDir -PageSize 1 -Page 2 | ConvertFrom-Json
    Assert ($null -eq $lastPage.coverage.next_page) 'Incorrect last-page state'
    $changed=[Drawing.Bitmap]::new(2,2)
    try {$changed.Save((Join-Path $inputDir 'second.png'),[Drawing.Imaging.ImageFormat]::Png)}finally{$changed.Dispose()}
    $changedPage=& $tool -Mode sheet -SourcePath $inputDir -OutputDirectory $outputDir -PageSize 1 | ConvertFrom-Json
    Assert (-not $changedPage.cached -and $changedPage.manifest -ne $paged.manifest) 'Changed source did not invalidate cache'
    $rejected=$false
    try { $null=& $tool -Mode crop -SourcePath $fixture -OutputDirectory $outputDir -X 79 -Width 2 -Height 2 } catch {$rejected=$true}
    Assert $rejected 'Out-of-bounds crop was accepted'
    $rejected=$false
    try { $null=& $tool -Mode tiles -SourcePath $fixture -OutputDirectory (Join-Path $inputDir 'nested') } catch {$rejected=$true}
    Assert $rejected 'Output inside input directory was accepted'
    Assert ($original -eq [Convert]::ToBase64String([IO.File]::ReadAllBytes($fixture))) 'Original file changed'
    Write-Output 'PASS: alpha/DPI, sampling, tiles, crop, sheet mapping/pages/unsupported files, cache reuse/repair/invalidation, invalid input and original preservation.'
} finally {
    $resolved=[IO.Path]::GetFullPath($work)
    if((Split-Path -Parent $resolved) -ne $root -or (Split-Path -Leaf $resolved) -notlike 'image-review-test-*'){throw 'Unsafe test cleanup path'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
