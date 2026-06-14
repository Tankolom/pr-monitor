# Kak dat dostup drugim lyudyam

Tekushchaya versiya - eto lokalnyy MVP. Ego mozhno dat drugim lyudyam dvumya sposobami.

## Variant 1. Bystryy dostup vnutri ofisa / domashney seti

1. Zapustite panel ne tolko dlya `127.0.0.1`, a dlya vseh ustroystv v seti:

```bash
MENTION_MONITOR_USER=admin MENTION_MONITOR_PASSWORD=change-me \
/Users/leonid.ivanenkov/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 run.py server --host 0.0.0.0 --port 8765
```

2. Uznayte IP adres vashego Mac v lokalnoy seti:

```bash
ipconfig getifaddr en0
```

3. Drugim lyudyam dayte adres:

```text
http://VASH-IP:8765/
```

Login po umolchaniyu v primere:

```text
admin
change-me
```

Parol nuzhno zamenit na svoi.

## Variant 2. Dostup cherez internet

Dlya realnogo ispolzovaniya neskolkimi lyudmi luchshe razvernut na VPS/cloud-servere:

- arendovat server;
- skopirovat papku proekta;
- zapustit programmu kak servis;
- postavit HTTPS domen;
- vklyuchit parol ili normalnuyu avtorizaciyu;
- nastroit raspisanie sbora `run.py watch --minutes 30`.

## Chto vazhno

- Ne publikuyte panel v internet bez parolya.
- Tekushchaya versiya ispolzuet SQLite, eto normalno dlya MVP i maloy komandy.
- Dlya produkta nuzhno dobavit polzovateley, roli, HTTPS, backup bazy i ochered fonovyh zadaniy.
