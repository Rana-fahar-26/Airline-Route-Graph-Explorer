"""
scripts/generate_sample_data.py
────────────────────────────────
Generates small sample .dat files for local testing WITHOUT
needing a live internet connection. These are a subset of the
real OpenFlights dataset with 20 airports and ~60 routes.

Run:  python scripts/generate_sample_data.py
"""

import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Airports (id,name,city,country,IATA,ICAO,lat,lon,alt,tz,dst,tzname,type,source)
AIRPORTS_DAT = """\
1,"Goroka Airport","Goroka","Papua New Guinea","GKA","AYGA",-6.081689834590001,145.391998291,5282,10,"U","Pacific/Port_Moresby","airport","OurAirports"
2,"Madang Airport","Madang","Papua New Guinea","MAG","AYMD",-5.20707988739,145.789001465,20,10,"U","Pacific/Port_Moresby","airport","OurAirports"
3,"Mount Hagen Kagamuga Airport","Mount Hagen","Papua New Guinea","HGU","AYMH",-5.826789855957031,144.29600524902344,5388,10,"U","Pacific/Port_Moresby","airport","OurAirports"
4,"Nadzab Airport","Nadzab","Papua New Guinea","LAE","AYNZ",-6.569803,146.725977,239,10,"U","Pacific/Port_Moresby","airport","OurAirports"
507,"John F Kennedy Intl","New York","United States","JFK","KJFK",40.63972222,-73.77888889,13,-5,"A","America/New_York","airport","OurAirports"
340,"Heathrow","London","United Kingdom","LHR","EGLL",51.4775,-0.461389,83,0,"E","Europe/London","airport","OurAirports"
1382,"Dubai International Airport","Dubai","United Arab Emirates","DXB","OMDB",25.2527999878,55.3643989563,62,4,"U","Asia/Dubai","airport","OurAirports"
3316,"Singapore Changi Airport","Singapore","Singapore","SIN","WSSS",1.35019,103.994003,22,8,"N","Asia/Singapore","airport","OurAirports"
1382,"Charles de Gaulle International Airport","Paris","France","CDG","LFPG",49.012798,2.55,392,1,"E","Europe/Paris","airport","OurAirports"
340,"Frankfurt am Main Airport","Frankfurt","Germany","FRA","EDDF",50.026401,8.543129,364,1,"E","Europe/Berlin","airport","OurAirports"
3077,"Amsterdam Airport Schiphol","Amsterdam","Netherlands","AMS","EHAM",52.308601,4.76389,11,1,"E","Europe/Amsterdam","airport","OurAirports"
3930,"Hong Kong International Airport","Hong Kong","Hong Kong","HKG","VHHH",22.308901,113.915001,28,8,"U","Asia/Hong_Kong","airport","OurAirports"
3484,"Los Angeles International Airport","Los Angeles","United States","LAX","KLAX",33.942501,-118.407997,125,-8,"A","America/Los_Angeles","airport","OurAirports"
3361,"Sydney Kingsford Smith International Airport","Sydney","Australia","SYD","YSSY",-33.94609832763672,151.177001953125,21,10,"O","Australia/Sydney","airport","OurAirports"
2359,"Narita International Airport","Tokyo","Japan","NRT","RJAA",35.7647018433,140.386001587,141,9,"U","Asia/Tokyo","airport","OurAirports"
3797,"O'Hare International Airport","Chicago","United States","ORD","KORD",41.9842987060547,-87.9067001342773,672,-6,"A","America/Chicago","airport","OurAirports"
3670,"Dallas Fort Worth International Airport","Dallas-Fort Worth","United States","DFW","KDFW",32.896801,-97.038002,607,-6,"A","America/Chicago","airport","OurAirports"
3682,"Hartsfield Jackson Atlanta International Airport","Atlanta","United States","ATL","KATL",33.6367,-84.428101,1026,-5,"A","America/New_York","airport","OurAirports"
1229,"Indira Gandhi International Airport","New Delhi","India","DEL","VIDP",28.5665,77.103104,777,5,"N","Asia/Calcutta","airport","OurAirports"
1128,"Cairo International Airport","Cairo","Egypt","CAI","HECA",30.12190056,31.40559959,382,2,"U","Africa/Cairo","airport","OurAirports"
"""

