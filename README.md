# uppo-status

Monitoraggio dei servizi Uppo e pagina di stato pubblica **[status.uppo.io](https://status.uppo.io)**.

```
Route 53 health checks          16 regioni, ogni 30 s, HTTPS
        │
        ├──→ allarmi CloudWatch  →  SNS  →  email
        │
        └──→ EventBridge (5 min) → Lambda → S3 → CloudFront → status.uppo.io
```

- **il codice** sta in [`monitoraggio/`](monitoraggio/) — la funzione, lo script di rilascio
  e la documentazione;
- **non c'è alcun workflow attivo** in questo repository, ed è deliberato: fino al 21/09/2026
  la pagina era generata da Upptime su GitHub Actions, il workflow ha smesso di partire per
  ragioni che non controlliamo, e per nove giorni la pagina ha dichiarato tutti i servizi
  funzionanti con tempo di risposta 0 ms — cioè ha mentito;
- **l'installazione Upptime precedente** è conservata in [`archivio/upptime/`](archivio/upptime/)
  con lo storico fino a quella data.

La pagina di oggi **si dichiara vecchia da sola**: se l'ultima misura supera i 20 minuti mostra
un avviso invece di continuare a dire «tutto bene». È la lezione di quei nove giorni: una
pagina di stato ferma è peggio di nessuna pagina.
