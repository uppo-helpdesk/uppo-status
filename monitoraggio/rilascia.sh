#!/usr/bin/env bash
#
# Rilascia la funzione che genera la pagina di stato.
#
# Non c'e' una GitHub Action che lo faccia, ed e' deliberato: questo repository
# ha consumato 73.722 minuti di Actions nel 2026 — piu' di uppo-backend — ed e'
# il motivo per cui il monitor si e' bloccato. Rimetterci dentro un workflow
# per risparmiare trenta secondi di lavoro manuale sarebbe ricominciare.
#
# Uso:  ./monitoraggio/rilascia.sh
set -euo pipefail

CARTELLA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUNZIONE="uppo-pagina-stato"
REGIONE="eu-central-1"
PROFILO="${AWS_PROFILE:-uppo}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cp "$CARTELLA/lambda_function.py" "$TMP/"
( cd "$TMP" && zip -q pacchetto.zip lambda_function.py )

echo "Carico $FUNZIONE ($REGIONE, profilo $PROFILO)…"
aws lambda update-function-code \
  --function-name "$FUNZIONE" \
  --zip-file "fileb://$TMP/pacchetto.zip" \
  --region "$REGIONE" --profile "$PROFILO" \
  --query '{stato:LastUpdateStatus,dimensione:CodeSize}' --output table

echo "Attendo che sia pronta…"
aws lambda wait function-updated --function-name "$FUNZIONE" --region "$REGIONE" --profile "$PROFILO"

echo "Eseguo una volta per rigenerare la pagina…"
aws lambda invoke --function-name "$FUNZIONE" --region "$REGIONE" --profile "$PROFILO" \
  --cli-binary-format raw-in-base64-out --payload '{}' "$TMP/esito.json" >/dev/null
cat "$TMP/esito.json"; echo

echo "Fatto. Verifica su https://status.uppo.io (la cache dura 60 secondi)."
