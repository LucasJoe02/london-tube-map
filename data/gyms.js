// Indoor bouldering gyms in and around London (hand-maintained).
// Locations from OpenStreetMap (Overpass, sport=climbing), cross-checked against operator
// sites (climbingdistrict.uk, londonclimbingcentres.co.uk, citybouldering.co.uk, the-font.co.uk)
// and boulderinglist.com in Sept 2026. Excludes kids' fun walls (Clip 'n Climb), outdoor
// boulders, high-ropes parks and small school/leisure-centre walls.
// ropes: true = roped/auto-belay climbing confirmed as well as bouldering.
window.GYMS = {
  checked: "2026-09-24",
  gyms: [
    { name: "City Bouldering Aldgate", lat: 51.5144, lon: -0.0750, url: "https://www.citybouldering.co.uk/" },
    { name: "City Bouldering Stratford", lat: 51.5372, lon: -0.0039, url: "https://www.citybouldering.co.uk/locations/stratford" },
    { name: "City Bouldering White City", lat: 51.5095, lon: -0.2230, url: "https://www.citybouldering.co.uk/" },
    { name: "Climbing Co Fulham", lat: 51.4763, lon: -0.1996, url: "https://www.citybouldering.co.uk/locations/climbing-co-fulham", note: "Parsons Green Depot (former Climbing Hangar)" },
    { name: "Climbing District Building One", lat: 51.4933, lon: -0.0611, url: "https://climbingdistrict.uk/", note: "Bermondsey; formerly The Arch Building One" },
    { name: "Climbing District London Fields", lat: 51.5347, lon: -0.0603, url: "https://climbingdistrict.uk/climbing-gym/london-fields/" },
    { name: "Climbing District Tottenham Hale", lat: 51.5854, lon: -0.0608, url: "https://climbingdistrict.uk/", ropes: true, note: "Formerly Stronghold" },
    { name: "Climbing District Surrey Quays", lat: 51.4956, lon: -0.0470, url: "https://climbingdistrict.uk/salle-escalade/surrey-quays/", note: "Surrey Quays Shopping Centre; formerly The Arch Surrey Quays" },
    { name: "The Arch North", lat: 51.5988, lon: -0.2657, url: "https://www.archclimbingwall.com/", note: "Burnt Oak" },
    { name: "The Arch Acton", lat: 51.5069, lon: -0.2652, url: "https://www.archclimbingwall.com/" },
    { name: "The Font Borough", lat: 51.5072, lon: -0.0972, url: "https://www.the-font.co.uk/borough" },
    { name: "The Font Wandsworth", lat: 51.4473, lon: -0.1912, url: "https://www.the-font.co.uk/wandsworth" },
    { name: "The Font Hounslow", lat: 51.4705, lon: -0.3619, url: "https://www.the-font.co.uk/" },
    { name: "BethWall", lat: 51.5277, lon: -0.0564, url: "https://londonclimbingcentres.co.uk/centre/bethwall/" },
    { name: "CanaryWall", lat: 51.5097, lon: -0.0274, url: "https://londonclimbingcentres.co.uk/centre/canarywall/" },
    { name: "EustonWall", lat: 51.5246, lon: -0.1419, url: "https://londonclimbingcentres.co.uk/centre/eustonwall/" },
    { name: "VauxWall East", lat: 51.4923, lon: -0.1146, url: "https://londonclimbingcentres.co.uk/centre/vauxeast/" },
    { name: "VauxWall West", lat: 51.4851, lon: -0.1229, url: "https://londonclimbingcentres.co.uk/centre/vauxwest/", ropes: true },
    { name: "HarroWall", lat: 51.5807, lon: -0.3444, url: "https://londonclimbingcentres.co.uk/centre/harrowall/", ropes: true },
    { name: "CroyWall", lat: 51.3742, lon: -0.1155, url: "https://londonclimbingcentres.co.uk/centre/croywall/", ropes: true },
    { name: "RavensWall", lat: 51.4943, lon: -0.2361, url: "https://www.ravenswall.co.uk/" },
    { name: "Yonder", lat: 51.5896, lon: -0.0409, url: "https://www.thisisyonder.com/yonder-climbing-new" },
    { name: "Substation Brixton", lat: 51.4587, lon: -0.1284, url: "https://substation.co.uk/brixton/" },
    { name: "Blocfit", lat: 51.4650, lon: -0.1029, url: "https://www.blocfit.co.uk/", note: "Brixton" },
    { name: "Parthian Climbing Wandsworth", lat: 51.4549, lon: -0.1931, url: "https://parthianclimbing.com/wandsworth/" },
    { name: "Rise Climbing", lat: 51.5112, lon: 0.0127, url: "https://www.rise-climbing.com/", note: "Royal Docks" },
    { name: "The Castle Climbing Centre", lat: 51.5653, lon: -0.0924, url: "https://www.castle-climbing.co.uk/", ropes: true },
    { name: "Mile End Climbing Wall", lat: 51.5277, lon: -0.0397, url: "https://www.mileendwall.org.uk/", ropes: true },
    { name: "Westway Climbing Centre", lat: 51.5155, lon: -0.2207, url: "https://www.everyoneactive.com/centre/westway-sports-fitness-centre", ropes: true },
    { name: "The Reach", lat: 51.4944, lon: 0.0426, url: "https://www.thereach.org.uk/", ropes: true, note: "Woolwich" },
    { name: "Romford Rock and Boulder", lat: 51.5830, lon: 0.1746, url: "https://www.romfordrockandboulder.co.uk/", ropes: true },
    { name: "White Spider", lat: 51.3724, lon: -0.2915, url: "https://spiderclimbing.com/white-spider/", note: "Chessington" },
  ],
};
