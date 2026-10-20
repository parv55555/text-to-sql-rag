"""
Database Initializer for Chinook Music Store & E-Commerce Sample Databases.
Creates realistic, relational SQLite databases with foreign keys and sample data.
"""

import sqlite3
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

def create_chinook_db(db_path: Path):
    """Generates the classic Chinook sample database with 11 relational tables."""
    if db_path.exists():
        # Check if already populated
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Customer")
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                print(f"[OK] Chinook DB already exists and has data: {db_path}")
                return
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    # Schema definition
    cur.executescript("""
    DROP TABLE IF EXISTS PlaylistTrack;
    DROP TABLE IF EXISTS Playlist;
    DROP TABLE IF EXISTS InvoiceLine;
    DROP TABLE IF EXISTS Invoice;
    DROP TABLE IF EXISTS Customer;
    DROP TABLE IF EXISTS Employee;
    DROP TABLE IF EXISTS Track;
    DROP TABLE IF EXISTS Genre;
    DROP TABLE IF EXISTS MediaType;
    DROP TABLE IF EXISTS Album;
    DROP TABLE IF EXISTS Artist;

    CREATE TABLE Artist (
        ArtistId INTEGER PRIMARY KEY AUTOINCREMENT,
        Name NVARCHAR(120) NOT NULL
    );

    CREATE TABLE Album (
        AlbumId INTEGER PRIMARY KEY AUTOINCREMENT,
        Title NVARCHAR(160) NOT NULL,
        ArtistId INTEGER NOT NULL,
        FOREIGN KEY (ArtistId) REFERENCES Artist(ArtistId) ON DELETE NO ACTION ON UPDATE NO ACTION
    );

    CREATE TABLE MediaType (
        MediaTypeId INTEGER PRIMARY KEY AUTOINCREMENT,
        Name NVARCHAR(120)
    );

    CREATE TABLE Genre (
        GenreId INTEGER PRIMARY KEY AUTOINCREMENT,
        Name NVARCHAR(120)
    );

    CREATE TABLE Track (
        TrackId INTEGER PRIMARY KEY AUTOINCREMENT,
        Name NVARCHAR(200) NOT NULL,
        AlbumId INTEGER,
        MediaTypeId INTEGER NOT NULL,
        GenreId INTEGER,
        Composer NVARCHAR(220),
        Milliseconds INTEGER NOT NULL,
        Bytes INTEGER,
        UnitPrice NUMERIC(10,2) NOT NULL,
        FOREIGN KEY (AlbumId) REFERENCES Album(AlbumId),
        FOREIGN KEY (MediaTypeId) REFERENCES MediaType(MediaTypeId),
        FOREIGN KEY (GenreId) REFERENCES Genre(GenreId)
    );

    CREATE TABLE Employee (
        EmployeeId INTEGER PRIMARY KEY AUTOINCREMENT,
        LastName NVARCHAR(20) NOT NULL,
        FirstName NVARCHAR(20) NOT NULL,
        Title NVARCHAR(30),
        ReportsTo INTEGER,
        BirthDate DATETIME,
        HireDate DATETIME,
        City NVARCHAR(40),
        State NVARCHAR(40),
        Country NVARCHAR(40),
        Email NVARCHAR(60),
        FOREIGN KEY (ReportsTo) REFERENCES Employee(EmployeeId)
    );

    CREATE TABLE Customer (
        CustomerId INTEGER PRIMARY KEY AUTOINCREMENT,
        FirstName NVARCHAR(40) NOT NULL,
        LastName NVARCHAR(20) NOT NULL,
        Company NVARCHAR(80),
        City NVARCHAR(40),
        State NVARCHAR(40),
        Country NVARCHAR(40),
        Email NVARCHAR(60) NOT NULL,
        SupportRepId INTEGER,
        FOREIGN KEY (SupportRepId) REFERENCES Employee(EmployeeId)
    );

    CREATE TABLE Invoice (
        InvoiceId INTEGER PRIMARY KEY AUTOINCREMENT,
        CustomerId INTEGER NOT NULL,
        InvoiceDate DATETIME NOT NULL,
        BillingAddress NVARCHAR(70),
        BillingCity NVARCHAR(40),
        BillingState NVARCHAR(40),
        BillingCountry NVARCHAR(40),
        BillingPostalCode NVARCHAR(10),
        Total NUMERIC(10,2) NOT NULL,
        FOREIGN KEY (CustomerId) REFERENCES Customer(CustomerId)
    );

    CREATE TABLE InvoiceLine (
        InvoiceLineId INTEGER PRIMARY KEY AUTOINCREMENT,
        InvoiceId INTEGER NOT NULL,
        TrackId INTEGER NOT NULL,
        UnitPrice NUMERIC(10,2) NOT NULL,
        Quantity INTEGER NOT NULL,
        FOREIGN KEY (InvoiceId) REFERENCES Invoice(InvoiceId),
        FOREIGN KEY (TrackId) REFERENCES Track(TrackId)
    );

    CREATE TABLE Playlist (
        PlaylistId INTEGER PRIMARY KEY AUTOINCREMENT,
        Name NVARCHAR(120)
    );

    CREATE TABLE PlaylistTrack (
        PlaylistId INTEGER NOT NULL,
        TrackId INTEGER NOT NULL,
        PRIMARY KEY (PlaylistId, TrackId),
        FOREIGN KEY (PlaylistId) REFERENCES Playlist(PlaylistId),
        FOREIGN KEY (TrackId) REFERENCES Track(TrackId)
    );
    """)

    # Populate Sample Data
    # Artists
    artists = [
        (1, "AC/DC"), (2, "Accept"), (3, "Aerosmith"), (4, "Alanis Morissette"),
        (5, "Alice In Chains"), (6, "Antônio Carlos Jobim"), (7, "Apocalyptica"),
        (8, "Audioslave"), (9, "BackBeat"), (10, "Billy Cobham"),
        (11, "Black Sabbath"), (12, "Deep Purple"), (13, "Led Zeppelin"),
        (14, "Miles Davis"), (15, "Queen"), (16, "Metallica"), (17, "Pink Floyd"),
        (18, "Iron Maiden"), (19, "The Beatles"), (20, "U2")
    ]
    cur.executemany("INSERT INTO Artist (ArtistId, Name) VALUES (?, ?)", artists)

    # Albums
    albums = [
        (1, "For Those About To Rock We Salute You", 1),
        (2, "Balls to the Wall", 2),
        (3, "Restless and Wild", 2),
        (4, "Let There Be Rock", 1),
        (5, "Big Ones", 3),
        (6, "Jagged Little Pill", 4),
        (7, "Facelift", 5),
        (8, "Warner 25 Anos", 6),
        (9, "Plays Metallica By Four Cellos", 7),
        (10, "Audioslave", 8),
        (11, "Out of Exile", 8),
        (12, "BackBeat Soundtrack", 9),
        (13, "The Best Of Billy Cobham", 10),
        (14, "Black Sabbath", 11),
        (15, "Machine Head", 12),
        (16, "Led Zeppelin IV", 13),
        (17, "Kind of Blue", 14),
        (18, "A Night at the Opera", 15),
        (19, "Master of Puppets", 16),
        (20, "The Dark Side of the Moon", 17),
        (21, "The Number of the Beast", 18),
        (22, "Abbey Road", 19),
        (23, "The Joshua Tree", 20)
    ]
    cur.executemany("INSERT INTO Album (AlbumId, Title, ArtistId) VALUES (?, ?, ?)", albums)

    # Genres
    genres = [
        (1, "Rock"), (2, "Jazz"), (3, "Metal"), (4, "Alternative & Punk"),
        (5, "Rock And Roll"), (6, "Blues"), (7, "Latin"), (8, "Reggae"),
        (9, "Pop"), (10, "Soundtrack"), (11, "Bossa Nova"), (12, "Classical")
    ]
    cur.executemany("INSERT INTO Genre (GenreId, Name) VALUES (?, ?)", genres)

    # MediaTypes
    media_types = [
        (1, "MPEG audio file"), (2, "Protected AAC audio file"),
        (3, "Protected MPEG-4 video file"), (4, "Purchased AAC audio file"),
        (5, "AAC audio file")
    ]
    cur.executemany("INSERT INTO MediaType (MediaTypeId, Name) VALUES (?, ?)", media_types)

    # Tracks
    tracks = [
        (1, "For Those About To Rock (We Salute You)", 1, 1, 1, "Angus Young, Malcolm Young, Brian Johnson", 343719, 11170334, 0.99),
        (2, "Balls to the Wall", 2, 2, 3, "U. Dirkschneider, W. Hoffmann, P. Baltes", 342562, 5510424, 0.99),
        (3, "Fast As a Shark", 3, 2, 3, "F. Baltes, S. Kaufman, U. Dirkchneider", 230619, 3990994, 0.99),
        (4, "Restless and Wild", 3, 2, 3, "F. Baltes, R.A. Smith-Diesel, S. Kaufman", 252051, 4331779, 0.99),
        (5, "Princess of the Dawn", 3, 2, 3, "Deaffy & R.A. Smith-Diesel", 375418, 6290521, 0.99),
        (6, "Go Down", 4, 1, 1, "AC/DC", 331180, 10847611, 0.99),
        (7, "Dog Eat Dog", 4, 1, 1, "AC/DC", 215196, 7032162, 0.99),
        (8, "Let There Be Rock", 4, 1, 1, "AC/DC", 366654, 12021261, 0.99),
        (9, "Bad Boy Boogie", 4, 1, 1, "AC/DC", 267728, 8776140, 0.99),
        (10, "Problem Child", 4, 1, 1, "AC/DC", 325041, 10617116, 0.99),
        (11, "Overdose", 4, 1, 1, "AC/DC", 369319, 12066294, 0.99),
        (12, "Hell Ain't A Bad Place To Be", 4, 1, 1, "AC/DC", 254380, 8331286, 0.99),
        (13, "Whole Lotta Rosie", 4, 1, 1, "AC/DC", 323761, 10597070, 0.99),
        (14, "Walk On Water", 5, 1, 1, "Steven Tyler, Joe Perry, Jack Blades", 295680, 9719579, 0.99),
        (15, "Love In An Elevator", 5, 1, 1, "Steven Tyler, Joe Perry", 338181, 11005217, 0.99),
        (16, "Rag Doll", 5, 1, 1, "Steven Tyler, Joe Perry, Jim Vallance", 264698, 8675345, 0.99),
        (17, "What It Takes", 5, 1, 1, "Steven Tyler, Joe Perry, Desmond Child", 309707, 10144730, 0.99),
        (18, "Dude (Looks Like A Lady)", 5, 1, 1, "Steven Tyler, Joe Perry, Desmond Child", 264855, 8679940, 0.99),
        (19, "Janie's Got A Gun", 5, 1, 1, "Steven Tyler, Tom Hamilton", 330736, 10869391, 0.99),
        (20, "Cryin'", 5, 1, 1, "Steven Tyler, Joe Perry, Taylor Rhodes", 309263, 10056995, 0.99),
        (21, "Smells Like Teen Spirit", 10, 1, 4, "Kurt Cobain", 301000, 9800000, 1.29),
        (22, "Bohemian Rhapsody", 18, 1, 1, "Freddie Mercury", 354000, 11500000, 1.29),
        (23, "Stairway to Heaven", 16, 1, 1, "Jimmy Page, Robert Plant", 482000, 15000000, 1.29),
        (24, "So What", 17, 1, 2, "Miles Davis", 562000, 18000000, 1.29),
        (25, "Master of Puppets", 19, 1, 3, "James Hetfield, Lars Ulrich", 515000, 16500000, 1.29),
        (26, "Time", 20, 1, 1, "Roger Waters, David Gilmour", 425000, 13700000, 1.29),
        (27, "Hallowed Be Thy Name", 21, 1, 3, "Steve Harris", 432000, 14000000, 1.29),
        (28, "Come Together", 22, 1, 1, "John Lennon, Paul McCartney", 259000, 8400000, 1.29),
        (29, "Where the Streets Have No Name", 23, 1, 1, "U2", 337000, 10900000, 1.29),
        (30, "With or Without You", 23, 1, 1, "U2", 296000, 9600000, 1.29)
    ]
    cur.executemany("INSERT INTO Track (TrackId, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, UnitPrice) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tracks)

    # Employees
    employees = [
        (1, "Adams", "Andrew", "General Manager", None, "1962-02-18", "2016-08-14", "Edmonton", "AB", "Canada", "andrew@chinookcorp.com"),
        (2, "Edwards", "Nancy", "Sales Manager", 1, "1958-12-08", "2016-05-01", "Calgary", "AB", "Canada", "nancy@chinookcorp.com"),
        (3, "Peacock", "Jane", "Sales Support Agent", 2, "1973-08-29", "2016-04-01", "Calgary", "AB", "Canada", "jane@chinookcorp.com"),
        (4, "Park", "Margaret", "Sales Support Agent", 2, "1947-09-19", "2017-05-03", "Calgary", "AB", "Canada", "margaret@chinookcorp.com"),
        (5, "Johnson", "Steve", "Sales Support Agent", 2, "1965-03-03", "2017-10-17", "Calgary", "AB", "Canada", "steve@chinookcorp.com")
    ]
    cur.executemany("INSERT INTO Employee (EmployeeId, LastName, FirstName, Title, ReportsTo, BirthDate, HireDate, City, State, Country, Email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", employees)

    # Customers
    customers = [
        (1, "Luís", "Gonçalves", "Embraer - Empresa Brasileira de Aeronáutica S.A.", "São José dos Campos", "SP", "Brazil", "luisg@embraer.com.br", 3),
        (2, "Leonie", "Köhler", None, "Stuttgart", None, "Germany", "leonekohler@surfeu.de", 5),
        (3, "François", "Tremblay", None, "Montréal", "QC", "Canada", "ftremblay@gmail.com", 3),
        (4, "Bjørn", "Hansen", None, "Oslo", None, "Norway", "bjorn.hansen@yahoo.no", 4),
        (5, "František", "Wichterlová", None, "Prague", None, "Czech Republic", "frantisekw@prague.cz", 4),
        (6, "Helena", "Holý", None, "Prague", None, "Czech Republic", "hholy@gmail.com", 5),
        (7, "Astrid", "Gruber", None, "Vienne", None, "Austria", "astrid.gruber@apple.at", 5),
        (8, "Daan", "Peeters", None, "Brussels", None, "Belgium", "daan_peeters@apple.be", 4),
        (9, "Kara", "Nielsen", None, "Copenhagen", None, "Denmark", "kara.nielsen@jubii.dk", 4),
        (10, "Eduardo", "Martins", "Woodstock Discos", "São Paulo", "SP", "Brazil", "eduardo@woodstock.com.br", 4),
        (11, "Alexandre", "Rocha", "Banco do Brasil S.A.", "São Paulo", "SP", "Brazil", "alero@uol.com.br", 5),
        (12, "Roberto", "Almeida", "Riotur", "Rio de Janeiro", "RJ", "Brazil", "roberto.almeida@riotur.gov.br", 3),
        (13, "Fernanda", "Ramos", None, "Brasília", "DF", "Brazil", "ferramosa@uol.com.br", 4),
        (14, "Mark", "Philips", "Telus", "Edmonton", "AB", "Canada", "mphilips12@shaw.ca", 5),
        (15, "Jennifer", "Peterson", None, "Vancouver", "BC", "Canada", "jenniferp@rogers.ca", 3),
        (16, "Frank", "Harris", "Google Inc.", "Mountain View", "CA", "USA", "frank.harris@google.com", 3),
        (17, "Jack", "Smith", "Microsoft Corporation", "Redmond", "WA", "USA", "jacksmith@microsoft.com", 4),
        (18, "Michelle", "Brooks", None, "New York", "NY", "USA", "michelleb@aol.com", 3),
        (19, "Tim", "Goyer", "Apple Inc.", "Cupertino", "CA", "USA", "tgoyer@apple.com", 3),
        (20, "Dan", "Miller", None, "Mountain View", "CA", "USA", "dmiller@comcast.net", 4)
    ]
    cur.executemany("INSERT INTO Customer (CustomerId, FirstName, LastName, Company, City, State, Country, Email, SupportRepId) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", customers)

    # Invoices
    invoices = [
        (1, 2, "2023-01-01 00:00:00", "Theodor-Heuss-Straße 34", "Stuttgart", None, "Germany", "70174", 3.96),
        (2, 4, "2023-01-02 00:00:00", "Ullevålsveien 14", "Oslo", None, "Norway", "0171", 5.94),
        (3, 8, "2023-01-03 00:00:00", "Grétrystraat 63", "Brussels", None, "Belgium", "1000", 8.91),
        (4, 14, "2023-01-06 00:00:00", "8210 111 ST NW", "Edmonton", "AB", "Canada", "T6G 2C7", 13.86),
        (5, 16, "2023-02-11 00:00:00", "1600 Amphitheatre Parkway", "Mountain View", "CA", "USA", "94043-1351", 15.84),
        (6, 17, "2023-02-19 00:00:00", "1 Microsoft Way", "Redmond", "WA", "USA", "98052-8300", 25.74),
        (7, 19, "2023-03-04 00:00:00", "1 Infinite Loop", "Cupertino", "CA", "USA", "95014", 17.82),
        (8, 1, "2023-03-15 00:00:00", "Av. Brigadeiro Faria Lima, 2170", "São José dos Campos", "SP", "Brazil", "12227-000", 9.90),
        (9, 3, "2023-04-10 00:00:00", "1498 rue Bélanger", "Montréal", "QC", "Canada", "H2G 1A7", 18.81),
        (10, 5, "2023-05-12 00:00:00", "Klanova 9/506", "Prague", None, "Czech Republic", "14700", 12.87),
        (11, 10, "2023-06-20 00:00:00", "Rua Dr. Falcão Filho, 155", "São Paulo", "SP", "Brazil", "01007-010", 21.78),
        (12, 12, "2023-07-04 00:00:00", "Praça Pio X, 119", "Rio de Janeiro", "RJ", "Brazil", "20040-020", 14.85),
        (13, 16, "2023-08-15 00:00:00", "1600 Amphitheatre Parkway", "Mountain View", "CA", "USA", "94043-1351", 31.68),
        (14, 18, "2023-09-01 00:00:00", "627 Broadway", "New York", "NY", "USA", "10012-2612", 22.77),
        (15, 20, "2023-10-18 00:00:00", "541 Del Medio Ave.", "Mountain View", "CA", "USA", "94040-111", 19.80)
    ]
    cur.executemany("INSERT INTO Invoice (InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity, BillingState, BillingCountry, BillingPostalCode, Total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", invoices)

    # Invoice Lines
    invoice_lines = [
        (1, 1, 1, 0.99, 2),
        (2, 1, 2, 0.99, 2),
        (3, 2, 3, 0.99, 2),
        (4, 2, 4, 0.99, 2),
        (5, 2, 5, 0.99, 2),
        (6, 3, 6, 0.99, 3),
        (7, 3, 7, 0.99, 3),
        (8, 3, 8, 0.99, 3),
        (9, 4, 14, 0.99, 5),
        (10, 4, 15, 0.99, 5),
        (11, 4, 16, 0.99, 4),
        (12, 5, 21, 1.29, 6),
        (13, 5, 22, 1.29, 6),
        (14, 6, 22, 1.29, 10),
        (15, 6, 23, 1.29, 10),
        (16, 7, 24, 1.29, 6),
        (17, 7, 25, 1.29, 8),
        (18, 8, 1, 0.99, 5),
        (19, 8, 8, 0.99, 5),
        (20, 9, 26, 1.29, 7),
        (21, 9, 27, 1.29, 7),
        (22, 10, 28, 1.29, 5),
        (23, 10, 29, 1.29, 5),
        (24, 11, 30, 1.29, 8),
        (25, 11, 22, 1.29, 8),
        (26, 12, 18, 0.99, 15),
        (27, 13, 22, 1.29, 12),
        (28, 13, 23, 1.29, 12),
        (29, 14, 15, 0.99, 13),
        (30, 14, 16, 0.99, 10),
        (31, 15, 26, 1.29, 15)
    ]
    cur.executemany("INSERT INTO InvoiceLine (InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity) VALUES (?, ?, ?, ?, ?)", invoice_lines)

    # Playlists
    playlists = [
        (1, "Music"), (2, "Movies"), (3, "TV Shows"), (4, "Audiobooks"),
        (5, "90s Music"), (6, "Audiobooks"), (7, "Movies"), (8, "Music"),
        (9, "Music Videos"), (10, "TV Shows"), (11, "Brazilian Music"),
        (12, "Classic Rock"), (13, "Heavy Metal"), (14, "Grunge"),
        (15, "On-The-Go 1")
    ]
    cur.executemany("INSERT INTO Playlist (PlaylistId, Name) VALUES (?, ?)", playlists)

    # PlaylistTrack
    playlist_tracks = [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
        (12, 1), (12, 6), (12, 7), (12, 8), (12, 14), (12, 15), (12, 22), (12, 23),
        (13, 2), (13, 3), (13, 4), (13, 5), (13, 25), (13, 27),
        (14, 21),
        (15, 22), (15, 23), (15, 26), (15, 28), (15, 30)
    ]
    cur.executemany("INSERT INTO PlaylistTrack (PlaylistId, TrackId) VALUES (?, ?)", playlist_tracks)

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Created Chinook database at: {db_path}")


def create_ecommerce_db(db_path: Path):
    """Generates an E-Commerce / Retail sample database with 5 tables."""
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Customers")
            count = cur.fetchone()[0]
            conn.close()
            if count > 0:
                print(f"[OK] E-Commerce DB already exists: {db_path}")
                return
        except Exception:
            pass

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    cur.executescript("""
    DROP TABLE IF EXISTS OrderItems;
    DROP TABLE IF EXISTS Orders;
    DROP TABLE IF EXISTS Products;
    DROP TABLE IF EXISTS Categories;
    DROP TABLE IF EXISTS Customers;

    CREATE TABLE Categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE Products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        price NUMERIC(10,2) NOT NULL,
        stock_quantity INTEGER NOT NULL,
        FOREIGN KEY (category_id) REFERENCES Categories(category_id)
    );

    CREATE TABLE Customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        city TEXT,
        country TEXT,
        signup_date DATE NOT NULL
    );

    CREATE TABLE Orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        status TEXT NOT NULL,
        total_amount NUMERIC(10,2) NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );

    CREATE TABLE OrderItems (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price NUMERIC(10,2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES Orders(order_id),
        FOREIGN KEY (product_id) REFERENCES Products(product_id)
    );
    """)

    # Categories
    categories = [
        (1, "Electronics", "Phones, laptops, accessories and gadgets"),
        (2, "Audio", "Headphones, speakers, sound systems"),
        (3, "Home & Kitchen", "Appliances, kitchenware, furniture"),
        (4, "Footwear & Apparel", "Shoes, sportswear, streetwear")
    ]
    cur.executemany("INSERT INTO Categories VALUES (?, ?, ?)", categories)

    # Products
    products = [
        (1, "Pro Laptop 16", 1, 1499.99, 45),
        (2, "Ultra Smartphone 5G", 1, 899.99, 70),
        (3, "Wireless Noise-Canceling Headphones", 2, 249.99, 120),
        (4, "Bluetooth Portable Speaker", 2, 79.99, 200),
        (5, "Mechanical Gaming Keyboard", 1, 119.99, 85),
        (6, "Espresso Machine Pro", 3, 349.99, 30),
        (7, "Ergonomic Office Chair", 3, 229.99, 40),
        (8, "Running Performance Sneakers", 4, 129.99, 90),
        (9, "Smart Fitness Tracker Watch", 1, 159.99, 110)
    ]
    cur.executemany("INSERT INTO Products VALUES (?, ?, ?, ?, ?)", products)

    # Customers
    custs = [
        (1, "Aarav Sharma", "aarav@techmail.com", "Bangalore", "India", "2023-01-15"),
        (2, "Emma Watson", "emma.w@ukmail.co.uk", "London", "UK", "2023-02-10"),
        (3, "Liam Miller", "lmiller@usmail.com", "Austin", "USA", "2023-03-05"),
        (4, "Sophia Chen", "schen@singmail.sg", "Singapore", "Singapore", "2023-04-12"),
        (5, "Mateo Rodriguez", "mateo.r@madrid.es", "Madrid", "Spain", "2023-05-20"),
        (6, "Chloe Dubois", "cdubois@paris.fr", "Paris", "France", "2023-06-18")
    ]
    cur.executemany("INSERT INTO Customers VALUES (?, ?, ?, ?, ?, ?)", custs)

    # Orders
    orders = [
        (1, 1, "2024-01-10", "Delivered", 1749.98),
        (2, 2, "2024-01-15", "Delivered", 249.99),
        (3, 3, "2024-02-01", "Delivered", 979.98),
        (4, 1, "2024-02-20", "Delivered", 119.99),
        (5, 4, "2024-03-05", "Shipped", 1499.99),
        (6, 5, "2024-03-12", "Delivered", 479.98),
        (7, 6, "2024-03-25", "Processing", 349.99),
        (8, 2, "2024-04-02", "Delivered", 159.99),
        (9, 3, "2024-04-18", "Delivered", 229.99)
    ]
    cur.executemany("INSERT INTO Orders VALUES (?, ?, ?, ?, ?)", orders)

    # OrderItems
    items = [
        (1, 1, 1, 1, 1499.99),
        (2, 1, 3, 1, 249.99),
        (3, 2, 3, 1, 249.99),
        (4, 3, 2, 1, 899.99),
        (5, 3, 4, 1, 79.99),
        (6, 4, 5, 1, 119.99),
        (7, 5, 1, 1, 1499.99),
        (8, 6, 3, 1, 249.99),
        (9, 6, 7, 1, 229.99),
        (10, 7, 6, 1, 349.99),
        (11, 8, 9, 1, 159.99),
        (12, 9, 7, 1, 229.99)
    ]
    cur.executemany("INSERT INTO OrderItems VALUES (?, ?, ?, ?, ?)", items)

    conn.commit()
    conn.close()
    print(f"[SUCCESS] Created E-Commerce database at: {db_path}")

def init_all_databases():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    create_chinook_db(DATA_DIR / "chinook.db")
    create_ecommerce_db(DATA_DIR / "ecommerce.db")

if __name__ == "__main__":
    init_all_databases()
