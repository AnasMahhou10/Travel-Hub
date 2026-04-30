# SupDeVinci Travel Hub - API NoSQL

Travel Hub est une API FastAPI qui démontre une architecture NoSQL polyglotte autour de trois bases :

- MongoDB pour stocker le catalogue des offres de voyage.
- Redis pour le cache, les sessions, les métriques et les notifications temps réel avec Pub/Sub.
- Neo4j pour les recommandations de destinations liées par graphe.

Une interface de test est disponible sur `http://localhost:8000`.

## Répartition

| Personne | Fonctionnalités |
| -------- | --------------- |
| Amina | Offres, offre par id, notifications temps réel |
| Mariya | Recommandations, top destinations |
| Anas | Login, métriques |

## Stack

| Service | Port | Rôle |
| ------- | ---- | ---- |
| API FastAPI | `8000` | Endpoints HTTP + interface web |
| Redis | `6379` | Cache, sessions, Pub/Sub, métriques |
| MongoDB | `27017` | Catalogue des offres |
| Neo4j | `7474`, `7687` | Graphe des destinations |

## Démarrage

```bash
docker compose up --build
```

Puis ouvrir :

```text
http://localhost:8000
```

Documentation Swagger :

```text
http://localhost:8000/docs
```

## Données initiales

MongoDB est initialisé avec `scripts/mongo-init.js`.

La collection `offers` contient des offres avec :

- une ville de départ : `from`
- une destination : `to`
- des dates : `departDate`, `returnDate`
- un fournisseur : `provider`
- un prix : `price`
- une devise : `currency`
- des vols : `legs`
- éventuellement un hôtel et une activité

Neo4j est initialisé avec `scripts/neo4j-init.cypher` pour créer un graphe de villes proches.

## Endpoints

<<<<<<< HEAD
| Route | Méthode | Description |
| ----- | ------- | ----------- |
| `/offers` | `GET` | Recherche les offres avec cache Redis |
| `/offers/{offer_id}` | `GET` | Retourne le détail d'une offre et des offres liées via Neo4j |
| `/offers` | `POST` | Crée une offre dans MongoDB et publie une notification Redis Pub/Sub |
| `/notifications/stream` | `GET` | Flux temps réel SSE branché sur Redis Pub/Sub |
| `/reco` | `GET` | Recommandations de destinations via Neo4j |
| `/stats/top-destinations` | `GET` | Top destinations calculé avec MongoDB et mis en cache Redis |
| `/login` | `POST` | Crée une session utilisateur stockée dans Redis |
| `/metrics` | `GET` | Métriques au format Prometheus |
| `/metrics/summary` | `GET` | Métriques au format JSON pour l'interface |
| `/health` | `GET` | Vérifie que l'API répond |
=======
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
>>>>>>> 1c4e8df0bfaeb91aeaf7954ecc4cbdf85019f404

## Amina - Offres

### Recherche d'offres

Endpoint :

```http
GET /offers?from=PAR&to=TYO&limit=5
```

Exemple :

```bash
curl "http://localhost:8000/offers?from=PAR&to=TYO&limit=5"
```

Fonctionnement :

1. L'API cherche d'abord dans Redis avec une clé du type `offers:PAR:TYO`.
2. Si la donnée existe, elle renvoie directement le cache : cache HIT.
3. Sinon, elle interroge MongoDB : cache MISS.
4. Le résultat MongoDB est stocké dans Redis avec un TTL de 60 secondes.

Ce mécanisme montre l'intérêt du cache Redis : les recherches répétées sont plus rapides et évitent de solliciter MongoDB inutilement.

### Offre par id

Endpoint :

```http
GET /offers/{offer_id}
```

Exemple :

```bash
curl "http://localhost:8000/offers/ID_DE_L_OFFRE"
```

Fonctionnement :

1. L'API vérifie d'abord Redis avec une clé du type `offers:{id}`.
2. Si l'offre n'est pas en cache, elle est récupérée depuis MongoDB.
3. L'API utilise ensuite Neo4j pour chercher des villes proches de la destination.
4. Elle retourne l'offre avec un champ `relatedOffers`.
5. Le détail est mis en cache Redis avec un TTL de 300 secondes.

Cette route démontre l'utilisation combinée de MongoDB, Redis et Neo4j.

## Amina - Notifications temps réel

Quand une nouvelle offre est créée avec `POST /offers`, l'API :

1. insère l'offre dans MongoDB ;
2. sérialise l'offre créée ;
3. publie un message JSON sur le canal Redis `offers:new` ;
4. invalide les caches liés aux offres et aux statistiques.

Le message publié contient notamment :

```json
{
  "event": "offer.created",
  "channel": "offers:new",
  "offerId": "id",
  "from": "PAR",
  "to": "AMS",
  "provider": "DemoAir",
  "price": 199,
  "currency": "EUR"
}
```

### Démonstration Redis Pub/Sub

Terminal 1 :

```bash
redis-cli SUBSCRIBE offers:new
```

Terminal 2 :

```bash
redis-cli PUBLISH offers:new "{\"event\":\"offer.created\",\"offerId\":\"demo\",\"from\":\"PAR\",\"to\":\"AMS\"}"
```

Le message arrive instantanément dans le terminal abonné.

