# Monitoraggio e pagina di stato

Questa cartella contiene **tutto il codice** di `status.uppo.io`. Prima viveva solo
dentro AWS, dove nessuno l'avrebbe ritrovato.

## Perché non è più Upptime

Upptime faceva due lavori con lo stesso strumento: controllare i servizi e pubblicare
la pagina. Il controllo girava su GitHub Actions ogni 5 minuti — 288 esecuzioni al
giorno — e questo repository è diventato **il primo consumatore di Actions
dell'organizzazione: 73.722 minuti nel 2026**, più di `uppo-backend` (49.045).

A settembre l'organizzazione ha superato il pacchetto incluso (52.421 minuti, per la
prima volta a pagamento) e GitHub ha iniziato a bloccare le esecuzioni: **1.000
consecutive** con esito `action_required`, compreso l'avvio manuale lanciato da un
amministratore.

Il monitor si è quindi spento da solo. E per nove giorni la pagina ha continuato a
dichiarare tutti i servizi «🟩 Up» con tempo di risposta **0 ms** — lo zero è la firma
del fatto che non stava misurando niente. Avrebbe mentito durante un guasto vero.

## Come funziona adesso

```
Route 53 health checks          16 regioni, ogni 30 s, HTTPS
        │                       (il controllo vero: fuori dal nostro compute)
        ├──→ allarmi CloudWatch  uppo-giu-*  →  SNS uppo-stato-servizi  →  email
        │
        └──→ EventBridge (5 min) → Lambda uppo-pagina-stato
                                      → s3://status.uppo.io (privato)
                                      → CloudFront → status.uppo.io
```

**La Lambda non controlla niente**: pubblica soltanto ciò che Route 53 ha già misurato.
La distinzione conta — se la Lambda si ferma, gli allarmi continuano a funzionare,
perché vivono su CloudWatch.

I controlli si trovano **per tag** (`gestito-da=sostituzione-upptime`), non da una lista
scritta nel codice: per aggiungere un servizio monitorato basta creare il health check
con quel tag e un tag `Name`, e comparirà nella pagina da solo. Nessuno deve ricordarsi
anche di questo file — che è esattamente il modo in cui queste cose si rompono.

## La pagina si dichiara vecchia da sola

Se l'ultima scrittura supera i **20 minuti**, la pagina mostra una fascia «Questa pagina
non è aggiornata» invece di continuare a dire «tutto bene». È la lezione diretta dei nove
giorni in cui ha mentito: **una pagina di stato ferma è peggio di nessuna pagina**.

## Modificare e rilasciare

```bash
# modifica monitoraggio/lambda_function.py, poi:
./monitoraggio/rilascia.sh
```

Non c'è una GitHub Action che rilasci al posto tuo, ed è deliberato: rimettere un
workflow in questo repository per risparmiare trenta secondi sarebbe ricominciare da
dove siamo partiti.

## Dove sono le cose

| cosa | dove |
|---|---|
| health check Route 53 | `uppo-app`, `uppo-api`, `uppo-portale`, `uppo-sso` (globali) |
| allarmi + topic SNS | **`us-east-1`** — le metriche dei health check esistono solo lì |
| Lambda + EventBridge | `eu-central-1`, `uppo-pagina-stato` / `uppo-pagina-stato-ogni-5min` |
| secchio | `s3://status.uppo.io` — **privato**, leggibile solo da CloudFront (OAC) |
| CloudFront | `EJO0Y78RMYOSX` → `d14bl5fgg238qv.cloudfront.net`, certificato `*.uppo.io` |
| DNS | `status.uppo.io` CNAME → CloudFront (prima: `uppo-helpdesk.github.io`) |

⚠️ Cercare allarmi o topic in `eu-central-1` non dà nulla: stanno in `us-east-1`.

## Costi

| | |
|---|---|
| 4 health check Route 53 | ~6 $/mese (0,50 $ ciascuno + 1 $ per HTTPS) |
| Lambda, 8.640 esecuzioni/mese | free tier permanente |
| S3 + CloudFront | trascurabile |
| GitHub Actions | **0** (erano ~35.000 minuti/mese) |

## Il resto del repository

I file di Upptime (`.upptimerc.yml`, `history/`, `api/`, i workflow) sono rimasti per lo
**storico fino al 21/09/2026**. `Uptime CI` e `Response Time CI` sono disabilitati: se
qualcuno li riattiva, il consumo riparte.
