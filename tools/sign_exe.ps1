param(
    [string]$FilePath = ".\FF7EC_Decryptor.exe"
)

if (-not (Test-Path $FilePath)) {
    Write-Error "Target file does not exist: $FilePath"
    exit 1
}

$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -like '*InIntRios*' } | Select-Object -First 1

if (-not $cert) {
    Write-Host "[*] Creating local CodeSigning certificate for InIntRios..."
    $cert = New-SelfSignedCertificate -CertStoreLocation Cert:\CurrentUser\My -Subject "CN=InIntRios Open Source Developer" -Type CodeSigningCert -NotAfter (Get-Date).AddYears(5)
}

Write-Host "[*] Signing $FilePath with certificate $($cert.Thumbprint)..."
$sig = Set-AuthenticodeSignature -Certificate $cert -FilePath $FilePath -TimestampServer "http://timestamp.digicert.com"

if ($sig.Status -eq "Valid" -or $sig.Status -eq "UnknownError") {
    Write-Host "[+] Successfully embedded Authenticode digital signature and DigiCert timestamp."
} else {
    Write-Warning "Signature status: $($sig.Status) ($($sig.StatusMessage))"
}