# ── Routes (airline,airline_id,src,src_id,dst,dst_id,codeshare,stops,equipment)
ROUTES_DAT = """\
BA,1355,LHR,340,JFK,507,,0,744 777
BA,1355,JFK,507,LHR,340,,0,744 777
EK,2183,DXB,1382,LHR,340,,0,380 777
EK,2183,LHR,340,DXB,1382,,0,380 777
EK,2183,DXB,1382,SIN,3316,,0,380
EK,2183,SIN,3316,DXB,1382,,0,380
SQ,4435,SIN,3316,LHR,340,,0,380 77W
SQ,4435,LHR,340,SIN,3316,,0,380 77W
SQ,4435,SIN,3316,JFK,507,,0,77W
AF,137,CDG,1382,JFK,507,,0,77W 332
AF,137,JFK,507,CDG,1382,,0,77W 332
AF,137,CDG,1382,LHR,340,,0,319 320
LH,3320,FRA,340,JFK,507,,0,744 748
LH,3320,JFK,507,FRA,340,,0,744 748
LH,3320,FRA,340,LHR,340,,0,319 321
LH,3320,FRA,340,DXB,1382,,0,744
LH,3320,DXB,1382,FRA,340,,0,744
KL,3090,AMS,3077,JFK,507,,0,772 773
KL,3090,JFK,507,AMS,3077,,0,772 773
KL,3090,AMS,3077,LHR,340,,0,E90 737
CX,1680,HKG,3930,LHR,340,,0,744 77W
CX,1680,LHR,340,HKG,3930,,0,744 77W
CX,1680,HKG,3930,SIN,3316,,0,333 359
CX,1680,SIN,3316,HKG,3930,,0,333 359
AA,24,LAX,3484,JFK,507,,0,738 321
AA,24,JFK,507,LAX,3484,,0,738 321
AA,24,LAX,3484,ORD,3797,,0,738 321
AA,24,ORD,3797,JFK,507,,0,738 321
AA,24,DFW,3670,JFK,507,,0,321 738
AA,24,ATL,3682,JFK,507,,0,738 321
QF,4089,SYD,3361,LAX,3484,,0,744 380
QF,4089,LAX,3484,SYD,3361,,0,744 380
QF,4089,SYD,3361,LHR,340,,1,744
NH,324,NRT,2359,LAX,3484,,0,77W 789
NH,324,LAX,3484,NRT,2359,,0,77W 789
NH,324,NRT,2359,HKG,3930,,0,763 789
NH,324,HKG,3930,NRT,2359,,0,763 789
AI,218,DEL,1229,LHR,340,,0,788 77W
AI,218,LHR,340,DEL,1229,,0,788 77W
AI,218,DEL,1229,JFK,507,,0,788
AI,218,JFK,507,DEL,1229,,0,788
MS,2143,CAI,1128,LHR,340,,0,738
MS,2143,LHR,340,CAI,1128,,0,738
EK,2183,DXB,1382,DEL,1229,,0,773 380
EK,2183,DEL,1229,DXB,1382,,0,773 380
"""

# ── Airlines (id,name,alias,IATA,ICAO,callsign,country,active)
AIRLINES_DAT = """\
1355,"British Airways","\\N","BA","BAW","SPEEDBIRD","United Kingdom","Y"
2183,"Emirates","\\N","EK","UAE","EMIRATES","United Arab Emirates","Y"
4435,"Singapore Airlines","\\N","SQ","SIA","SINGAPORE","Singapore","Y"
137,"Air France","\\N","AF","AFR","AIRFRANS","France","Y"
3320,"Lufthansa","\\N","LH","DLH","LUFTHANSA","Germany","Y"
3090,"KLM","\\N","KL","KLM","KLM","Netherlands","Y"
1680,"Cathay Pacific","\\N","CX","CPA","CATHAY","Hong Kong","Y"
24,"American Airlines","\\N","AA","AAL","AMERICAN","United States","Y"
4089,"Qantas","\\N","QF","QFA","QANTAS","Australia","Y"
324,"All Nippon Airways","ANA All Nippon Airways","NH","ANA","ALL NIPPON","Japan","Y"
218,"Air India","\\N","AI","AIC","AIRINDIA","India","Y"
2143,"EgyptAir","\\N","MS","MSR","EGYPTAIR","Egypt","Y"
"""

def write(filename, content):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    count = content.strip().count("\n") + 1
    print(f"  ✓ {filename} — {count} records")

if __name__ == "__main__":
    print("Generating sample data files in /data …")
    write("airports.dat", AIRPORTS_DAT)
    write("routes.dat",   ROUTES_DAT)
    write("airlines.dat", AIRLINES_DAT)
    print("Done! Run setup_db.py to load into databases.")
