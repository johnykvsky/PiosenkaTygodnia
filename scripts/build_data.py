#!/usr/bin/env python3
"""
Fetch and build dataset + local optimized covers for Piosenka Tygodnia
(Spotify playlist: 0FrlCdqFAI5kqSDjKh1oJ5).

Completely self-contained inside PiosenkaTygodnia/.
"""
import hashlib
import json
import os
import re
import subprocess
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS_DIR = os.path.join(BASE_DIR, "assets", "covers")
DATA_JS_PATH = os.path.join(BASE_DIR, "js", "data.js")
RAW_CACHE_PATH = os.path.join(BASE_DIR, "scripts", "spotify_playlist_raw.json")

os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "js"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "scripts"), exist_ok=True)

PLAYLIST_ID = "0FrlCdqFAI5kqSDjKh1oJ5"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
TARGET_MIN_SIDE = 200
JPEG_QUALITY = 85

# Curated genre classification for all 500 primary artists on the playlist
ARTIST_GENRE_MAP = {
    # Rock progresywny (Progressive Rock, Art Rock, Post-Rock, Krautrock, Neo-Prog)
    "A Perfect Circle": "Rock progresywny",
    "Airbag": "Rock progresywny",
    "Alan Parsons": "Rock progresywny",
    "Anathema": "Rock progresywny",
    "Angine de Poitrine": "Rock progresywny",
    "Anna von Hausswolff": "Rock progresywny",
    "Aphrodite's Child": "Rock progresywny",
    "Archive": "Rock progresywny",
    "Bioscope": "Rock progresywny",
    "Bjørn Riis": "Rock progresywny",
    "Camel": "Rock progresywny",
    "Caravan": "Rock progresywny",
    "Collage": "Rock progresywny",
    "Daturah": "Rock progresywny",
    "David Gilmour": "Rock progresywny",
    "Dream Theater": "Rock progresywny",
    "Electric Light Orchestra": "Rock progresywny",
    "Eloy": "Rock progresywny",
    "Eric Woolfson": "Rock progresywny",
    "Fish": "Rock progresywny",
    "Focus": "Rock progresywny",
    "Genesis": "Rock progresywny",
    "IQ": "Rock progresywny",
    "If These Trees Could Talk": "Rock progresywny",
    "King Gizzard & The Lizard Wizard": "Rock progresywny",
    "Long Distance Calling": "Rock progresywny",
    "Marillion": "Rock progresywny",
    "Meniscus": "Rock progresywny",
    "Mike Oldfield": "Rock progresywny",
    "Naxatras": "Rock progresywny",
    "Peter Gabriel": "Rock progresywny",
    "Pink Floyd": "Rock progresywny",
    "Porcupine Tree": "Rock progresywny",
    "Queensrÿche": "Rock progresywny",
    "Riverside": "Rock progresywny",
    "Robert Erdesz": "Rock progresywny",
    "Roger Waters": "Rock progresywny",
    "Russian Circles": "Rock progresywny",
    "Skaldowie": "Rock progresywny",
    "Steve Hackett": "Rock progresywny",
    "Steve Rothery": "Rock progresywny",
    "Steven Wilson": "Rock progresywny",
    "Supertramp": "Rock progresywny",
    "TOOL": "Rock progresywny",
    "The Alan Parsons Project": "Rock progresywny",
    "The Evpatoria Report": "Rock progresywny",
    "The Moody Blues": "Rock progresywny",
    "The Pineapple Thief": "Rock progresywny",
    "Yes": "Rock progresywny",
    "Yogi Lang": "Rock progresywny",
    "tRKproject": "Rock progresywny",

    # Metal (Heavy Metal, Thrash, Prog Metal, Stoner/Doom, Gothic/Industrial Metal)
    "Accept": "Metal",
    "Alcest": "Metal",
    "Apocalyptica": "Metal",
    "Astral Doors": "Metal",
    "Behemoth": "Metal",
    "Black Mountain": "Metal",
    "Body Count": "Metal",
    "Breaking Benjamin": "Metal",
    "Chino Moreno": "Metal",
    "Clutch": "Metal",
    "Crematory": "Metal",
    "Dimmu Bongir": "Metal",
    "Dio": "Metal",
    "Elder": "Metal",
    "Evanescence": "Metal",
    "Godsmack": "Metal",
    "Gojira": "Metal",
    "Guano Apes": "Metal",
    "Hunter": "Metal",
    "ISIS": "Metal",
    "Iron Maiden": "Metal",
    "Jinjer": "Metal",
    "Judas Priest": "Metal",
    "Kadavar": "Metal",
    "Kreator": "Metal",
    "Kyuss": "Metal",
    "Lacrimosa": "Metal",
    "Lemmy": "Metal",
    "Lipali": "Metal",
    "Luxtorpeda": "Metal",
    "Marilyn Manson": "Metal",
    "Megadeth": "Metal",
    "Metallica": "Metal",
    "OM": "Metal",
    "Ozzy Osbourne": "Metal",
    "Paradise Lost": "Metal",
    "Pigs Pigs Pigs Pigs Pigs Pigs Pigs": "Metal",
    "Proletaryat": "Metal",
    "Psycho Alumni": "Metal",
    "REZN": "Metal",
    "Rabea Massaad": "Metal",
    "Rage Against The Machine": "Metal",
    "Sepultura": "Metal",
    "Stratovarius": "Metal",
    "The Birthday Massacre": "Metal",
    "The Ocean": "Metal",

    # Hard Rock
    "AC/DC": "Hard Rock",
    "Aerosmith": "Hard Rock",
    "Airbourne": "Hard Rock",
    "All Them Witches": "Hard Rock",
    "Audioslave": "Hard Rock",
    "Billy Squier": "Hard Rock",
    "Bob Daisley and Friends": "Hard Rock",
    "Bonfire": "Hard Rock",
    "Coverdale/Page": "Hard Rock",
    "Deep Purple": "Hard Rock",
    "Foreigner": "Hard Rock",
    "Golden Earring": "Hard Rock",
    "Heart": "Hard Rock",
    "Heroes Del Silencio": "Hard Rock",
    "Joe Walsh": "Hard Rock",
    "Journey": "Hard Rock",
    "Kingdom Come": "Hard Rock",
    "Mech": "Hard Rock",
    "STEELHEART": "Hard Rock",
    "Slade": "Hard Rock",
    "Soundgarden": "Hard Rock",
    "Temple Of The Dog": "Hard Rock",
    "Tenacious D": "Hard Rock",
    "The Darkness": "Hard Rock",
    "UFO": "Hard Rock",
    "Ugly Kid Joe": "Hard Rock",

    # Alternatywa / Indie (Alternative Rock, Grunge, Post-Punk, Gothic Rock, New Wave, Shoegaze, Indie)
    "Alanis Morissette": "Alternatywa / Indie",
    "Alice In Chains": "Alternatywa / Indie",
    "Anja Garbarek": "Alternatywa / Indie",
    "Arctic Monkeys": "Alternatywa / Indie",
    "Asaf Avidan": "Alternatywa / Indie",
    "Aya RL": "Alternatywa / Indie",
    "BOKKA": "Alternatywa / Indie",
    "Badly Drawn Boy": "Alternatywa / Indie",
    "Bajzel": "Alternatywa / Indie",
    "Band of Horses": "Alternatywa / Indie",
    "Basht.": "Alternatywa / Indie",
    "Battles": "Alternatywa / Indie",
    "Beth Gibbons": "Alternatywa / Indie",
    "Bielizna": "Alternatywa / Indie",
    "Biffy Clyro": "Alternatywa / Indie",
    "Bluszcz": "Alternatywa / Indie",
    "Brainstorm": "Alternatywa / Indie",
    "Buldog": "Alternatywa / Indie",
    "Carrion": "Alternatywa / Indie",
    "Cat Power": "Alternatywa / Indie",
    "Clan of Xymox": "Alternatywa / Indie",
    "Classix Nouveaux": "Alternatywa / Indie",
    "Clock Machine": "Alternatywa / Indie",
    "Cocteau Twins": "Alternatywa / Indie",
    "Coma": "Alternatywa / Indie",
    "Crimen": "Alternatywa / Indie",
    "DOPE LEMON": "Alternatywa / Indie",
    "Daniel Spaleniak": "Alternatywa / Indie",
    "Daria ze Śląska": "Alternatywa / Indie",
    "Dead Can Dance": "Alternatywa / Indie",
    "Diving Stove": "Alternatywa / Indie",
    "Early Day Miners": "Alternatywa / Indie",
    "Eddie Vedder": "Alternatywa / Indie",
    "Editors": "Alternatywa / Indie",
    "Einstürzende Neubauten": "Alternatywa / Indie",
    "Faith No More": "Alternatywa / Indie",
    "Family Band": "Alternatywa / Indie",
    "Filter": "Alternatywa / Indie",
    "Fink": "Alternatywa / Indie",
    "Firewater": "Alternatywa / Indie",
    "Fontaines D.C.": "Alternatywa / Indie",
    "Fort Frances": "Alternatywa / Indie",
    "Fury In The Slaughterhouse": "Alternatywa / Indie",
    "Gorillaz": "Alternatywa / Indie",
    "Gołoledź": "Alternatywa / Indie",
    "Green Day": "Alternatywa / Indie",
    "Grzegorz Ciechowski": "Alternatywa / Indie",
    "Heather Nova": "Alternatywa / Indie",
    "Holy Høly": "Alternatywa / Indie",
    "Ian Brown": "Alternatywa / Indie",
    "Iggy Pop": "Alternatywa / Indie",
    "Ilegales": "Alternatywa / Indie",
    "James": "Alternatywa / Indie",
    "Joachim Witt": "Alternatywa / Indie",
    "Jonathan Bree": "Alternatywa / Indie",
    "Julee Cruise": "Alternatywa / Indie",
    "KSU": "Alternatywa / Indie",
    "Khruangbin": "Alternatywa / Indie",
    "Kings of Leon": "Alternatywa / Indie",
    "Kino": "Alternatywa / Indie",
    "Klaus Mitffoch": "Alternatywa / Indie",
    "Lao Che": "Alternatywa / Indie",
    "Let Babylon Burn": "Alternatywa / Indie",
    "Linda Perry": "Alternatywa / Indie",
    "London Grammar": "Alternatywa / Indie",
    "Lord Newborn and the Magic Skulls": "Alternatywa / Indie",
    "Lou Reed": "Alternatywa / Indie",
    "Mad Season": "Alternatywa / Indie",
    "Maria Peszek": "Alternatywa / Indie",
    "Mark Lanegan": "Alternatywa / Indie",
    "Mark Stewart": "Alternatywa / Indie",
    "Matylda/Łukasiewicz": "Alternatywa / Indie",
    "Mayflower Madame": "Alternatywa / Indie",
    "Michelle Gurevich": "Alternatywa / Indie",
    "My Chemical Romance": "Alternatywa / Indie",
    "Myslovitz": "Alternatywa / Indie",
    "New Order": "Alternatywa / Indie",
    "Nightbus": "Alternatywa / Indie",
    "Nine Inch Nails": "Alternatywa / Indie",
    "Nirvana": "Alternatywa / Indie",
    "Noel Gallagher's High Flying Birds": "Alternatywa / Indie",
    "Obywatel G.C.": "Alternatywa / Indie",
    "Ozark Henry": "Alternatywa / Indie",
    "PJ Harvey": "Alternatywa / Indie",
    "Perry Farrell": "Alternatywa / Indie",
    "Pidżama Porno": "Alternatywa / Indie",
    "Pixies": "Alternatywa / Indie",
    "Placebo": "Alternatywa / Indie",
    "Pulp": "Alternatywa / Indie",
    "R.E.M.": "Alternatywa / Indie",
    "Reel Big Fish": "Alternatywa / Indie",
    "Renata Przemyk": "Alternatywa / Indie",
    "Republika": "Alternatywa / Indie",
    "Siekiera": "Alternatywa / Indie",
    "Simple Minds": "Alternatywa / Indie",
    "Sinéad O'Connor": "Alternatywa / Indie",
    "Siouxsie and the Banshees": "Alternatywa / Indie",
    "Sisters of Mercy": "Alternatywa / Indie",
    "Soap&Skin": "Alternatywa / Indie",
    "Spięty": "Alternatywa / Indie",
    "Spoon": "Alternatywa / Indie",
    "Stereophonics": "Alternatywa / Indie",
    "Still Corners": "Alternatywa / Indie",
    "Stina Nordenstam": "Alternatywa / Indie",
    "Strachy Na Lachy": "Alternatywa / Indie",
    "Tame Impala": "Alternatywa / Indie",
    "The Cardigans": "Alternatywa / Indie",
    "The Charlatans": "Alternatywa / Indie",
    "The Cranberries": "Alternatywa / Indie",
    "The Cure": "Alternatywa / Indie",
    "The Dolly Rocker Movement": "Alternatywa / Indie",
    "The Fratellis": "Alternatywa / Indie",
    "The Music": "Alternatywa / Indie",
    "The Protomen": "Alternatywa / Indie",
    "The Saxophones": "Alternatywa / Indie",
    "The Smiths": "Alternatywa / Indie",
    "The Stranglers": "Alternatywa / Indie",
    "The The": "Alternatywa / Indie",
    "The Walkmen": "Alternatywa / Indie",
    "TheStylacja": "Alternatywa / Indie",
    "This Mortal Coil": "Alternatywa / Indie",
    "Thurston Moore": "Alternatywa / Indie",
    "Tilt": "Alternatywa / Indie",
    "Tori Amos": "Alternatywa / Indie",
    "Two Feet": "Alternatywa / Indie",
    "Tymon & The Transistors": "Alternatywa / Indie",
    "Warhaus": "Alternatywa / Indie",
    "Wildest Dreams": "Alternatywa / Indie",
    "YUNGBLUD": "Alternatywa / Indie",
    "Youth Novels": "Alternatywa / Indie",
    "Zoë Fox and the Rocket Clocks": "Alternatywa / Indie",

    # Rock (Classic Rock, Pop Rock, Roots Rock)
    "Big Cyc": "Rock",
    "Bijelo Dugme": "Rock",
    "Billy Idol": "Rock",
    "Billy Joel": "Rock",
    "Bruce Springsteen": "Rock",
    "Bryan Ferry": "Rock",
    "Budka Suflera": "Rock",
    "Chris Rea": "Rock",
    "David Bowie": "Rock",
    "Dire Straits": "Rock",
    "Don Henley": "Rock",
    "Eagles": "Rock",
    "Fleetwood Mac": "Rock",
    "Garland Jeffreys": "Rock",
    "Herman's Hermits": "Rock",
    "Kasia Kowalska": "Rock",
    "Klincz": "Rock",
    "Lady Pank": "Rock",
    "Linda Ronstadt": "Rock",
    "Loggins & Messina": "Rock",
    "Maanam": "Rock",
    "Mark Knopfler": "Rock",
    "Mike + The Mechanics": "Rock",
    "Neil Young": "Rock",
    "Nils Lofgren": "Rock",
    "Phil Collins": "Rock",
    "Ray Wilson": "Rock",
    "Red Box": "Rock",
    "Rod Stewart": "Rock",
    "Santana": "Rock",
    "Sheryl Crow": "Rock",
    "Steve Jones": "Rock",
    "Sting": "Rock",
    "T.Love": "Rock",
    "TOTO": "Rock",
    "The Animals": "Rock",
    "The Beatles": "Rock",
    "The Cars": "Rock",
    "The J. Geils Band": "Rock",
    "The Notting Hillbillies": "Rock",
    "The Rebels": "Rock",
    "The Rolling Stones": "Rock",
    "The Shadows": "Rock",
    "Tito & Tarantula": "Rock",
    "Tom Petty": "Rock",
    "Tom Petty and the Heartbreakers": "Rock",
    "Wanda i Banda": "Rock",

    # Muzyka elektroniczna (Synthpop, Trip-Hop, Ambient, Electronica, IDM, Synthwave)
    "Agar Agar": "Muzyka elektroniczna",
    "Ambala": "Muzyka elektroniczna",
    "Apollo 440": "Muzyka elektroniczna",
    "Bartosz Szpak": "Muzyka elektroniczna",
    "Black Strobe": "Muzyka elektroniczna",
    "Bronski Beat": "Muzyka elektroniczna",
    "Daft Punk": "Muzyka elektroniczna",
    "Daniel Bloom": "Muzyka elektroniczna",
    "Death In Vegas": "Muzyka elektroniczna",
    "Depeche Mode": "Muzyka elektroniczna",
    "Dreamstate Logic": "Muzyka elektroniczna",
    "Erasure": "Muzyka elektroniczna",
    "Floating Points": "Muzyka elektroniczna",
    "Gunship": "Muzyka elektroniczna",
    "Happyendless": "Muzyka elektroniczna",
    "Hooverphonic": "Muzyka elektroniczna",
    "Howard Jones": "Muzyka elektroniczna",
    "Jam & Spoon": "Muzyka elektroniczna",
    "Jan Hammer": "Muzyka elektroniczna",
    "Jean-Michel Jarre": "Muzyka elektroniczna",
    "Jem": "Muzyka elektroniczna",
    "John Carpenter": "Muzyka elektroniczna",
    "Jon & Vangelis": "Muzyka elektroniczna",
    "KATZROAR": "Muzyka elektroniczna",
    "Klaus Schulze": "Muzyka elektroniczna",
    "Madis": "Muzyka elektroniczna",
    "Massive Attack": "Muzyka elektroniczna",
    "Nicolas Jaar": "Muzyka elektroniczna",
    "Nightmares On Wax": "Muzyka elektroniczna",
    "Northern Lite": "Muzyka elektroniczna",
    "Ofenbach": "Muzyka elektroniczna",
    "Orchestral Manoeuvres In The Dark": "Muzyka elektroniczna",
    "Portishead": "Muzyka elektroniczna",
    "Propaganda": "Muzyka elektroniczna",
    "Röyksopp": "Muzyka elektroniczna",
    "Sainte Vie": "Muzyka elektroniczna",
    "Schiller": "Muzyka elektroniczna",
    "Sunglasses Kid": "Muzyka elektroniczna",
    "Susanne Sundfør": "Muzyka elektroniczna",
    "Tangerine Dream": "Muzyka elektroniczna",
    "Tears For Fears": "Muzyka elektroniczna",
    "The KLF": "Muzyka elektroniczna",
    "Tricky": "Muzyka elektroniczna",
    "Ultravox": "Muzyka elektroniczna",
    "Vangelis": "Muzyka elektroniczna",
    "Yazoo": "Muzyka elektroniczna",
    "Yosi Horikawa": "Muzyka elektroniczna",
    "Zaho de Sagazan": "Muzyka elektroniczna",

    # Pop
    "AURORA": "Pop",
    "Alison Moyet": "Pop",
    "Alon Aboutboul": "Pop",
    "Andrzej Rybiński": "Pop",
    "Ania Karwan": "Pop",
    "Bajm": "Pop",
    "Barbara Sikorska": "Pop",
    "Basia": "Pop",
    "Billie Eilish": "Pop",
    "Bolland": "Pop",
    "Ciao Italy Band": "Pop",
    "Darko Domijan": "Pop",
    "Dawid Podsiadło": "Pop",
    "Donna Summer": "Pop",
    "Dwa plus Jeden": "Pop",
    "Ella Eyre": "Pop",
    "Francesco Napoli": "Pop",
    "Frankie Goes To Hollywood": "Pop",
    "Geoff Castellucci": "Pop",
    "George Michael": "Pop",
    "Ginamaría Hidalgo": "Pop",
    "Grace Jones": "Pop",
    "Julia Kamińska": "Pop",
    "Kylie Minogue": "Pop",
    "Lady Linn": "Pop",
    "Lily Allen": "Pop",
    "MIKA": "Pop",
    "Madonna": "Pop",
    "Michael Bublé": "Pop",
    "Michael Jackson": "Pop",
    "Miley Cyrus": "Pop",
    "OSYDA": "Pop",
    "Pentatonix": "Pop",
    "Peter Cetera": "Pop",
    "Self Esteem": "Pop",
    "September": "Pop",
    "Sia": "Pop",
    "Stromae": "Pop",
    "Sława Przybylska": "Pop",
    "Tercet Egzotyczny": "Pop",
    "U.S.A. For Africa": "Pop",
    "VOX": "Pop",

    # Jazz
    "Aga Zaryan": "Jazz",
    "Anders Baldwin": "Jazz",
    "Andrzej Dabrowski": "Jazz",
    "Chuck Mangione": "Jazz",
    "Dida Pelled": "Jazz",
    "Dominique Fils-Aimé": "Jazz",
    "Dzamble": "Jazz",
    "Ezra Collective": "Jazz",
    "GoGo Penguin": "Jazz",
    "Gregory Porter": "Jazz",
    "Główny Zawór Jazzu": "Jazz",
    "Herb Alpert & The Tijuana Brass": "Jazz",
    "Karo Glazer": "Jazz",
    "Krystyna Prońko": "Jazz",
    "Lars Danielsson": "Jazz",
    "Manu Katché": "Jazz",
    "Marek Żebrowski": "Jazz",
    "Matthew Halsall": "Jazz",
    "Melanie De Biasio": "Jazz",
    "Nahorny i jego orkiestra": "Jazz",
    "Nils Petter Molvær": "Jazz",
    "Pat Metheny": "Jazz",
    "Ralph Towner": "Jazz",
    "Rebecca Pidgeon": "Jazz",
    "Sara K.": "Jazz",
    "Shirley Horn": "Jazz",
    "Sonny Rollins": "Jazz",
    "The Dave Brubeck Quartet": "Jazz",
    "Touch & Go": "Jazz",
    "Us3": "Jazz",

    # Blues
    "Alvin Lee": "Blues",
    "Beth Hart": "Blues",
    "Chris Jones": "Blues",
    "Dżem": "Blues",
    "Eric Clapton": "Blues",
    "Gary Moore": "Blues",
    "Jeff Beck": "Blues",
    "Joe Bonamassa": "Blues",
    "John Campbell": "Blues",
    "Philip Sayce": "Blues",
    "Snowy White": "Blues",
    "Sosnowski": "Blues",
    "Stefan Benecke": "Blues",
    "Stevie Ray Vaughan": "Blues",
    "Tadeusz Nalepa": "Blues",
    "Tony Joe White": "Blues",
    "Will Barber": "Blues",

    # Folk / World
    "Ane Brun": "Folk",
    "Bob Dylan": "Folk",
    "Clannad": "Folk",
    "Daniel Norgren": "Folk",
    "Dead Combo": "Folk",
    "Eivør": "Folk",
    "Elanor Moss": "Folk",
    "Graham Nash": "Folk",
    "Heilung": "Folk",
    "John Martyn": "Folk",
    "Lor": "Folk",
    "Maire Brennan": "Folk",
    "Mari Boine": "Folk",
    "Mariza": "Folk",
    "Rokiczanka": "Folk",
    "Sally Oldfield": "Folk",
    "Shelby Lynne": "Folk",
    "The Devil Makes Three": "Folk",
    "Wardruna": "Folk",

    # Soul / R&B / Funk
    "Andrzej Zaucha": "Soul / R&B",
    "Cinnamon Gum": "Soul / R&B",
    "Funkadelic": "Soul / R&B",
    "Kelela": "Soul / R&B",
    "Kelis": "Soul / R&B",
    "Labi Siffre": "Soul / R&B",
    "Macy Gray": "Soul / R&B",
    "Mrozu": "Soul / R&B",
    "Natalia Przybysz": "Soul / R&B",
    "October London": "Soul / R&B",
    "Prince": "Soul / R&B",
    "RAYE": "Soul / R&B",
    "Sade": "Soul / R&B",
    "Seal": "Soul / R&B",
    "Stevie Wonder": "Soul / R&B",

    # Poezja śpiewana / Piosenka autorska
    "Antoni Muracki": "Poezja śpiewana",
    "Edyta Geppert": "Poezja śpiewana",
    "Leonard Cohen": "Poezja śpiewana",
    "Maciej Zembaty": "Poezja śpiewana",
    "Maja Kleszcz": "Poezja śpiewana",
    "Marek Grechuta": "Poezja śpiewana",
    "Silna Grupa Pod Wezwaniem": "Poezja śpiewana",
    "Wojciech Młynarski": "Poezja śpiewana",
    "Wojtek Szumański": "Poezja śpiewana",
    "Владимир Высоцкий": "Poezja śpiewana",

    # Muzyka klasyczna / Neoklasyka
    "Hania Rani": "Muzyka klasyczna",
    "Johann Sebastian Bach": "Muzyka klasyczna",
    "Kurt Weill": "Muzyka klasyczna",
    "Ludovico Einaudi": "Muzyka klasyczna",
    "Ludwig van Beethoven": "Muzyka klasyczna",
    "Léo Delibes": "Muzyka klasyczna",
    "Max Richter": "Muzyka klasyczna",
    "Simon Chamberlain": "Muzyka klasyczna",

    # Hip-hop / Rap
    "DOBRY": "Hip-hop / Rap",
    "Dildo Baggins": "Hip-hop / Rap",
    "Fisz Emade Tworzywo": "Hip-hop / Rap",
    "Gawryle": "Hip-hop / Rap",
    "Grand Duke P.": "Hip-hop / Rap",
    "Stakka Bo": "Hip-hop / Rap",
    "TACONAFIDE": "Hip-hop / Rap",

    # OST / Musical
    "Annie Lennox": "OST / Musical",
    "Carl Anderson": "OST / Musical",
    "Rodrigo Amarante": "OST / Musical",
}


