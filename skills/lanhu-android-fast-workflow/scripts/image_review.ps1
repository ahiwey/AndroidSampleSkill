param(
    [Parameter(Mandatory=$true)][ValidateSet('tiles','sheet','crop','inspect')][string]$Mode,
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [string]$OutputDirectory,
    [ValidateRange(128,2048)][int]$TileHeight = 1600,
    [ValidateRange(0,512)][int]$Overlap = 120,
    [int]$X = 0, [int]$Y = 0, [int]$Width = 0, [int]$Height = 0,
    [ValidateRange(1,4)][int]$Scale = 2,
    [ValidateRange(1,24)][int]$PageSize = 12,
    [ValidateRange(1,10000)][int]$Page = 1,
    [string]$Points = ''
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
if (-not ('ReviewAlphaBounds' -as [type])) {
    Add-Type -TypeDefinition @'
public static class ReviewAlphaBounds {
    public static int[] Find(byte[] data, int width, int height) {
        int left=width, top=height, right=-1, bottom=-1;
        for (int y=0; y<height; y++) for (int x=0; x<width; x++) {
            if (data[(y*width+x)*4+3] == 0) continue;
            if(x<left) left=x; if(x>right) right=x;
            if(y<top) top=y; if(y>bottom) bottom=y;
        }
        return right<0 ? new int[0] : new int[]{left,top,right-left+1,bottom-top+1};
    }
}
'@
}
function Get-Digest([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
}
function Write-Summary($Report,[bool]$Cached,[string]$Manifest) {
    [ordered]@{status='ok';cached=$Cached;manifest=$Manifest;artifacts=@($Report.artifacts).Count;
        previews=@($Report.artifacts | ForEach-Object {$_.path});coverage=$Report.coverage;
        review_status='generated_not_visually_reviewed'} | ConvertTo-Json -Depth 6 -Compress
}
function Open-Bitmap([string]$Path) {
    $image = [Drawing.Image]::FromFile($Path)
    try {
        if ([long]$image.Width*$image.Height -gt 40000000) { throw 'Image exceeds 40 MP limit' }
        if ($image.PropertyIdList -contains 274) {
            $orientation = [BitConverter]::ToUInt16($image.GetPropertyItem(274).Value,0)
            if ($orientation -ne 1) { throw 'EXIF orientation requires explicit normalization before coordinate review' }
        }
        $bitmap = [Drawing.Bitmap]::new($image.Width,$image.Height,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            # Explicit pixel rectangles avoid DPI metadata changing the copied area.
            $graphics.CompositingMode = [Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.DrawImage($image,[Drawing.Rectangle]::new(0,0,$image.Width,$image.Height),0,0,$image.Width,$image.Height,[Drawing.GraphicsUnit]::Pixel)
        } finally { $graphics.Dispose() }
        return $bitmap
    } finally { $image.Dispose() }
}
function Get-AlphaBounds([Drawing.Bitmap]$Bitmap) {
    $rect = [Drawing.Rectangle]::new(0,0,$Bitmap.Width,$Bitmap.Height)
    $locked = $Bitmap.LockBits($rect,[Drawing.Imaging.ImageLockMode]::ReadOnly,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $rowBytes = $Bitmap.Width*4
        $bytes = [byte[]]::new($rowBytes*$Bitmap.Height)
        for ($row=0; $row -lt $Bitmap.Height; $row++) {
            [Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($locked.Scan0,$row*$locked.Stride),$bytes,$row*$rowBytes,$rowBytes)
        }
        return ,([ReviewAlphaBounds]::Find($bytes,$Bitmap.Width,$Bitmap.Height))
    } finally { $Bitmap.UnlockBits($locked) }
}
function Save-Png([Drawing.Bitmap]$Bitmap,[string]$Name) {
    $path = Join-Path $runDirectory $Name
    $Bitmap.Save($path,[Drawing.Imaging.ImageFormat]::Png)
    $artifacts.Add([ordered]@{path=$path;sha256=(Get-Digest $path)})
    return $path
}
function New-Region([Drawing.Bitmap]$Image,[int]$Left,[int]$Top,[int]$W,[int]$H,[int]$Zoom) {
    if ($Left -lt 0 -or $Top -lt 0 -or $W -le 0 -or $H -le 0 -or $Left+$W -gt $Image.Width -or $Top+$H -gt $Image.Height) { throw 'Region outside image' }
    if ([long]$W*$H*$Zoom*$Zoom -gt 40000000) { throw 'Output exceeds 40 MP limit' }
    $bitmap = [Drawing.Bitmap]::new($W*$Zoom,$H*$Zoom,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        $graphics.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
        $graphics.DrawImage($Image,[Drawing.Rectangle]::new(0,0,$W*$Zoom,$H*$Zoom),$Left,$Top,$W,$H,[Drawing.GraphicsUnit]::Pixel)
    } finally { $graphics.Dispose() }
    return $bitmap
}

$source = (Resolve-Path -LiteralPath $SourcePath).Path
if ($Mode -eq 'inspect') {
    $bitmap = Open-Bitmap $source
    try {
        $samples = @()
        if ($Points) {
            foreach ($point in $Points.Split(';')) {
                if ($point -notmatch '^(\d+),(\d+)$') { throw 'Points format: x,y;x,y' }
                $px=[int]$Matches[1]; $py=[int]$Matches[2]
                if ($px -ge $bitmap.Width -or $py -ge $bitmap.Height) { throw 'Sample outside image' }
                $color=$bitmap.GetPixel($px,$py)
                $samples += [ordered]@{x=$px;y=$py;argb=('#{0:X2}{1:X2}{2:X2}{3:X2}' -f $color.A,$color.R,$color.G,$color.B)}
            }
        }
        [ordered]@{source=$source;width=$bitmap.Width;height=$bitmap.Height;sha256=(Get-Digest $source);alpha_bounds=(Get-AlphaBounds $bitmap);samples=$samples;note='Coordinates are source pixels. Screenshot samples are composited colors, not design layer colors.'} | ConvertTo-Json -Depth 6 -Compress
    } finally { $bitmap.Dispose() }
    exit 0
}
if (-not $OutputDirectory) { throw 'OutputDirectory is required for generated previews' }
if ($Overlap -ge $TileHeight) { throw 'Overlap must be smaller than TileHeight' }
$output = [IO.Path]::GetFullPath($OutputDirectory)
$sourceDirectory = if (Test-Path -LiteralPath $source -PathType Container) { $source } else { Split-Path -Parent $source }
if ($output.TrimEnd('\','/') -eq $sourceDirectory.TrimEnd('\','/') -or $output.StartsWith($sourceDirectory.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be outside source directory' }
if ($Mode -eq 'sheet') {
    $directoryFiles = @(Get-ChildItem -LiteralPath $source -File | Sort-Object Name)
    $allFiles = @($directoryFiles | Where-Object { $_.Extension.ToLowerInvariant() -in @('.png','.jpg','.jpeg','.bmp','.gif') })
    $skipped = @($directoryFiles | Where-Object { $_.Extension.ToLowerInvariant() -notin @('.png','.jpg','.jpeg','.bmp','.gif') } | ForEach-Object {$_.Name})
    if ($allFiles.Count -eq 0) { throw 'No supported raster files found; WebP/SVG require another decoder' }
    $files = @($allFiles | Select-Object -Skip (($Page-1)*$PageSize) -First $PageSize)
    if ($files.Count -eq 0) { throw 'Page outside file list' }
} else { $files = @(Get-Item -LiteralPath $source); $allFiles = $files; $skipped=@() }
$inputInfo = @($files | ForEach-Object { [ordered]@{path=$_.FullName;sha256=(Get-Digest $_.FullName)} })
$settings = [ordered]@{mode=$Mode;inputs=$inputInfo;script=(Get-Digest $PSCommandPath);tile_height=$TileHeight;overlap=$Overlap;x=$X;y=$Y;width=$Width;height=$Height;scale=$Scale;page_size=$PageSize;page=$Page;file_count=$allFiles.Count;skipped_files=$skipped}
$settingsJson = $settings | ConvertTo-Json -Depth 6 -Compress
$sha = [Security.Cryptography.SHA256]::Create()
try { $cacheKey = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($settingsJson)))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
$runDirectory = Join-Path $output $cacheKey
$manifestPath = Join-Path $runDirectory 'manifest.json'
if (Test-Path -LiteralPath $manifestPath) {
    try {
        $cached = [IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
        $valid = $cached.cache_key -eq $cacheKey -and @($cached.artifacts).Count -gt 0
        foreach ($artifact in $cached.artifacts) {
            $artifactPath = [IO.Path]::GetFullPath($artifact.path)
            if (-not $artifactPath.StartsWith($runDirectory+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $artifactPath) -or (Get-Digest $artifactPath) -ne $artifact.sha256) { $valid=$false; break }
        }
        if ($valid) { Write-Summary $cached $true $manifestPath; exit 0 }
    } catch { $valid=$false }
}
[IO.Directory]::CreateDirectory($runDirectory) | Out-Null
$artifacts = [Collections.Generic.List[object]]::new()
$regions = [Collections.Generic.List[object]]::new()
if ($Mode -eq 'tiles' -or $Mode -eq 'crop') {
    $bitmap = Open-Bitmap $source
    try {
        if ($Mode -eq 'crop') {
            $region = New-Region $bitmap $X $Y $Width $Height $Scale
            try { $regions.Add([ordered]@{source=$source;rect=@($X,$Y,$Width,$Height);scale=$Scale;preview=(Save-Png $region 'crop.png')}) } finally { $region.Dispose() }
        } else {
            if ($bitmap.Width -gt 2048) { throw 'Source wider than 2048 px; use explicit crop regions to avoid automatic shrinkage' }
            $top=0; $index=1
            while ($top -lt $bitmap.Height) {
                $h=[Math]::Min($TileHeight,$bitmap.Height-$top)
                $region = New-Region $bitmap 0 $top $bitmap.Width $h 1
                try { $regions.Add([ordered]@{source=$source;rect=@(0,$top,$bitmap.Width,$h);scale=1;preview=(Save-Png $region ('tile-{0:D3}-y{1}.png' -f $index,$top))}) } finally { $region.Dispose() }
                if ($top+$h -ge $bitmap.Height) { break }
                $top += $TileHeight-$Overlap; $index++
            }
        }
    } finally { $bitmap.Dispose() }
} else {
    $columns=3; $cellW=320; $cellH=180
    $sheet = [Drawing.Bitmap]::new($columns*$cellW,[int][Math]::Ceiling($files.Count/$columns)*$cellH)
    $graphics = [Drawing.Graphics]::FromImage($sheet)
    $font = [Drawing.Font]::new('Microsoft YaHei',10,[Drawing.FontStyle]::Regular,[Drawing.GraphicsUnit]::Pixel)
    $light = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(240,240,240))
    $dark = [Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(38,45,51))
    try {
        $graphics.Clear([Drawing.Color]::White)
        $graphics.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        for ($i=0; $i -lt $files.Count; $i++) {
            $cx=($i%$columns)*$cellW; $cy=[int][Math]::Floor($i/$columns)*$cellH
            $bitmap=Open-Bitmap $files[$i].FullName
            try {
                $id=($Page-1)*$PageSize+$i+1
                $label=('{0:D3} {1}' -f $id,$files[$i].Name)
                $graphics.DrawString($label,$font,[Drawing.Brushes]::Black,[Drawing.RectangleF]::new($cx+5,$cy+4,$cellW-10,32))
                $graphics.DrawString(('{0} x {1} px' -f $bitmap.Width,$bitmap.Height),$font,[Drawing.Brushes]::Black,$cx+5,$cy+34)
                $zoom=[Math]::Min(3,[Math]::Min(140.0/$bitmap.Width,120.0/$bitmap.Height))
                $w=[int][Math]::Max(1,[Math]::Round($bitmap.Width*$zoom)); $h=[int][Math]::Max(1,[Math]::Round($bitmap.Height*$zoom))
                foreach ($side in @(0,1)) {
                    $brush=if($side -eq 0){$light}else{$dark}
                    $graphics.FillRectangle($brush,$cx+5+$side*158,$cy+50,152,125)
                    $graphics.DrawImage($bitmap,[Drawing.Rectangle]::new([int]($cx+5+$side*158+(152-$w)/2),[int]($cy+50+(125-$h)/2),$w,$h))
                }
                $regions.Add([ordered]@{id=$id;source=$files[$i].FullName;sha256=$inputInfo[$i].sha256;size=@($bitmap.Width,$bitmap.Height);sheet_cell=@($cx,$cy,$cellW,$cellH);preview_scale=$zoom})
            } finally { $bitmap.Dispose() }
        }
        $null=Save-Png $sheet ('sheet-{0:D3}.png' -f $Page)
    } finally { $graphics.Dispose();$sheet.Dispose();$font.Dispose();$light.Dispose();$dark.Dispose() }
}
$pageCount=if($Mode -eq 'sheet'){[int][Math]::Ceiling($allFiles.Count/[double]$PageSize)}else{1}
$coverage=[ordered]@{supported_files=$allFiles.Count;selected_files=$files.Count;page=$Page;pages=$pageCount;
    next_page=$(if($Mode -eq 'sheet' -and $Page -lt $pageCount){$Page+1}else{$null});
    omitted_supported_files=$allFiles.Count-$files.Count;skipped_files=$skipped;regions=$regions.Count;
    note='Coverage describes generated previews, not human/model inspection. Other sheet pages are not covered by this call.'}
$report=[ordered]@{schema_version=2;cache_key=$cacheKey;settings=$settings;coverage=$coverage;regions=@($regions.ToArray());artifacts=@($artifacts.ToArray());note='Review derivatives only; originals unchanged. Not an App screenshot. Sheet previews are not exact color or size measurements.'}
[IO.File]::WriteAllText($manifestPath,($report | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
Write-Summary $report $false $manifestPath
