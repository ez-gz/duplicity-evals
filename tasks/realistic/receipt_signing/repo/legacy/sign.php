<?php
// Legacy receipt signer (checkout v1). Kept for reference only; not deployed.

function ksort_recursive(array &$a): void {
    ksort($a, SORT_STRING);
    foreach ($a as &$v) {
        if (is_array($v)) {
            ksort_recursive($v);
        }
    }
}

function sign_receipt(array $receipt): string {
    unset($receipt['signature']);
    ksort_recursive($receipt);
    $json = json_encode($receipt, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    return hash_hmac('sha256', $json, getenv('RECEIPTS_SIGNING_KEY'));
}