def slugify(artist: str, album: str) -> str:
    raw = f"{artist}-{album}".lower()
    pl_map = str.maketrans("ąćęłńóśźż", "acelnoszz")
    raw = raw.translate(pl_map)
    raw = unicodedata.normalize("NFD", raw)
    raw = "".join(ch for ch in raw if unicodedata.category(ch) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    h = hashlib.md5(f"{artist}|{album}".encode("utf-8")).hexdigest()[:8]
    return f"{slug[:55]}-{h}"


def download_and_optimize_image(url: str, dest: str) -> bool:
    if os.path.exists(dest) and os.path.getsize(dest) > 1500:
        return True
    try:
        subprocess.run(
            ["curl", "-sL", "-A", USER_AGENT, "-o", dest, url],
            check=True,
            timeout=15,
        )
        if not os.path.exists(dest) or os.path.getsize(dest) <= 1000:
            return False

        with Image.open(dest) as img:
            w, h = img.size
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgba = img.convert("RGBA")
                bg = Image.new("RGB", rgba.size, (25, 28, 36))
                bg.paste(rgba, mask=rgba.split()[3])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            short_side = min(w, h)
            if short_side > TARGET_MIN_SIDE:
                scale = TARGET_MIN_SIDE / float(short_side)
                new_w = max(TARGET_MIN_SIDE, int(round(w * scale)))
                new_h = max(TARGET_MIN_SIDE, int(round(h * scale)))
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            tmp_path = dest + ".tmp.jpg"
            img.save(tmp_path, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        os.replace(tmp_path, dest)
        return True
    except Exception:
        return False


def fetch_spotify_playlist():
    if os.path.exists(RAW_CACHE_PATH):
        with open(RAW_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    if os.path.exists("/tmp/spotify_playlist_raw.json"):
        with open("/tmp/spotify_playlist_raw.json", "r", encoding="utf-8") as f:
            items = json.load(f)
        with open(RAW_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return items

    embed_url = f"https://open.spotify.com/embed/playlist/{PLAYLIST_ID}"
    req = urllib.request.Request(embed_url, headers={"User-Agent": USER_AGENT})
    html = urllib.request.urlopen(req).read().decode("utf-8", errors="replace")
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    data = json.loads(m.group(1))
    token = data["props"]["pageProps"]["state"]["settings"]["session"]["accessToken"]

    items = []
    for offset in range(0, 1000, 100):
        payload = json.dumps({
            "variables": {
                "uri": f"spotify:playlist:{PLAYLIST_ID}",
                "offset": offset,
                "limit": 100,
                "enableWatchFeedEntrypoint": False,
            },
            "operationName": "fetchPlaylist",
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "21ea11a6ac75a5f3e01fd365d29c18e0a4a8b7dc09f89bbb5d73910190c6acaf",
                }
            },
        }).encode("utf-8")

        req_q = urllib.request.Request(
            "https://api-partner.spotify.com/pathfinder/v2/query",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json;charset=UTF-8",
                "User-Agent": USER_AGENT,
            },
        )
        resp = json.loads(urllib.request.urlopen(req_q).read().decode("utf-8"))
        content = resp["data"]["playlistV2"]["content"]
        items.extend(content["items"])
        if len(items) >= content["totalCount"] or not content["items"]:
            break

    with open(RAW_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return items


def main():
    raw_items = fetch_spotify_playlist()
    print(f"Loaded {len(raw_items)} playlist items.")

    tracks_data = []
    download_tasks = {}

    for idx, item in enumerate(raw_items):
        order = idx + 1
        it = item["itemV2"]["data"]
        artist_items = it.get("artists", {}).get("items", [])
        artists_list = [a["profile"]["name"] for a in artist_items if a.get("profile", {}).get("name")]
        primary_artist = artists_list[0] if artists_list else "Nieznany wykonawca"
        artist_display = ", ".join(artists_list) if artists_list else primary_artist

        title = it.get("name", "").strip()
        album_obj = it.get("albumOfTrack", {})
        album_name = album_obj.get("name", "").strip()

        iso_date = (album_obj.get("date") or {}).get("isoString") or ""
        release_year = iso_date[:4] if len(iso_date) >= 4 else ""

        dur_ms = (it.get("trackDuration") or {}).get("totalMilliseconds") or 0
        dur_sec = int(round(dur_ms / 1000.0))

        added_at = (item.get("addedAt") or {}).get("isoString") or ""
        added_date = added_at[:10] if len(added_at) >= 10 else ""

        track_uri = it.get("uri", "")
        track_id = track_uri.split(":")[-1] if ":" in track_uri else ""
        spotify_url = f"https://open.spotify.com/track/{track_id}" if track_id else ""

        sources = (album_obj.get("coverArt") or {}).get("sources") or []
        cover_url = ""
        for s in sources:
            if s.get("width") == 300:
                cover_url = s.get("url")
                break
        if not cover_url and sources:
            cover_url = sources[0].get("url", "")

        slug = slugify(primary_artist, album_name or title)
        rel_cover = f"assets/covers/{slug}.jpg"
        full_cover = os.path.join(BASE_DIR, rel_cover)
        if cover_url:
            download_tasks[full_cover] = (cover_url, rel_cover)

        genre = ARTIST_GENRE_MAP.get(primary_artist, "Rock")

        tracks_data.append({
            "order": order,
            "artist": artist_display,
            "primaryArtist": primary_artist,
            "artists": artists_list,
            "title": title,
            "album": album_name,
            "releaseYear": release_year,
            "durationSeconds": dur_sec,
            "durationMs": dur_ms,
            "genre": genre,
            "cover": rel_cover,
            "addedDate": added_date,
            "spotifyUrl": spotify_url,
        })

    print(f"Downloading & optimizing {len(download_tasks)} unique album covers...")
    ok_count = 0
    with ThreadPoolExecutor(max_workers=24) as ex:
        futures = {
            ex.submit(download_and_optimize_image, url, dest): (dest, rel)
            for dest, (url, rel) in download_tasks.items()
        }
        for fut in as_completed(futures):
            if fut.result():
                ok_count += 1

    print(f"Covers downloaded/verified: {ok_count}/{len(download_tasks)}")

    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write("// Piosenka Tygodnia — Spotify playlist dataset (604 tracks, covers, genres, durations)\n")
        f.write("window.PIOSENKA_DATA = " + json.dumps(tracks_data, ensure_ascii=False, indent=2) + ";\n")

    print(f"Wrote {len(tracks_data)} tracks to {DATA_JS_PATH}")


if __name__ == "__main__":
    main()