### Démonstration via l'interface

L'interface web utilise :

```http
GET /notifications/stream
```

Cette route transforme les messages Redis Pub/Sub en Server-Sent Events. Le navigateur reçoit donc les nouvelles offres en temps réel, sans polling.

## Mariya - Recommandations

Endpoint :

```http
GET /reco?city=PAR&k=3
```

Exemple :

```bash
curl "http://localhost:8000/reco?city=PAR&k=3"
```

Fonctionnement :

1. L'utilisateur donne une ville de départ.
2. L'API interroge Neo4j.
3. Neo4j parcourt le graphe des villes proches.
4. L'API retourne les meilleures recommandations avec un score.

Cette partie montre l'intérêt d'une base graphe : elle est adaptée aux relations entre villes, distances, proximité et recommandations.

## Mariya - Top destinations

Endpoint :

```http
GET /stats/top-destinations
```

Exemple :

```bash
curl "http://localhost:8000/stats/top-destinations"
```

Réponse :

```json
{
  "source": "redis",
  "data": [
    {
      "destination": "AMS",
      "count": 12,
      "avgPrice": 199.0,
      "minPrice": 199.0
    }
  ]
}
```

Fonctionnement :

1. L'API vérifie Redis avec la clé `stats:top-destinations:{limit}`.
2. Si le cache existe, la réponse indique `"source": "redis"`.
3. Sinon, MongoDB calcule une agrégation :
   - groupement par destination ;
   - nombre d'offres ;
   - prix moyen ;
   - prix minimum.
4. Le résultat est stocké dans Redis pendant 300 secondes.
5. La réponse indique `"source": "mongodb"` lors du premier calcul.

Dans l'interface, un badge affiche :

- `cache HIT - Redis`
- `cache MISS - MongoDB`

## Anas - Login

Endpoint :

```http
POST /login
```

Exemple :

```bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d "{\"userId\":\"u42\"}"
```

Fonctionnement :

1. L'utilisateur envoie un `userId`.
2. L'API génère un token de session.
3. Le token est stocké dans Redis avec une clé du type `session:{token}`.
4. La session expire automatiquement grâce au TTL Redis.

Redis est adapté ici parce que les sessions sont temporaires et doivent être lues rapidement.

## Anas - Métriques

Deux routes sont disponibles.

### Métriques Prometheus

Endpoint :

```http
GET /metrics
```

Exemple :

```bash
curl "http://localhost:8000/metrics"
```

La réponse est au format Prometheus :

```text
sth_offers_requests_total 10
sth_cache_hits_total 7
sth_cache_misses_total 3
sth_cache_hit_rate 0.7000
sth_avg_response_ms 12.40
```

Ces métriques permettent de suivre :

- le nombre de requêtes ;
- les cache hits ;
- les cache misses ;
- le taux de réussite du cache ;
- le temps moyen de réponse.

### Résumé JSON pour le front

Endpoint :

```http
GET /metrics/summary
```

Exemple :

```bash
curl "http://localhost:8000/metrics/summary"
```

Cette route est utilisée par l'interface web pour afficher :

- le nombre total de requêtes suivies ;
- le nombre de HIT Redis ;
- le nombre de MISS ;
- le pourcentage de cache hit ;
- les temps moyens par endpoint ;
- des barres visuelles pour comprendre rapidement les performances.

## Interface web

L'interface `http://localhost:8000` permet de tester :

- la recherche d'offres ;
- le détail d'une offre ;
- les recommandations ;
- la connexion utilisateur ;
- les top destinations ;
- les métriques ;
- les notifications temps réel.

Pour forcer le navigateur à charger la dernière version du front :

```text
Ctrl + F5
```

## Tests utiles

Vérifier que l'API répond :

```bash
curl "http://localhost:8000/health"
```

Voir les top destinations :

```bash
curl "http://localhost:8000/stats/top-destinations"
```

Voir les métriques :

```bash
curl "http://localhost:8000/metrics"
```

Créer une offre et déclencher Pub/Sub :

```bash
curl -X POST "http://localhost:8000/offers" \
  -H "Content-Type: application/json" \
  -d "{
    \"from\": \"PAR\",
    \"to\": \"AMS\",
    \"departDate\": \"2026-06-01T00:00:00\",
    \"returnDate\": \"2026-06-05T00:00:00\",
    \"provider\": \"DemoAir\",
    \"price\": 199,
    \"currency\": \"EUR\",
    \"legs\": [
      {
        \"flightNum\": \"DA123\",
        \"dep\": \"PAR\",
        \"arr\": \"AMS\",
        \"duration\": \"1h30\"
      }
    ],
    \"hotel\": {
      \"name\": \"Amsterdam Hotel\",
      \"nights\": 4,
      \"price\": 300
    },
    \"activity\": null
  }"
```

## Résumé technique

Le projet montre comment combiner plusieurs bases NoSQL selon leur rôle :

- MongoDB stocke les documents d'offres.
- Redis accélère les lectures fréquentes avec le cache.
- Redis Pub/Sub pousse les nouvelles offres en temps réel.
- Redis stocke les sessions temporaires.
- Neo4j gère les relations entre destinations.
- FastAPI expose l'ensemble sous forme d'API HTTP.
