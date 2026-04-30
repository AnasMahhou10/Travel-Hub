# SupDeVinci Travel Hub — API NoSQL

Architecture polyglotte : Redis + MongoDB + Neo4j

## Stack

| Service     | Port      | Rôle                       |
| ----------- | --------- | -------------------------- |
| API FastAPI | 8000      | Endpoints HTTP             |
| Redis       | 6379      | Cache + Sessions + Pub/Sub |
| MongoDB     | 27017     | Catalogue offres           |
| Neo4j       | 7474/7687 | Graphe destinations        |

## Démarrage

```bash
docker-compose up --build
```

## Endpoints

| Route                   | Méthode | Description                              |
| ----------------------- | ------- | ---------------------------------------- |
| /offers                 | GET     | Recherche offres (cache Redis + MongoDB) |
| /offers/{id}            | GET     | Détail offre + relatedOffers Neo4j       |
| /reco                   | GET     | Recommandations villes via Neo4j         |
| /login                  | POST    | Session Redis UUID TTL 900s              |
| /stats/top-destinations | GET     | Agrégation MongoDB + cache Redis         |
| /metrics                | GET     | Métriques Prometheus                     |
| /notifications/stream   | GET     | Flux SSE branché sur Redis Pub/Sub       |

## Pub/Sub Redis

Quand `POST /offers` insere une offre dans MongoDB, l'API publie automatiquement un message JSON sur le canal Redis `offers:new`.

Tester dans deux terminaux :

```bash
redis-cli SUBSCRIBE offers:new
```

```bash
redis-cli PUBLISH offers:new '{"event":"offer.created","offerId":"demo","from":"PAR","to":"AMS"}'
```

Les clients web peuvent aussi ecouter `/notifications/stream`, qui transforme les messages Redis en Server-Sent Events.

## Équipe

- **[Ton prénom]** : GET /offers, GET /offers/{id}
- **Mariya** : GET /reco, Pub/Sub Redis
- **Anas** : POST /login, Extensions (/stats, /metrics)
