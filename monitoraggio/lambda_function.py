"""
Genera la pagina di stato pubblica di Uppo su S3.

PERCHE' ESISTE
--------------
Sostituisce Upptime, che faceva due lavori con lo stesso strumento: controllare
i servizi e pubblicare la pagina. Il controllo ogni 5 minuti su GitHub Actions
e' costato 73.722 minuti nel 2026 — piu' di tutto il backend — finche'
l'organizzazione ha sfondato il pacchetto incluso e GitHub ha smesso di
eseguire. Il monitor si e' spento da solo, e per nove giorni la pagina ha
continuato a dichiarare tutti i servizi «Up» con tempo di risposta 0 ms.

Ora il controllo lo fanno i health check di Route 53, da 16 regioni, ogni 30
secondi. Questa funzione NON controlla niente: si limita a PUBBLICARE cio' che
Route 53 ha gia' misurato. La distinzione conta: se questa funzione si ferma,
gli allarmi continuano a funzionare lo stesso, perche' vivono su CloudWatch.

LA REGOLA CHE LA PAGINA DEVE RISPETTARE
---------------------------------------
Una pagina di stato ferma e' peggio di nessuna pagina: dice «tutto bene» quando
non sta guardando. Percio' ogni pagina generata porta l'ora in cui e' stata
scritta, e il browser di chi la legge dichiara il dato VECCHIO se supera la
soglia — senza aspettare che ce ne accorgiamo noi.
"""

import datetime
import html
import json
import os

import boto3

SECCHIO = os.environ.get("SECCHIO", "status.uppo.io")
TAG_GESTIONE = "sostituzione-upptime"
# Oltre questa eta', la pagina si dichiara non aggiornata invece di mostrare
# uno stato che non sta piu' misurando.
SOGLIA_STANTIO_MIN = 20

r53 = boto3.client("route53")
s3 = boto3.client("s3")


def _controlli():
    """I health check che questa pagina deve mostrare, trovati per TAG.

    Per tag e non per lista scritta a mano: aggiungere un servizio da monitorare
    non deve richiedere di ricordarsi anche di questa funzione.
    """
    ids = []
    for pagina in r53.get_paginator("list_health_checks").paginate():
        ids += [h["Id"] for h in pagina["HealthChecks"]]
    if not ids:
        return []

    nomi = {}
    for i in range(0, len(ids), 10):  # l'API accetta al massimo 10 risorse
        risposta = r53.list_tags_for_resources(ResourceType="healthcheck", ResourceIds=ids[i:i + 10])
        for insieme in risposta["ResourceTagSets"]:
            tag = {t["Key"]: t["Value"] for t in insieme["Tags"]}
            if tag.get("gestito-da") == TAG_GESTIONE:
                nomi[insieme["ResourceId"]] = tag.get("Name", insieme["ResourceId"])
    return sorted(nomi.items(), key=lambda x: x[1])


def _stato(id_controllo):
    """Quante regioni vedono il servizio raggiungibile."""
    osservazioni = r53.get_health_check_status(HealthCheckId=id_controllo)["HealthCheckObservations"]
    totale = len(osservazioni)
    ok = sum(1 for o in osservazioni
             if o.get("StatusReport", {}).get("Status", "").startswith("Success"))
    return ok, totale


ETICHETTE = {
    "uppo-app": ("Console Uppo", "app.uppo.io"),
    "uppo-api": ("API", "api.uppo.io"),
    "uppo-portale": ("Portale self-service", "uppohelpdesk.portal.uppo.io"),
    "uppo-sso": ("Accesso (SSO)", "sso.uppo.io"),
}


