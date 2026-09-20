# Generates a PKCE code_verifier and S256 code_challenge.

function ConvertTo-Base64UrlNoPadding {
    param(
        [Parameter(Mandatory = $true)]
        [byte[]]$Bytes
    )

    [Convert]::ToBase64String($Bytes).
        TrimEnd('=').
        Replace('+', '-').
        Replace('/', '_')
}

$randomBytes = New-Object byte[] 64
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $rng.GetBytes($randomBytes)
}
finally {
    $rng.Dispose()
}

$verifier = ConvertTo-Base64UrlNoPadding -Bytes $randomBytes

$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $challengeBytes = $sha256.ComputeHash(
        [System.Text.Encoding]::ASCII.GetBytes($verifier)
    )
}
finally {
    $sha256.Dispose()
}

$challenge = ConvertTo-Base64UrlNoPadding -Bytes $challengeBytes

"code_verifier=$verifier"
"code_challenge=$challenge"
"code_challenge_method=S256"
