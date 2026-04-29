// Nœuds City
CREATE (par:City {code: "PAR", name: "Paris",     country: "FR"})
CREATE (tyo:City {code: "TYO", name: "Tokyo",     country: "JP"})
CREATE (lon:City {code: "LON", name: "London",    country: "GB"})
CREATE (ams:City {code: "AMS", name: "Amsterdam", country: "NL"})
CREATE (bcn:City {code: "BCN", name: "Barcelona", country: "ES"})
CREATE (nyc:City {code: "NYC", name: "New York",  country: "US"})
CREATE (ber:City {code: "BER", name: "Berlin",    country: "DE"})

// Relations depuis PAR
CREATE (par)-[:NEAR {weight: 0.9}]->(lon)
CREATE (par)-[:NEAR {weight: 0.85}]->(ams)
CREATE (par)-[:NEAR {weight: 0.8}]->(bcn)
CREATE (par)-[:NEAR {weight: 0.7}]->(ber)

// Relations depuis TYO
CREATE (tyo)-[:NEAR {weight: 0.9}]->(lon)
CREATE (tyo)-[:NEAR {weight: 0.75}]->(nyc)

// Relations depuis LON
CREATE (lon)-[:NEAR {weight: 0.9}]->(par)
CREATE (lon)-[:NEAR {weight: 0.85}]->(ams)
CREATE (lon)-[:NEAR {weight: 0.7}]->(nyc)