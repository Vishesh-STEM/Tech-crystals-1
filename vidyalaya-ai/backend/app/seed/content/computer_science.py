"""Class 12 Computer Science (Python) content pack - CBSE/NCERT aligned structure."""

NCERT_CS = "https://ncert.nic.in/textbook.php"
CBSE_SYLLABUS = "https://cbseacademic.nic.in/"

SUBJECT = {
    "code": "CS",
    "name": "Computer Science",
    "icon": "💻",
    "color": "cyan",
    "description": "Python programming, data structures, databases with SQL, and computer networks for CBSE Class 12 Computer Science.",
    "ncert_url": NCERT_CS,
    "chapters": [
        {
            "name": "Python Revision: Functions and Flow of Control",
            "number": 1,
            "ncert_url": NCERT_CS,
            "description": "Functions, arguments, scope and modular programming in Python.",
            "topics": [
                {
                    "name": "Functions, Arguments and Scope",
                    "difficulty": "easy",
                    "summary": "Functions package reusable logic; Python supports positional, default and keyword arguments, and names are resolved using the LEGB scope rule.",
                    "concepts": [
                        "def defines a function; return sends a value back (None by default)",
                        "Argument types: positional, default, keyword and variable length (*args, **kwargs)",
                        "Scope resolution order: Local, Enclosing, Global, Built-in (LEGB)",
                        "global and nonlocal keywords change where a name is bound",
                    ],
                    "examples": [
                        "def area(l, b=2): return l*b - calling area(5) uses the default b and returns 10.",
                    ],
                    "questions": [
                        {
                            "text": "What does a Python function return if it has no return statement?",
                            "options": ["A. 0", "B. None", "C. An empty string", "D. It raises an error"],
                            "answer": "B. None",
                            "explanation": "Python functions implicitly return None when execution ends without a return statement.",
                            "difficulty": "easy",
                            "concept": "Functions",
                        },
                        {
                            "text": "Which keyword lets a function modify a variable defined at module level?",
                            "options": ["A. static", "B. nonlocal", "C. global", "D. extern"],
                            "answer": "C. global",
                            "explanation": "global binds the name to the module-level variable; nonlocal is for enclosing function scopes.",
                            "difficulty": "medium",
                            "concept": "Scope",
                        },
                    ],
                },
            ],
        },
        {
            "name": "File Handling",
            "number": 2,
            "ncert_url": NCERT_CS,
            "description": "Text, binary and CSV files in Python.",
            "topics": [
                {
                    "name": "Text and Binary Files",
                    "difficulty": "medium",
                    "summary": "Python opens files in text or binary mode; text files store readable characters while binary files store objects serialised with pickle.",
                    "concepts": [
                        "open(file, mode) with modes r, w, a, r+, and 'b' for binary",
                        "with open(...) as f closes the file automatically even if an error occurs",
                        "Text methods: read(), readline(), readlines(), write(), writelines()",
                        "pickle.dump() and pickle.load() serialise and restore Python objects in binary files",
                    ],
                    "examples": [
                        "with open('data.txt') as f: lines = f.readlines() reads every line into a list.",
                    ],
                    "questions": [
                        {
                            "text": "Which file mode opens a file for writing and erases existing content?",
                            "options": ["A. 'r'", "B. 'a'", "C. 'w'", "D. 'r+'"],
                            "answer": "C. 'w'",
                            "explanation": "'w' truncates the file if it exists and creates it otherwise; 'a' appends without erasing.",
                            "difficulty": "easy",
                            "concept": "File modes",
                        },
                    ],
                },
                {
                    "name": "CSV Files and the csv Module",
                    "difficulty": "easy",
                    "summary": "CSV files store tabular data as comma separated text and Python's csv module reads and writes them row by row.",
                    "concepts": [
                        "csv.reader() returns rows as lists of strings",
                        "csv.writer().writerow() writes a single row; writerows() writes many",
                        "newline='' is used when opening a csv file for writing to avoid blank rows",
                        "delimiter argument supports files separated by other characters",
                    ],
                    "examples": [
                        "import csv; w = csv.writer(f); w.writerow(['roll','name','marks']) writes a header row.",
                    ],
                    "prerequisites": ["text-and-binary-files"],
                },
            ],
        },
        {
            "name": "Data Structures: Stack",
            "number": 3,
            "ncert_url": NCERT_CS,
            "description": "Stack operations using Python lists and their applications.",
            "topics": [
                {
                    "name": "Stack Implementation and Applications",
                    "difficulty": "medium",
                    "summary": "A stack is a LIFO structure implemented in Python with a list, using append() to push and pop() to remove the top element.",
                    "concepts": [
                        "LIFO: the last element pushed is the first popped",
                        "Operations: push, pop, peek/top, isEmpty",
                        "Underflow occurs when popping an empty stack - always check before popping",
                        "Applications: expression conversion and evaluation, undo operations, function call stack",
                    ],
                    "examples": [
                        "s = []; s.append(10); s.append(20); s.pop() returns 20, leaving [10].",
                    ],
                    "questions": [
                        {
                            "text": "A stack follows which order of operation?",
                            "options": ["A. FIFO", "B. LIFO", "C. Random access", "D. Priority order"],
                            "answer": "B. LIFO",
                            "explanation": "Last In First Out: the most recently pushed item is removed first.",
                            "difficulty": "easy",
                            "concept": "Stack",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Computer Networks",
            "number": 4,
            "ncert_url": NCERT_CS,
            "description": "Network types, topologies, devices, protocols and web services.",
            "topics": [
                {
                    "name": "Network Types, Topologies and Devices",
                    "difficulty": "easy",
                    "summary": "Networks are classified by geographic spread and arranged in topologies, with hubs, switches, routers and gateways connecting them.",
                    "concepts": [
                        "PAN, LAN, MAN and WAN differ in geographical coverage",
                        "Topologies: bus, star, tree, mesh - star is the most common in modern LANs",
                        "Switch forwards frames by MAC address; router forwards packets by IP address",
                        "Transmission media: twisted pair, coaxial, optical fibre, and wireless (radio, microwave, infrared)",
                    ],
                    "examples": [
                        "A school computer lab connected through a single switch is a star topology LAN.",
                    ],
                },
                {
                    "name": "Protocols, IP Addressing and Web Services",
                    "difficulty": "medium",
                    "summary": "Protocols define the rules of communication; IP addressing identifies hosts and application protocols such as HTTP and SMTP deliver web and mail services.",
                    "concepts": [
                        "TCP/IP, HTTP/HTTPS, FTP, SMTP, POP3 and their typical uses",
                        "IPv4 is 32-bit (dotted decimal) and IPv6 is 128-bit; MAC address is a 48-bit hardware address",
                        "DNS resolves a domain name to an IP address",
                        "Web terms: URL, web server, web browser, cookies and web hosting",
                    ],
                    "examples": [
                        "Typing a URL triggers a DNS lookup, then an HTTP request to the resolved IP address.",
                    ],
                },
            ],
        },
        {
            "name": "Database Concepts and SQL",
            "number": 5,
            "ncert_url": NCERT_CS,
            "description": "Relational model, keys, DDL and DML commands, functions and joins.",
            "topics": [
                {
                    "name": "Relational Model and Keys",
                    "difficulty": "easy",
                    "summary": "A relational database stores data in tables of rows and columns, with keys enforcing uniqueness and links between tables.",
                    "concepts": [
                        "Relation (table), tuple (row), attribute (column), degree and cardinality",
                        "Primary key uniquely identifies a row; candidate keys are the alternatives",
                        "Foreign key references the primary key of another table and enforces referential integrity",
                        "NULL means unknown, not zero or empty string",
                    ],
                    "examples": [
                        "In a STUDENT table, ADMNO can be the primary key while CLASSID is a foreign key to CLASS.",
                    ],
                },
                {
                    "name": "SQL Queries, Aggregate Functions and Joins",
                    "difficulty": "hard",
                    "summary": "SQL uses DDL commands to define structure and DML commands to manipulate data, with aggregate functions and joins answering analytical questions.",
                    "concepts": [
                        "DDL: CREATE, ALTER, DROP. DML: INSERT, UPDATE, DELETE, SELECT",
                        "Clauses: WHERE filters rows, GROUP BY groups them, HAVING filters groups, ORDER BY sorts",
                        "Aggregate functions: COUNT, SUM, AVG, MIN, MAX (they ignore NULLs, except COUNT(*))",
                        "Equi join matches rows of two tables on a common column using a WHERE or JOIN condition",
                    ],
                    "examples": [
                        "SELECT CLASS, AVG(MARKS) FROM STUDENT GROUP BY CLASS HAVING AVG(MARKS) > 60;",
                    ],
                    "prerequisites": ["relational-model-and-keys"],
                    "questions": [
                        {
                            "text": "Which SQL clause filters groups created by GROUP BY?",
                            "options": ["A. WHERE", "B. HAVING", "C. ORDER BY", "D. FILTER"],
                            "answer": "B. HAVING",
                            "explanation": "WHERE filters individual rows before grouping; HAVING filters the resulting groups.",
                            "difficulty": "medium",
                            "concept": "SQL clauses",
                        },
                        {
                            "text": "COUNT(*) differs from COUNT(column) because",
                            "options": [
                                "A. COUNT(*) counts all rows including NULLs",
                                "B. COUNT(*) is slower always",
                                "C. COUNT(column) counts all rows",
                                "D. They are identical",
                            ],
                            "answer": "A. COUNT(*) counts all rows including NULLs",
                            "explanation": "COUNT(column) skips NULL values in that column, while COUNT(*) counts every row.",
                            "difficulty": "hard",
                            "concept": "Aggregate functions",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Interface Python with MySQL",
            "number": 6,
            "ncert_url": NCERT_CS,
            "description": "Database connectivity from Python using a connector module.",
            "topics": [
                {
                    "name": "Python-MySQL Connectivity",
                    "difficulty": "medium",
                    "summary": "Python connects to MySQL through a connector module: create a connection, get a cursor, execute queries and commit changes.",
                    "concepts": [
                        "Steps: import connector -> connect() -> cursor() -> execute() -> fetch/commit -> close()",
                        "fetchone(), fetchmany(n) and fetchall() retrieve result sets",
                        "commit() is required after INSERT, UPDATE and DELETE",
                        "Parameterised queries (%s placeholders) prevent SQL injection",
                    ],
                    "examples": [
                        "cur.execute('SELECT * FROM student WHERE class=%s', (12,)); rows = cur.fetchall()",
                    ],
                    "prerequisites": ["sql-queries-aggregate-functions-and-joins"],
                },
            ],
        },
        {
            "name": "Society, Law and Ethics",
            "number": 7,
            "ncert_url": NCERT_CS,
            "description": "Digital footprint, cyber safety, IPR, cybercrime and e-waste.",
            "topics": [
                {
                    "name": "Cyber Safety, IPR and Digital Citizenship",
                    "difficulty": "easy",
                    "summary": "Responsible computing covers protecting one's digital footprint, respecting intellectual property and knowing the legal remedies for cybercrime.",
                    "concepts": [
                        "Digital footprint: active and passive traces left online",
                        "IPR: copyright, patent and trademark; plagiarism versus fair use",
                        "Cybercrimes: phishing, identity theft, cyberbullying; the IT Act provides remedies",
                        "E-waste management follows reduce, reuse and recycle principles",
                    ],
                    "examples": [
                        "Using a strong unique password and two factor authentication reduces the risk of identity theft.",
                    ],
                },
            ],
        },
        {
            "name": "Searching, Sorting and Algorithm Efficiency",
            "number": 8,
            "ncert_url": NCERT_CS,
            "description": "Linear and binary search, common sorting techniques and complexity.",
            "topics": [
                {
                    "name": "Searching and Sorting Techniques",
                    "difficulty": "medium",
                    "summary": "Linear search scans every element while binary search halves a sorted list each time; simple sorts such as bubble and insertion sort arrange data in O(n^2) time.",
                    "concepts": [
                        "Linear search O(n) works on unsorted data; binary search O(log n) needs sorted data",
                        "Bubble sort repeatedly swaps adjacent out-of-order elements",
                        "Insertion sort builds a sorted prefix one element at a time",
                        "Time complexity compares growth rates, not exact running time",
                    ],
                    "examples": [
                        "Binary search on a sorted list of 1000 items needs at most 10 comparisons.",
                    ],
                },
            ],
        },
    ],
}
