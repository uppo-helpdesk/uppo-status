# Archivio Upptime (fino al 21 settembre 2026)

Questa cartella contiene l'installazione Upptime che ha gestito `status.uppo.io` fino al
21/09/2026. **Non è più attiva e non deve tornare a esserlo.**

I workflow sono stati spostati qui dentro apposta: fuori da `.github/workflows/` GitHub non
li vede come workflow e non può eseguirli. Disabilitarli non bastava — `update-template.yml`
girava ogni notte e li **rigenerava** dalla configurazione.

## Cosa si è rotto, e cosa non sappiamo

**Quel che è verificato:**

- da almeno il 21/09/2026, **ogni** esecuzione di `Uptime CI` è finita con esito
  `action_required`: mille consecutive, compreso un avvio **manuale** lanciato da un
  amministratore dell'organizzazione. Il workflow non è mai partito;
- per **nove giorni** la pagina ha continuato a dichiarare tutti e quattro i servizi
  «🟩 Up» con tempo di risposta **0 ms**. Lo zero è la firma del fatto che non stava
  misurando niente. Avrebbe mentito durante un guasto vero;
- il consumo di Actions dell'organizzazione è cresciuto da 5.003 minuti/mese (febbraio) a
  52.421 (settembre), e a settembre ha superato per la prima volta il pacchetto incluso
  (€ 12,42 a pagamento).

**Quel che NON è vero**, e va detto perché è stato scritto altrove: lo sforamento non è
colpa di questo repository. `uppo-status` è **pubblico**, e sui repository pubblici i
minuti Actions su runner standard sono **gratuiti**. La riga di fatturazione di settembre
è attribuita a `tfc`, che è privato.

**Quel che resta ignoto:** *perché* GitHub blocchi queste esecuzioni. L'ipotesi non
dimostrata è che i controlli automatici di GitHub reagiscano a un cron ogni 5 minuti su un
repository pubblico. Non l'abbiamo provato.

## Perché allora si è cambiato lo stesso

Perché il motivo vero non è il costo: è che **un monitor che vive dentro GitHub Actions
dipende da un meccanismo che non controlliamo e che non sappiamo diagnosticare** — e ha
smesso di funzionare in silenzio per nove giorni senza che nessuno se ne accorgesse.

Il controllo ora lo fanno i health check di Route 53, da 16 regioni, con allarmi su
CloudWatch. Vedi `monitoraggio/LEGGIMI.md`.

## Cosa c'è qui dentro

| | |
|---|---|
| `workflows/` | gli otto workflow di Upptime, resi inerti spostandoli |
| `.upptimerc.yml` | la configurazione |
| `history/` | le misure storiche, una per servizio |
| `api/`, `graphs/`, `assets/` | dati e risorse della pagina generata |

Si conserva per lo storico. Se un giorno servisse riprendere quei dati, sono qui.
