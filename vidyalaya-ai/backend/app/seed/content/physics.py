"""Class 12 Physics content pack (NCERT aligned structure).

Only original short summaries, concept statements and practice questions are
stored here - no NCERT text is reproduced. Every chapter links to the official
NCERT chapter PDF so students read the textbook from the source.
"""

NCERT_BOOK_1 = "https://ncert.nic.in/textbook.php?leph1=0-8"
NCERT_BOOK_2 = "https://ncert.nic.in/textbook.php?leph2=0-6"


def _pdf(code: str) -> str:
    return f"https://ncert.nic.in/textbook/pdf/{code}.pdf"


SUBJECT = {
    "code": "PHY",
    "name": "Physics",
    "icon": "🧲",
    "color": "violet",
    "description": "Electrostatics, current electricity, magnetism, optics and modern physics for CBSE Class 12.",
    "ncert_url": NCERT_BOOK_1,
    "chapters": [
        {
            "name": "Electric Charges and Fields",
            "number": 1,
            "ncert_url": _pdf("leph101"),
            "description": "Charge, Coulomb's law, electric field and Gauss's law.",
            "topics": [
                {
                    "name": "Coulomb's Law and Superposition",
                    "difficulty": "easy",
                    "summary": "Coulomb's law gives the force between two point charges, and the superposition principle lets you add such forces as vectors when many charges are present.",
                    "concepts": [
                        "Force between point charges: F = k q1 q2 / r^2 with k = 1/(4 pi epsilon0) = 9x10^9 N m^2 C^-2",
                        "Force is along the line joining the charges: repulsive for like charges, attractive for unlike charges",
                        "Superposition principle: the net force on a charge is the vector sum of the forces due to every other charge",
                        "Charge is quantised (q = ne) and conserved in every isolated system",
                    ],
                    "examples": [
                        "Two charges of +2 microC and -3 microC placed 30 cm apart attract each other with F = 9x10^9 x (2x10^-6)(3x10^-6)/(0.3)^2 = 0.6 N.",
                    ],
                    "questions": [
                        {
                            "text": "Two point charges are separated by a distance r. If the separation is doubled, the electrostatic force becomes",
                            "options": ["A. Twice", "B. Half", "C. One-fourth", "D. Unchanged"],
                            "answer": "C. One-fourth",
                            "explanation": "Coulomb force varies as 1/r^2, so doubling r reduces F by a factor of 4.",
                            "difficulty": "easy",
                            "concept": "Coulomb's law",
                        },
                        {
                            "text": "The SI unit of the permittivity of free space epsilon0 is",
                            "options": ["A. N m^2 C^-2", "B. C^2 N^-1 m^-2", "C. C N^-1", "D. N C^-1"],
                            "answer": "B. C^2 N^-1 m^-2",
                            "explanation": "From F = q1q2/(4 pi epsilon0 r^2), epsilon0 has units C^2 N^-1 m^-2.",
                            "difficulty": "medium",
                            "concept": "Coulomb's law",
                        },
                    ],
                },
                {
                    "name": "Electric Field and Field Lines",
                    "difficulty": "medium",
                    "summary": "The electric field is the force per unit positive test charge; field lines are a picture of that field, never crossing and always starting on positive charge and ending on negative charge.",
                    "concepts": [
                        "E = F/q0 measured in N/C or V/m, a vector quantity",
                        "Field of a point charge: E = kq/r^2 directed radially outward for positive charge",
                        "Field lines are continuous, never intersect, and their density indicates field strength",
                        "A dipole of moment p in a uniform field experiences torque tau = p x E but zero net force",
                    ],
                    "examples": [
                        "On the axis of a short dipole at distance r, E = 2kp/r^3; on the equatorial line E = kp/r^3 in the opposite direction.",
                    ],
                },
                {
                    "name": "Gauss's Law and Applications",
                    "difficulty": "hard",
                    "summary": "Gauss's law states that the net electric flux through a closed surface equals the enclosed charge divided by epsilon0, which turns symmetric problems into one-line calculations.",
                    "concepts": [
                        "Flux phi = integral E . dA and Gauss's law phi = q_enclosed / epsilon0",
                        "Infinite line charge: E = lambda /(2 pi epsilon0 r)",
                        "Infinite charged sheet: E = sigma /(2 epsilon0), independent of distance",
                        "Field inside a uniformly charged conducting shell is zero; outside it behaves as a point charge",
                    ],
                    "examples": [
                        "For a spherical shell of radius R carrying charge Q, E = kQ/r^2 for r > R and E = 0 for r < R.",
                    ],
                    "prerequisites": ["electric-field-and-field-lines"],
                },
            ],
        },
        {
            "name": "Electrostatic Potential and Capacitance",
            "number": 2,
            "ncert_url": _pdf("leph102"),
            "description": "Potential, equipotential surfaces, capacitors, dielectrics and energy storage.",
            "topics": [
                {
                    "name": "Electric Potential and Potential Energy",
                    "difficulty": "medium",
                    "summary": "Electric potential is the work done per unit charge in bringing a test charge from infinity to a point, and potential energy is the work stored in an assembled charge configuration.",
                    "concepts": [
                        "V = W/q0, a scalar measured in volts; V = kq/r for a point charge",
                        "Relation with field: E = -dV/dr, so field points from high to low potential",
                        "Potential energy of a pair: U = k q1 q2 / r",
                        "Equipotential surfaces are always perpendicular to field lines and no work is done moving along them",
                    ],
                    "examples": [
                        "Work done in moving 2 microC through a potential difference of 5 V is W = qV = 10 microJ.",
                    ],
                },
                {
                    "name": "Capacitors, Combinations and Dielectrics",
                    "difficulty": "medium",
                    "summary": "A capacitor stores charge at a given potential difference; its capacitance depends only on geometry and the dielectric between the plates.",
                    "concepts": [
                        "C = Q/V, unit farad; parallel plate capacitor C = epsilon0 A / d",
                        "Series: 1/C = 1/C1 + 1/C2 ... (same charge). Parallel: C = C1 + C2 ... (same voltage)",
                        "Inserting a dielectric of constant K multiplies capacitance by K",
                        "Energy stored U = 1/2 CV^2 = Q^2/(2C), with energy density u = 1/2 epsilon0 E^2",
                    ],
                    "examples": [
                        "Two capacitors of 3 microF and 6 microF in series give C = 2 microF; in parallel they give 9 microF.",
                    ],
                    "prerequisites": ["electric-potential-and-potential-energy"],
                    "questions": [
                        {
                            "text": "The capacitance of a parallel plate capacitor is doubled when",
                            "options": [
                                "A. The plate separation is doubled",
                                "B. The plate area is doubled",
                                "C. The charge on the plates is doubled",
                                "D. The potential difference is doubled",
                            ],
                            "answer": "B. The plate area is doubled",
                            "explanation": "C = epsilon0 A/d, so C is proportional to A and inversely proportional to d. Charge and voltage do not change capacitance.",
                            "difficulty": "easy",
                            "concept": "Capacitance",
                        },
                        {
                            "text": "A 4 microF capacitor is charged to 100 V. The energy stored is",
                            "options": ["A. 0.02 J", "B. 0.04 J", "C. 0.2 J", "D. 2 J"],
                            "answer": "A. 0.02 J",
                            "explanation": "U = 1/2 CV^2 = 0.5 x 4x10^-6 x 10^4 = 0.02 J.",
                            "difficulty": "medium",
                            "concept": "Energy stored in a capacitor",
                        },
                        {
                            "text": "When a dielectric slab of constant K is inserted into an isolated charged capacitor, the potential difference",
                            "options": ["A. Increases K times", "B. Decreases K times", "C. Stays the same", "D. Becomes zero"],
                            "answer": "B. Decreases K times",
                            "explanation": "Charge is constant on an isolated capacitor; C becomes KC so V = Q/C falls by a factor K.",
                            "difficulty": "hard",
                            "concept": "Dielectrics",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Current Electricity",
            "number": 3,
            "ncert_url": _pdf("leph103"),
            "description": "Ohm's law, resistivity, EMF, Kirchhoff's rules, Wheatstone bridge and meter bridge.",
            "topics": [
                {
                    "name": "Electric Current, Drift Velocity and Ohm's Law",
                    "difficulty": "medium",
                    "summary": "Current is the rate of flow of charge, produced by a slow drift of free electrons; Ohm's law links it to potential difference through resistance for ohmic conductors at constant temperature.",
                    "concepts": [
                        "I = q/t = n A e v_d, where v_d is drift velocity and n the free electron density",
                        "Ohm's law V = IR holds at constant temperature for ohmic conductors",
                        "Resistance R = rho L / A; resistivity rho is a property of the material",
                        "Metals: rho increases with temperature, rho_t = rho_0 (1 + alpha delta T); semiconductors behave oppositely",
                    ],
                    "examples": [
                        "A wire of resistivity 1.7x10^-8 ohm m, length 2 m and area 1 mm^2 has R = rho L/A = 0.034 ohm.",
                    ],
                    "questions": [
                        {
                            "text": "A wire is stretched to twice its length keeping its volume constant. Its resistance becomes",
                            "options": ["A. 2R", "B. 4R", "C. R/2", "D. R/4"],
                            "answer": "B. 4R",
                            "explanation": "Doubling length halves the area at constant volume, so R = rho L/A increases by 2 x 2 = 4.",
                            "difficulty": "hard",
                            "concept": "Resistivity",
                        },
                        {
                            "text": "Drift velocity of free electrons in a metallic conductor carrying a steady current is of the order of",
                            "options": ["A. 10^8 m/s", "B. 10^6 m/s", "C. 10^-4 m/s", "D. 10^-15 m/s"],
                            "answer": "C. 10^-4 m/s",
                            "explanation": "Drift velocity is typically a fraction of a millimetre per second even though the signal travels near light speed.",
                            "difficulty": "medium",
                            "concept": "Drift velocity",
                        },
                    ],
                },
                {
                    "name": "Kirchhoff's Laws and Circuit Analysis",
                    "difficulty": "hard",
                    "summary": "Kirchhoff's junction rule expresses conservation of charge and the loop rule expresses conservation of energy; together they solve any multi-loop circuit that Ohm's law alone cannot.",
                    "concepts": [
                        "Junction rule: the algebraic sum of currents at a junction is zero (sum in = sum out)",
                        "Loop rule: the algebraic sum of potential changes around any closed loop is zero",
                        "Sign convention: a drop of IR when moving with the current, a rise of EMF when entering the negative terminal",
                        "Wheatstone bridge is balanced when P/Q = R/S and then no current flows through the galvanometer",
                    ],
                    "examples": [
                        "In a balanced Wheatstone bridge with P = 10 ohm, Q = 20 ohm and R = 15 ohm, S = QR/P = 30 ohm.",
                    ],
                    "prerequisites": ["electric-current-drift-velocity-and-ohms-law"],
                    "questions": [
                        {
                            "text": "Kirchhoff's junction rule is a statement of the conservation of",
                            "options": ["A. Energy", "B. Charge", "C. Momentum", "D. Magnetic flux"],
                            "answer": "B. Charge",
                            "explanation": "No charge accumulates at a junction, so the current entering equals the current leaving.",
                            "difficulty": "easy",
                            "concept": "Kirchhoff's Laws",
                        },
                        {
                            "text": "Kirchhoff's loop rule follows from the conservation of",
                            "options": ["A. Charge", "B. Energy", "C. Mass", "D. Current"],
                            "answer": "B. Energy",
                            "explanation": "Taking a charge around a closed loop returns it to the same potential, so the net energy change is zero.",
                            "difficulty": "easy",
                            "concept": "Kirchhoff's Laws",
                        },
                        {
                            "text": "In a balanced Wheatstone bridge, the galvanometer is replaced by a cell. The balance condition P/Q = R/S",
                            "options": [
                                "A. No longer holds",
                                "B. Still holds because it does not depend on the galvanometer branch",
                                "C. Depends on the EMF of the new cell",
                                "D. Holds only for equal resistances",
                            ],
                            "answer": "B. Still holds because it does not depend on the galvanometer branch",
                            "explanation": "At balance the bridge diagonal carries no current, so what is connected across it does not affect the condition.",
                            "difficulty": "hard",
                            "concept": "Wheatstone bridge",
                        },
                    ],
                },
                {
                    "name": "EMF, Internal Resistance and Cell Combinations",
                    "difficulty": "medium",
                    "summary": "A real cell has internal resistance, so the terminal voltage falls below the EMF whenever current is drawn; cells can be combined in series or parallel to increase voltage or current capacity.",
                    "concepts": [
                        "Terminal voltage V = E - I r while discharging, V = E + I r while charging",
                        "Series: E_eq = E1 + E2, r_eq = r1 + r2. Parallel (identical cells): E_eq = E, r_eq = r/n",
                        "Maximum power is delivered to an external resistance when R = r",
                        "A potentiometer measures EMF without drawing current, so it is more accurate than a voltmeter",
                    ],
                    "examples": [
                        "A cell of EMF 2 V with internal resistance 0.5 ohm drives 1 A: terminal voltage is 2 - 1x0.5 = 1.5 V.",
                    ],
                },
            ],
        },
        {
            "name": "Moving Charges and Magnetism",
            "number": 4,
            "ncert_url": _pdf("leph104"),
            "description": "Magnetic force, Biot-Savart law, Ampere's law, solenoids and moving coil galvanometer.",
            "topics": [
                {
                    "name": "Magnetic Force on Charges and Currents",
                    "difficulty": "medium",
                    "summary": "A charge moving in a magnetic field feels a force perpendicular to both its velocity and the field, which makes charged particles move in circles and current-carrying wires experience sideways forces.",
                    "concepts": [
                        "Lorentz force F = q(v x B); magnitude qvB sin theta, zero when v is parallel to B",
                        "Force on a current element: F = I L x B, magnitude BIL sin theta",
                        "Circular motion radius r = mv/(qB) and cyclotron frequency f = qB/(2 pi m)",
                        "Magnetic force does no work because it is always perpendicular to velocity",
                    ],
                    "examples": [
                        "A proton moving at 10^6 m/s perpendicular to a 0.5 T field moves in a circle of radius r = mv/qB ~ 2.1 cm.",
                    ],
                },
                {
                    "name": "Biot-Savart Law, Ampere's Law and Solenoids",
                    "difficulty": "hard",
                    "summary": "The Biot-Savart law gives the field of a current element and Ampere's circuital law provides a shortcut for symmetric current distributions such as long wires, solenoids and toroids.",
                    "concepts": [
                        "Straight infinite wire: B = mu0 I /(2 pi r), circular field lines given by the right-hand rule",
                        "Centre of a circular loop of N turns: B = mu0 N I /(2R)",
                        "Ampere's law: line integral of B . dl = mu0 I_enclosed",
                        "Inside a long solenoid B = mu0 n I (n = turns per unit length); a toroid confines the field inside",
                    ],
                    "examples": [
                        "A solenoid with 1000 turns/m carrying 2 A has B = 4 pi x10^-7 x 1000 x 2 = 2.5x10^-3 T inside.",
                    ],
                },
            ],
        },
        {
            "name": "Magnetism and Matter",
            "number": 5,
            "ncert_url": _pdf("leph105"),
            "description": "Bar magnets, magnetic dipoles, earth's magnetism and magnetic materials.",
            "topics": [
                {
                    "name": "Magnetic Dipoles and Earth's Magnetism",
                    "difficulty": "medium",
                    "summary": "A bar magnet behaves like a magnetic dipole, and the Earth itself acts as a giant dipole described by declination, dip and the horizontal component of its field.",
                    "concepts": [
                        "Magnetic moment m = NIA for a current loop; torque tau = m x B in a uniform field",
                        "Potential energy of a dipole U = -m . B, minimum when aligned with the field",
                        "Earth's field elements: magnetic declination, angle of dip and horizontal component B_H",
                        "Magnetic field lines form closed loops - isolated magnetic monopoles have never been observed",
                    ],
                    "examples": [
                        "At the magnetic equator the dip angle is 0 degrees, so the Earth's field is horizontal there.",
                    ],
                },
                {
                    "name": "Magnetic Properties of Materials",
                    "difficulty": "easy",
                    "summary": "Materials respond to magnetic fields as diamagnetic, paramagnetic or ferromagnetic depending on how their atomic magnetic moments align.",
                    "concepts": [
                        "Diamagnetic: weakly repelled, susceptibility slightly negative (bismuth, copper)",
                        "Paramagnetic: weakly attracted, small positive susceptibility, follows Curie's law chi = C/T",
                        "Ferromagnetic: strongly attracted, domains align, shows hysteresis and a Curie temperature",
                        "Permeability mu = mu0(1 + chi), relative permeability mu_r = 1 + chi",
                    ],
                    "examples": [
                        "Soft iron has a narrow hysteresis loop, which is why it is used for transformer cores and electromagnets.",
                    ],
                },
            ],
        },
        {
            "name": "Electromagnetic Induction",
            "number": 6,
            "ncert_url": _pdf("leph106"),
            "description": "Faraday's laws, Lenz's law, motional EMF, self and mutual inductance.",
            "topics": [
                {
                    "name": "Faraday's and Lenz's Laws",
                    "difficulty": "medium",
                    "summary": "A changing magnetic flux through a circuit induces an EMF whose direction always opposes the change that produced it, which is simply energy conservation in magnetic form.",
                    "concepts": [
                        "Magnetic flux phi = B A cos theta, measured in weber",
                        "Faraday's law: induced EMF e = -N dphi/dt",
                        "Lenz's law: the induced current opposes the change in flux (the minus sign)",
                        "Motional EMF of a rod moving in a field: e = B l v",
                    ],
                    "examples": [
                        "A 20 cm rod moving at 5 m/s perpendicular to a 0.4 T field develops e = Blv = 0.4 x 0.2 x 5 = 0.4 V.",
                    ],
                },
                {
                    "name": "Inductance and Eddy Currents",
                    "difficulty": "medium",
                    "summary": "Self-inductance opposes changes of current in a coil and mutual inductance couples two coils, while eddy currents are induced loops in bulk conductors that are useful for braking and wasteful in cores.",
                    "concepts": [
                        "Self inductance: e = -L dI/dt; solenoid L = mu0 n^2 A l",
                        "Energy stored in an inductor U = 1/2 L I^2",
                        "Mutual inductance M links two coils: e2 = -M dI1/dt",
                        "Eddy currents are minimised by laminating cores; they are used in induction furnaces and magnetic braking",
                    ],
                    "examples": [
                        "A coil of L = 0.5 H carrying 2 A stores U = 0.5 x 0.5 x 4 = 1 J of magnetic energy.",
                    ],
                    "prerequisites": ["faradays-and-lenzs-laws"],
                },
            ],
        },
        {
            "name": "Alternating Current",
            "number": 7,
            "ncert_url": _pdf("leph107"),
            "description": "AC circuits, reactance, impedance, resonance, power factor and transformers.",
            "topics": [
                {
                    "name": "AC Circuits, Reactance and Impedance",
                    "difficulty": "hard",
                    "summary": "In AC circuits inductors and capacitors offer frequency-dependent opposition called reactance, and the combined opposition with resistance is the impedance that decides current and phase.",
                    "concepts": [
                        "RMS values: I_rms = I0/sqrt(2), V_rms = V0/sqrt(2)",
                        "Inductive reactance X_L = omega L (voltage leads current by 90 degrees)",
                        "Capacitive reactance X_C = 1/(omega C) (current leads voltage by 90 degrees)",
                        "Series LCR impedance Z = sqrt(R^2 + (X_L - X_C)^2), phase tan phi = (X_L - X_C)/R",
                    ],
                    "examples": [
                        "For R = 30 ohm, X_L = 60 ohm and X_C = 20 ohm, Z = sqrt(30^2 + 40^2) = 50 ohm.",
                    ],
                },
                {
                    "name": "Resonance, Power Factor and Transformers",
                    "difficulty": "medium",
                    "summary": "A series LCR circuit resonates when inductive and capacitive reactances cancel, and real power in AC depends on the power factor; transformers change voltage levels using mutual induction.",
                    "concepts": [
                        "Resonance at omega0 = 1/sqrt(LC): Z is minimum (= R) and current is maximum",
                        "Quality factor Q = omega0 L / R measures sharpness of resonance",
                        "Average power P = V_rms I_rms cos phi, where cos phi is the power factor",
                        "Ideal transformer: V_s/V_p = N_s/N_p and V_p I_p = V_s I_s",
                    ],
                    "examples": [
                        "A step-down transformer with 1000 primary and 100 secondary turns converts 220 V to 22 V.",
                    ],
                    "prerequisites": ["ac-circuits-reactance-and-impedance"],
                },
            ],
        },
        {
            "name": "Electromagnetic Waves",
            "number": 8,
            "ncert_url": _pdf("leph108"),
            "description": "Displacement current, properties of EM waves and the electromagnetic spectrum.",
            "topics": [
                {
                    "name": "Electromagnetic Waves and the Spectrum",
                    "difficulty": "easy",
                    "summary": "Changing electric and magnetic fields sustain each other and travel as transverse electromagnetic waves at the speed of light, forming a spectrum from radio waves to gamma rays.",
                    "concepts": [
                        "Displacement current I_d = epsilon0 dphi_E/dt completes Ampere-Maxwell law",
                        "In vacuum c = 1/sqrt(mu0 epsilon0) = 3x10^8 m/s and E0/B0 = c",
                        "E, B and the direction of propagation are mutually perpendicular (transverse wave)",
                        "Spectrum order by increasing frequency: radio, microwave, infrared, visible, ultraviolet, X-ray, gamma",
                    ],
                    "examples": [
                        "Microwave ovens use ~2.45 GHz waves that resonate with water molecules to heat food.",
                    ],
                },
            ],
        },
        {
            "name": "Ray Optics and Optical Instruments",
            "number": 9,
            "ncert_url": _pdf("leph201"),
            "description": "Reflection, refraction, lenses, prisms and optical instruments.",
            "topics": [
                {
                    "name": "Reflection, Refraction and Total Internal Reflection",
                    "difficulty": "medium",
                    "summary": "Light bends when it changes medium according to Snell's law, and beyond the critical angle it is totally internally reflected - the principle behind optical fibres.",
                    "concepts": [
                        "Snell's law: n1 sin i = n2 sin r, refractive index n = c/v",
                        "Mirror formula 1/v + 1/u = 1/f, magnification m = -v/u",
                        "Critical angle: sin C = 1/n; total internal reflection needs i > C and a denser to rarer medium",
                        "Apparent depth = real depth / n explains why a pool looks shallower",
                    ],
                    "examples": [
                        "For water (n = 1.33) the critical angle is C = sin^-1(1/1.33) ~ 48.8 degrees.",
                    ],
                },
                {
                    "name": "Lenses, Lens Maker's Formula and Optical Instruments",
                    "difficulty": "medium",
                    "summary": "Thin lenses are described by the lens formula and lens maker's formula, and combinations of lenses build microscopes and telescopes with predictable magnification.",
                    "concepts": [
                        "Lens formula 1/v - 1/u = 1/f; power P = 1/f (in dioptre)",
                        "Lens maker's formula 1/f = (n-1)(1/R1 - 1/R2)",
                        "Lenses in contact: P = P1 + P2",
                        "Compound microscope M = (v0/u0)(1 + D/fe); astronomical telescope M = f0/fe",
                    ],
                    "examples": [
                        "Two thin lenses of +10 D and -4 D in contact behave as a single lens of power +6 D (f ~ 16.7 cm).",
                    ],
                    "prerequisites": ["reflection-refraction-and-total-internal-reflection"],
                },
            ],
        },
        {
            "name": "Wave Optics",
            "number": 10,
            "ncert_url": _pdf("leph202"),
            "description": "Huygens principle, interference, Young's double slit, diffraction and polarisation.",
            "topics": [
                {
                    "name": "Interference and Young's Double Slit Experiment",
                    "difficulty": "hard",
                    "summary": "Two coherent sources superpose to give bright and dark fringes whose spacing depends on wavelength, slit separation and screen distance.",
                    "concepts": [
                        "Coherent sources have a constant phase difference; only then are stable fringes seen",
                        "Constructive interference when path difference = n lambda, destructive when = (n + 1/2) lambda",
                        "Fringe width beta = lambda D / d",
                        "Intensity I = 4 I0 cos^2(phi/2) for two equal sources",
                    ],
                    "examples": [
                        "Light of 600 nm with d = 0.5 mm and D = 1 m gives beta = 600x10^-9 x 1 / 0.5x10^-3 = 1.2 mm.",
                    ],
                },
                {
                    "name": "Diffraction and Polarisation",
                    "difficulty": "medium",
                    "summary": "A single slit spreads light into a broad central maximum, and polarisation shows that light waves are transverse.",
                    "concepts": [
                        "Single slit minima at a sin theta = n lambda; central maximum width = 2 lambda D / a",
                        "Resolving power improves with larger aperture and smaller wavelength",
                        "Malus's law: I = I0 cos^2 theta for polarised light through an analyser",
                        "Brewster's law: tan i_p = n, and the reflected ray is completely plane polarised",
                    ],
                    "examples": [
                        "For n = 1.5, Brewster's angle is i_p = tan^-1(1.5) ~ 56.3 degrees.",
                    ],
                },
            ],
        },
        {
            "name": "Dual Nature of Radiation and Matter",
            "number": 11,
            "ncert_url": _pdf("leph203"),
            "description": "Photoelectric effect, Einstein's equation and de Broglie waves.",
            "topics": [
                {
                    "name": "Photoelectric Effect and Einstein's Equation",
                    "difficulty": "medium",
                    "summary": "Light ejects electrons from a metal only above a threshold frequency, which classical wave theory cannot explain but the photon picture does exactly.",
                    "concepts": [
                        "Einstein's equation: K_max = h nu - phi0, where phi0 = h nu0 is the work function",
                        "Stopping potential V0 satisfies eV0 = K_max and is independent of intensity",
                        "Photocurrent is proportional to intensity; K_max depends only on frequency",
                        "Photon energy E = h nu = hc/lambda, momentum p = h/lambda",
                    ],
                    "examples": [
                        "For a metal with work function 2 eV illuminated by 3 eV photons, K_max = 1 eV and V0 = 1 V.",
                    ],
                },
                {
                    "name": "de Broglie Waves and Matter Duality",
                    "difficulty": "medium",
                    "summary": "Every moving particle has an associated wavelength, confirmed by electron diffraction, showing matter is both particle and wave.",
                    "concepts": [
                        "de Broglie wavelength lambda = h/p = h/(mv)",
                        "For an electron accelerated through V volts: lambda = 12.27/sqrt(V) angstrom",
                        "Davisson-Germer experiment confirmed electron diffraction",
                        "Heavier and faster particles have shorter wavelengths, which is why duality is invisible in daily life",
                    ],
                    "examples": [
                        "An electron accelerated through 100 V has lambda = 12.27/10 = 1.227 angstrom, comparable to atomic spacing.",
                    ],
                },
            ],
        },
        {
            "name": "Atoms and Nuclei",
            "number": 12,
            "ncert_url": _pdf("leph204"),
            "description": "Rutherford and Bohr models, spectral series, nuclear binding energy and radioactivity.",
            "topics": [
                {
                    "name": "Bohr Model and Hydrogen Spectrum",
                    "difficulty": "medium",
                    "summary": "Bohr quantised angular momentum to explain stable orbits and the discrete line spectrum of hydrogen.",
                    "concepts": [
                        "Angular momentum quantisation mvr = n h/(2 pi)",
                        "Energy levels E_n = -13.6/n^2 eV; radius r_n = 0.53 n^2 angstrom",
                        "Emission when an electron jumps down: h nu = E_i - E_f",
                        "Series: Lyman (UV, n->1), Balmer (visible, n->2), Paschen (IR, n->3)",
                    ],
                    "examples": [
                        "The n = 3 to n = 2 transition emits 1.89 eV, the red H-alpha line at 656 nm.",
                    ],
                },
                {
                    "name": "Nuclear Binding Energy and Radioactivity",
                    "difficulty": "hard",
                    "summary": "Mass defect converts into binding energy that holds nuclei together, and unstable nuclei decay exponentially by alpha, beta or gamma emission.",
                    "concepts": [
                        "Mass defect delta m gives binding energy E = delta m c^2 (1 u = 931.5 MeV)",
                        "Binding energy per nucleon peaks near iron (~8.8 MeV), explaining fusion and fission energy release",
                        "Radioactive decay law N = N0 e^(-lambda t); half life T = 0.693/lambda",
                        "Alpha decay reduces A by 4 and Z by 2; beta decay changes Z by 1 with A unchanged",
                    ],
                    "examples": [
                        "A sample with a half life of 5 days falls to one eighth of its activity after 15 days (3 half lives).",
                    ],
                    "questions": [
                        {
                            "text": "The half life of a radioactive sample is 10 years. The fraction remaining after 30 years is",
                            "options": ["A. 1/2", "B. 1/4", "C. 1/8", "D. 1/16"],
                            "answer": "C. 1/8",
                            "explanation": "30 years is 3 half lives, so the remaining fraction is (1/2)^3 = 1/8.",
                            "difficulty": "easy",
                            "concept": "Radioactive decay",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Semiconductor Electronics",
            "number": 13,
            "ncert_url": _pdf("leph205"),
            "description": "Semiconductors, p-n junction, diodes, rectifiers and special purpose diodes.",
            "topics": [
                {
                    "name": "Semiconductors and the p-n Junction",
                    "difficulty": "medium",
                    "summary": "Doping a pure semiconductor creates n-type or p-type material, and joining them forms a p-n junction with a depletion layer that conducts in only one direction.",
                    "concepts": [
                        "Intrinsic semiconductors: n_e = n_h; doping with pentavalent atoms gives n-type, trivalent gives p-type",
                        "Depletion region and barrier potential (~0.7 V for Si, ~0.3 V for Ge)",
                        "Forward bias narrows the depletion layer and current flows; reverse bias widens it and only leakage flows",
                        "Conductivity of semiconductors increases with temperature, unlike metals",
                    ],
                    "examples": [
                        "Silicon doped with phosphorus (group 15) has extra free electrons, making it n-type.",
                    ],
                },
                {
                    "name": "Diode Applications: Rectifiers, LEDs and Zener Diodes",
                    "difficulty": "easy",
                    "summary": "The one-way behaviour of a diode is used to convert AC to DC, regulate voltage and emit light.",
                    "concepts": [
                        "Half wave rectifier uses one diode (output for half the cycle); full wave uses two diodes or a bridge",
                        "Ripple is reduced with a filter capacitor across the load",
                        "Zener diode works in reverse breakdown as a voltage regulator",
                        "LED converts electrical energy to light in forward bias; photodiode is used in reverse bias to detect light",
                    ],
                    "examples": [
                        "A bridge rectifier gives an output frequency of 100 Hz from a 50 Hz AC supply.",
                    ],
                    "prerequisites": ["semiconductors-and-the-p-n-junction"],
                },
            ],
        },
    ],
}