def _pagina(righe, adesso):
    giu = [r for r in righe if r["ok"] == 0]
    parziale = [r for r in righe if 0 < r["ok"] < r["totale"]]

    if giu:
        titolo, classe = ("Disservizio in corso", "giu")
    elif parziale:
        titolo, classe = ("Raggiungibilità ridotta", "parziale")
    else:
        titolo, classe = ("Tutti i servizi funzionano", "su")

    voci = []
    for r in righe:
        nome, dominio = ETICHETTE.get(r["id"], (r["id"], ""))
        if r["ok"] == 0:
            stato, cls = "Non raggiungibile", "giu"
        elif r["ok"] < r["totale"]:
            stato, cls = f"Raggiungibile da {r['ok']} regioni su {r['totale']}", "parziale"
        else:
            stato, cls = "Funziona", "su"
        voci.append(
            f'<li class="{cls}"><div><b>{html.escape(nome)}</b>'
            f'<span class="dom">{html.escape(dominio)}</span></div>'
            f'<span class="stato">{html.escape(stato)}</span></li>'
        )

    return f"""<!doctype html>
<html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stato dei servizi Uppo</title>
<link rel="icon" href="data:,">
<style>
:root{{--fondo:#F2F5F5;--carta:#fff;--inchiostro:#0E1A1F;--tenue:#56696E;--linea:#D7E0E1;
--su:#1C6B47;--su-b:#E0EFE7;--parziale:#8A5A0B;--parziale-b:#F6EBD8;--giu:#8A3324;--giu-b:#F6E5E1;}}
@media(prefers-color-scheme:dark){{:root{{--fondo:#0B1315;--carta:#111D20;--inchiostro:#E7EEEF;
--tenue:#94A7AB;--linea:#22353A;--su:#6FCB9C;--su-b:#10261D;--parziale:#E0AC5C;--parziale-b:#2A2113;
--giu:#E8907C;--giu-b:#2C1915;}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--fondo);color:var(--inchiostro);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.c{{max-width:680px;margin:0 auto;padding:56px 22px 80px}}
h1{{font-size:clamp(25px,4vw,34px);margin:0 0 6px;letter-spacing:-.01em}}
h1.su{{color:var(--su)}} h1.parziale{{color:var(--parziale)}} h1.giu{{color:var(--giu)}}
.quando{{color:var(--tenue);font-size:14px;margin:0 0 30px}}
ul{{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:9px}}
li{{background:var(--carta);border:1px solid var(--linea);border-radius:10px;padding:14px 17px;
display:flex;justify-content:space-between;align-items:center;gap:16px;border-left-width:4px}}
li.su{{border-left-color:var(--su)}} li.parziale{{border-left-color:var(--parziale)}}
li.giu{{border-left-color:var(--giu)}}
.dom{{display:block;color:var(--tenue);font-size:13px;margin-top:1px}}
.stato{{font-size:13px;font-weight:700;padding:4px 10px;border-radius:999px;white-space:nowrap;text-align:right}}
li.su .stato{{background:var(--su-b);color:var(--su)}}
li.parziale .stato{{background:var(--parziale-b);color:var(--parziale)}}
li.giu .stato{{background:var(--giu-b);color:var(--giu)}}
#stantio{{display:none;background:var(--parziale-b);color:var(--parziale);border:1px solid var(--parziale);
border-radius:10px;padding:13px 17px;margin-bottom:22px;font-size:14.5px}}
footer{{margin-top:34px;color:var(--tenue);font-size:13px;line-height:1.7}}
</style></head><body><div class="c">
<div id="stantio"><b>Questa pagina non è aggiornata.</b> L'ultima misura risale a più di {SOGLIA_STANTIO_MIN} minuti fa,
quindi lo stato qui sotto potrebbe non riflettere la situazione attuale.</div>
<h1 class="{classe}">{titolo}</h1>
<p class="quando">Ultima verifica: <span id="quando">{adesso.strftime('%d/%m/%Y %H:%M')} UTC</span></p>
<ul>{''.join(voci)}</ul>
<footer>Ogni servizio è controllato da 16 regioni del mondo, ogni 30 secondi.
«Raggiungibile da N regioni» significa che il servizio risponde, ma non da ovunque.</footer>
</div>
<script>
// La pagina si dichiara vecchia da sola: una pagina di stato ferma che dice
// «tutto bene» e' peggio di nessuna pagina.
(function(){{
  var scritta = new Date("{adesso.isoformat()}Z");
  var minuti = (Date.now() - scritta.getTime()) / 60000;
  if (minuti > {SOGLIA_STANTIO_MIN}) document.getElementById('stantio').style.display = 'block';
  try {{
    document.getElementById('quando').textContent =
      scritta.toLocaleString('it-IT', {{dateStyle:'short', timeStyle:'short'}});
  }} catch (e) {{}}
}})();
</script></body></html>"""


def lambda_handler(event, context):
    adesso = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None)

    righe = []
    for id_controllo, nome in _controlli():
        ok, totale = _stato(id_controllo)
        righe.append({"id": nome, "ok": ok, "totale": totale})

    if not righe:
        # Nessun controllo trovato: NON si pubblica una pagina «tutto bene» vuota.
        raise RuntimeError("nessun health check con tag gestito-da=" + TAG_GESTIONE)

    s3.put_object(Bucket=SECCHIO, Key="index.html",
                  Body=_pagina(righe, adesso).encode("utf-8"),
                  ContentType="text/html; charset=utf-8",
                  CacheControl="public, max-age=60")

    s3.put_object(Bucket=SECCHIO, Key="status.json",
                  Body=json.dumps({"aggiornato": adesso.isoformat() + "Z", "servizi": righe},
                                  ensure_ascii=False).encode("utf-8"),
                  ContentType="application/json",
                  CacheControl="public, max-age=60")

    return {"servizi": len(righe), "aggiornato": adesso.isoformat() + "Z"}
