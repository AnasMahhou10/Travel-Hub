db = db.getSiblingDB("sth");

db.offers.drop();

db.offers.insertMany([
  {
    from: "PAR", to: "TYO",
    departDate: new Date("2024-07-10"), returnDate: new Date("2024-07-20"),
    provider: "AirZen", price: 750.00, currency: "EUR",
    legs: [{ flightNum: "AZ101", dep: "CDG", arr: "NRT", duration: "11h30" }],
    hotel: { name: "Shinjuku Palace", nights: 10, price: 900 },
    activity: { title: "Visite du Mont Fuji", price: 80 }
  },
  {
    from: "PAR", to: "TYO",
    departDate: new Date("2024-07-15"), returnDate: new Date("2024-07-25"),
    provider: "SkyWings", price: 680.00, currency: "EUR",
    legs: [{ flightNum: "SW202", dep: "ORY", arr: "HND", duration: "12h00" }],
    hotel: { name: "Akihabara Inn", nights: 10, price: 750 },
    activity: null
  },
  {
    from: "PAR", to: "LON",
    departDate: new Date("2024-08-01"), returnDate: new Date("2024-08-05"),
    provider: "EuroJet", price: 120.00, currency: "EUR",
    legs: [{ flightNum: "EJ310", dep: "CDG", arr: "LHR", duration: "1h20" }],
    hotel: { name: "London Bridge Hotel", nights: 4, price: 400 },
    activity: null
  },
  {
    from: "LON", to: "NYC",
    departDate: new Date("2024-09-10"), returnDate: new Date("2024-09-20"),
    provider: "AirZen", price: 450.00, currency: "GBP",
    legs: [{ flightNum: "AZ505", dep: "LHR", arr: "JFK", duration: "7h30" }],
    hotel: { name: "Manhattan Suites", nights: 10, price: 1200 },
    activity: { title: "Broadway Show", price: 150 }
  },
  {
    from: "PAR", to: "BCN",
    departDate: new Date("2024-10-05"), returnDate: new Date("2024-10-10"),
    provider: "SkyWings", price: 95.00, currency: "EUR",
    legs: [{ flightNum: "SW410", dep: "ORY", arr: "BCN", duration: "2h00" }],
    hotel: null,
    activity: { title: "Sagrada Familia Tour", price: 30 }
  }
]);

db.offers.createIndex({ from: 1, to: 1, price: 1 });
db.offers.createIndex(
  { provider: "text", "hotel.name": "text", "activity.title": "text" },
  { name: "offer_text_search", default_language: "none" }
);

print("MongoDB seed OK — " + db.offers.countDocuments() + " offers inserted");