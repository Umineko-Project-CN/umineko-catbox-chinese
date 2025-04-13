#!/usr/bin/pwsh
# Build requirements: Python 3, Ruby, .NET Runtime
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$restore = $args.Count -gt 0 -and $args[0] -eq '-r'
Write-Host $(if ($restore) { "@@ Restored @@" } else { "@@ Standard @@" })
Write-Host "=== Preparing files... ==="
New-Item -ItemType Directory -Path ./romfs -Force | Out-Null
Copy-Item -Recurse -Force ./romfs_standard/* ./romfs
if ($restore) {
    Copy-Item -Recurse -Force ./romfs_restored/* ./romfs
}
Copy-Item -Recurse -Force $(if ($restore) { './script_restored.rb' } else { './script_standard.rb' })  ./script.rb

if (Test-Path font_manifests) {
    Write-Host "=== Copying font manifests... ==="
    Copy-Item font_manifests/regular repack/rom-repack/font/regular -Force
    Copy-Item font_manifests/bold repack/rom-repack/font/bold -Force
    Write-Host "=== Running localization script... ==="
    dotnet fsi ./ReplaceChars.fsx
}

Write-Host "=== Building romfs... ==="
Set-Location repack/rom-repack
ruby kal_real.rb ../../script.rb ../../romfs ../../patch.rom ../../patch.snr 6 19 88
Set-Location ../..

Write-Host "=== Building exefs... ==="
python build_exefs_text.py

Write-Host "=== Generating mod directory structure... ==="
$MODBASE = "mods/contents/01006a300ba2c000/"
New-Item -ItemType Directory -Path $MODBASE/romfs -Force | Out-Null
Move-Item patch.rom $MODBASE/romfs/patch.rom -Force
Copy-Item exefs $MODBASE -Recurse -Force
New-Item -ItemType Directory -Path mods/exefs_patches/umineko -Force | Out-Null
Move-Item 7616F8963DACCD70E20FF3904E13367F96F2D9B3000000000000000000000000.ips mods/exefs_patches/umineko/ -Force
Remove-Item patch.snr -Force

Write-Host "=== Deploying... ==="
if (Test-Path env:UMINEKO_TARGET) {
    # Local/dev build
    Copy-Item mods $env:UMINEKO_TARGET -Recurse -Force
    Remove-Item mods -Recurse -Force
}
elseif (Test-Path env:UMINEKO_TARGET_YUZU) {
    # Local/dev build
    $MODBASE_YUZU = "$env:UMINEKO_TARGET_YUZU/load/01006A300BA2C000/UminekoCatboxChinese"
    New-Item -ItemType Directory -Path $MODBASE_YUZU -Force | Out-Null
    Copy-Item $MODBASE/* $MODBASE_YUZU/ -Recurse -Force
    Copy-Item mods/exefs_patches/umineko/*.ips $MODBASE_YUZU/exefs/ -Force
    Remove-Item mods -Recurse -Force
}
else {
    # Public build
    $suffix = if ($restore) { '_restored' } else { '_standard' }
    Set-Location mods
    if ($env:SKIP_ARCHIVE -ne "1") {
        Compress-Archive -Path * -DestinationPath "../patch_atmos$suffix.zip" -Force
    }
    Set-Location ..
    
    New-Item -ItemType Directory -Path UminekoCatboxChinese -Force | Out-Null
    Copy-Item $MODBASE/* UminekoCatboxChinese/ -Recurse -Force
    Copy-Item mods/exefs_patches/umineko/*.ips UminekoCatboxChinese/exefs/ -Force
    
    if ($env:SKIP_ARCHIVE -ne "1") {
        Compress-Archive -Path UminekoCatboxChinese -DestinationPath "patch_yuzu$suffix.zip" -Force
    }
}

Write-Host "=== Cleaning up... ==="
Remove-Item -Recurse -Force ./romfs
Remove-Item -Force ./script.rb