"""Class 12 Chemistry content pack (NCERT aligned structure)."""

NCERT_BOOK_1 = "https://ncert.nic.in/textbook.php?lech1=0-5"
NCERT_BOOK_2 = "https://ncert.nic.in/textbook.php?lech2=0-5"


def _pdf(code: str) -> str:
    return f"https://ncert.nic.in/textbook/pdf/{code}.pdf"


SUBJECT = {
    "code": "CHEM",
    "name": "Chemistry",
    "icon": "⚗️",
    "color": "emerald",
    "description": "Physical, inorganic and organic chemistry for CBSE Class 12 - solutions, electrochemistry, kinetics, coordination compounds and organic families.",
    "ncert_url": NCERT_BOOK_1,
    "chapters": [
        {
            "name": "Solutions",
            "number": 1,
            "ncert_url": _pdf("lech101"),
            "description": "Concentration terms, Raoult's law, colligative properties and abnormal molar mass.",
            "topics": [
                {
                    "name": "Concentration Terms and Raoult's Law",
                    "difficulty": "medium",
                    "summary": "Solution strength is expressed by molarity, molality and mole fraction, and Raoult's law relates vapour pressure to the mole fraction of each component.",
                    "concepts": [
                        "Molarity M = moles of solute per litre of solution (temperature dependent)",
                        "Molality m = moles of solute per kg of solvent (temperature independent)",
                        "Raoult's law for volatile components: p_total = p1 x1 + p2 x2",
                        "Positive deviation: weaker A-B interactions (ethanol + acetone); negative deviation: stronger (chloroform + acetone)",
                    ],
                    "examples": [
                        "A solution with 0.5 mol solute in 500 g water has molality m = 0.5/0.5 = 1 mol/kg.",
                    ],
                },
                {
                    "name": "Colligative Properties",
                    "difficulty": "hard",
                    "summary": "Adding a non-volatile solute lowers vapour pressure, elevates boiling point, depresses freezing point and creates osmotic pressure - all depending on the number of particles, not their nature.",
                    "concepts": [
                        "Relative lowering of vapour pressure = mole fraction of solute",
                        "Elevation in boiling point delta Tb = Kb m; depression in freezing point delta Tf = Kf m",
                        "Osmotic pressure pi = CRT, the most sensitive colligative property",
                        "Van't Hoff factor i accounts for association or dissociation of solute",
                    ],
                    "examples": [
                        "NaCl in water gives i ~ 2, so it depresses the freezing point about twice as much as glucose at the same molality.",
                    ],
                    "prerequisites": ["concentration-terms-and-raoults-law"],
                    "questions": [
                        {
                            "text": "Which of these is NOT a colligative property?",
                            "options": ["A. Osmotic pressure", "B. Elevation of boiling point", "C. Optical activity", "D. Depression of freezing point"],
                            "answer": "C. Optical activity",
                            "explanation": "Colligative properties depend only on the number of solute particles; optical activity depends on molecular structure.",
                            "difficulty": "easy",
                            "concept": "Colligative properties",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Electrochemistry",
            "number": 2,
            "ncert_url": _pdf("lech102"),
            "description": "Galvanic cells, electrode potential, Nernst equation, conductance and electrolysis.",
            "topics": [
                {
                    "name": "Galvanic Cells and the Nernst Equation",
                    "difficulty": "hard",
                    "summary": "A galvanic cell converts chemical energy to electrical energy; the Nernst equation corrects the standard cell potential for non-standard concentrations.",
                    "concepts": [
                        "Cell notation: anode (oxidation) on the left, cathode (reduction) on the right",
                        "E_cell = E_cathode - E_anode (both as reduction potentials)",
                        "Nernst: E = E0 - (0.0591/n) log Q at 298 K",
                        "delta G = -nFE_cell; a positive E_cell means a spontaneous reaction",
                    ],
                    "examples": [
                        "For the Daniell cell Zn|Zn2+||Cu2+|Cu, E0_cell = 0.34 - (-0.76) = 1.10 V.",
                    ],
                    "questions": [
                        {
                            "text": "In a galvanic cell, oxidation takes place at the",
                            "options": ["A. Cathode", "B. Anode", "C. Salt bridge", "D. Both electrodes"],
                            "answer": "B. Anode",
                            "explanation": "By definition oxidation occurs at the anode, which is the negative terminal in a galvanic cell.",
                            "difficulty": "easy",
                            "concept": "Galvanic cells",
                        },
                    ],
                },
                {
                    "name": "Conductance and Electrolysis",
                    "difficulty": "medium",
                    "summary": "Electrolytic conductance depends on ion concentration and mobility, and Faraday's laws quantify how much substance is deposited during electrolysis.",
                    "concepts": [
                        "Conductivity kappa = G x cell constant; molar conductivity Lm = kappa x 1000/C",
                        "Lm increases on dilution; strong electrolytes follow Lm = Lm0 - A sqrt(C)",
                        "Kohlrausch's law: Lm0 = v+ lambda+ + v- lambda-",
                        "Faraday's first law: mass deposited w = Z I t, with 1 F = 96500 C",
                    ],
                    "examples": [
                        "Passing 1 F through molten AlCl3 deposits 27/3 = 9 g of aluminium.",
                    ],
                },
            ],
        },
        {
            "name": "Chemical Kinetics",
            "number": 3,
            "ncert_url": _pdf("lech103"),
            "description": "Rate of reaction, rate laws, order, integrated rate equations and Arrhenius equation.",
            "topics": [
                {
                    "name": "Rate Laws, Order and Molecularity",
                    "difficulty": "medium",
                    "summary": "The rate law is found experimentally and defines the order of a reaction, which is different from molecularity.",
                    "concepts": [
                        "Rate = k[A]^x[B]^y; overall order = x + y",
                        "Order can be zero or fractional; molecularity is always a positive integer for an elementary step",
                        "Units of k: zero order mol L^-1 s^-1, first order s^-1, second order L mol^-1 s^-1",
                        "The rate determining step is the slowest step of the mechanism",
                    ],
                    "examples": [
                        "If doubling [A] doubles the rate while [B] has no effect, the reaction is first order in A and zero order in B.",
                    ],
                },
                {
                    "name": "Integrated Rate Equations and Arrhenius Equation",
                    "difficulty": "hard",
                    "summary": "Integrated rate laws give concentration as a function of time, and the Arrhenius equation explains the strong temperature dependence of rate constants.",
                    "concepts": [
                        "First order: k = (2.303/t) log([A0]/[A]); half life t1/2 = 0.693/k, independent of concentration",
                        "Zero order: [A] = [A0] - kt with t1/2 = [A0]/2k",
                        "Arrhenius: k = A e^(-Ea/RT); log(k2/k1) = Ea(T2-T1)/(2.303 R T1 T2)",
                        "A catalyst lowers Ea and speeds up both forward and backward reactions equally",
                    ],
                    "examples": [
                        "A first order reaction with k = 0.0693 min^-1 has a half life of 0.693/0.0693 = 10 minutes.",
                    ],
                    "prerequisites": ["rate-laws-order-and-molecularity"],
                    "questions": [
                        {
                            "text": "The half life of a first order reaction",
                            "options": [
                                "A. Depends on the initial concentration",
                                "B. Is independent of the initial concentration",
                                "C. Doubles when concentration doubles",
                                "D. Is always 0.693 seconds",
                            ],
                            "answer": "B. Is independent of the initial concentration",
                            "explanation": "For first order kinetics t1/2 = 0.693/k, which contains no concentration term.",
                            "difficulty": "medium",
                            "concept": "First order kinetics",
                        },
                    ],
                },
            ],
        },
        {
            "name": "The d- and f-Block Elements",
            "number": 4,
            "ncert_url": _pdf("lech104"),
            "description": "Transition and inner transition elements, oxidation states, colour, magnetism and catalysis.",
            "topics": [
                {
                    "name": "Transition Elements: Trends and Properties",
                    "difficulty": "medium",
                    "summary": "Partly filled d orbitals give transition metals variable oxidation states, coloured ions, magnetic behaviour and catalytic activity.",
                    "concepts": [
                        "Variable oxidation states arise from similar energies of (n-1)d and ns electrons",
                        "Colour is due to d-d transitions; ions with d0 or d10 configurations are colourless",
                        "Magnetic moment mu = sqrt(n(n+2)) BM where n is the number of unpaired electrons",
                        "Lanthanoid contraction makes the 4d and 5d elements similar in size",
                    ],
                    "examples": [
                        "Zn2+ (d10) is colourless while Cu2+ (d9) is blue in aqueous solution.",
                    ],
                },
            ],
        },
        {
            "name": "Coordination Compounds",
            "number": 5,
            "ncert_url": _pdf("lech105"),
            "description": "Werner's theory, nomenclature, isomerism, VBT and crystal field theory.",
            "topics": [
                {
                    "name": "Coordination Compounds, Nomenclature and Isomerism",
                    "difficulty": "hard",
                    "summary": "A complex has a central metal ion surrounded by ligands in the coordination sphere, and IUPAC rules name it while isomerism explains different arrangements of the same formula.",
                    "concepts": [
                        "Coordination number = number of donor atoms bonded to the metal",
                        "Ligands: monodentate (NH3, Cl-), bidentate (en, C2O4^2-), ambidentate (NO2-, SCN-)",
                        "Structural isomerism: ionisation, linkage, coordination and hydrate isomerism",
                        "Stereoisomerism: geometrical (cis/trans) and optical isomers",
                    ],
                    "examples": [
                        "[Co(NH3)5Cl]SO4 and [Co(NH3)5SO4]Cl are ionisation isomers with different precipitation tests.",
                    ],
                },
                {
                    "name": "Crystal Field Theory and Magnetic Behaviour",
                    "difficulty": "hard",
                    "summary": "Ligands split the d orbitals into two energy sets; the size of the split decides colour and whether the complex is high spin or low spin.",
                    "concepts": [
                        "In an octahedral field d orbitals split into t2g (lower) and eg (higher) by delta_o",
                        "Strong field ligands (CN-, CO) give low spin; weak field ligands (I-, Br-, F-) give high spin",
                        "Spectrochemical series: I- < Br- < Cl- < F- < H2O < NH3 < en < CN- < CO",
                        "Colour arises from electronic transitions across delta_o and complements the absorbed wavelength",
                    ],
                    "examples": [
                        "[Fe(CN)6]^4- is low spin and diamagnetic while [Fe(H2O)6]^2+ is high spin and paramagnetic.",
                    ],
                    "prerequisites": ["coordination-compounds-nomenclature-and-isomerism"],
                },
            ],
        },
        {
            "name": "Haloalkanes and Haloarenes",
            "number": 6,
            "ncert_url": _pdf("lech201"),
            "description": "Nomenclature, preparation, SN1 and SN2 mechanisms and reactions.",
            "topics": [
                {
                    "name": "Nucleophilic Substitution: SN1 and SN2",
                    "difficulty": "hard",
                    "summary": "Haloalkanes react with nucleophiles either in one concerted step (SN2) or through a carbocation intermediate (SN1), and the substrate structure decides which dominates.",
                    "concepts": [
                        "SN2: one step, backside attack, inversion of configuration, favoured by primary halides",
                        "SN1: two steps via a carbocation, racemisation, favoured by tertiary halides and polar protic solvents",
                        "Reactivity order for SN1: 3 degree > 2 degree > 1 degree; the reverse holds for SN2",
                        "Haloarenes are much less reactive because of resonance and the partial double bond character of C-X",
                    ],
                    "examples": [
                        "CH3Br + OH- gives CH3OH by an SN2 path with complete inversion at the carbon centre.",
                    ],
                },
            ],
        },
        {
            "name": "Alcohols, Phenols and Ethers",
            "number": 7,
            "ncert_url": _pdf("lech202"),
            "description": "Preparation, properties and reactions of alcohols, phenols and ethers.",
            "topics": [
                {
                    "name": "Alcohols and Phenols: Properties and Reactions",
                    "difficulty": "medium",
                    "summary": "Hydrogen bonding gives alcohols high boiling points, and phenols are more acidic than alcohols because the phenoxide ion is resonance stabilised.",
                    "concepts": [
                        "Acidity: phenol > water > alcohol; electron withdrawing groups increase phenol acidity",
                        "Dehydration of alcohols with conc. H2SO4 gives alkenes (order 3 degree > 2 degree > 1 degree)",
                        "Oxidation: primary alcohol -> aldehyde -> carboxylic acid; secondary -> ketone; tertiary resists",
                        "Reimer-Tiemann reaction converts phenol to salicylaldehyde with CHCl3/NaOH",
                    ],
                    "examples": [
                        "Ethanol boils at 78 degrees C while ethane boils at -89 degrees C, because of hydrogen bonding.",
                    ],
                },
            ],
        },
        {
            "name": "Aldehydes, Ketones and Carboxylic Acids",
            "number": 8,
            "ncert_url": _pdf("lech203"),
            "description": "Carbonyl chemistry, nucleophilic addition and acidity of carboxylic acids.",
            "topics": [
                {
                    "name": "Carbonyl Compounds and Nucleophilic Addition",
                    "difficulty": "hard",
                    "summary": "The polar C=O group undergoes nucleophilic addition, with aldehydes more reactive than ketones for both electronic and steric reasons.",
                    "concepts": [
                        "Reactivity: HCHO > RCHO > RCOR' because of +I effect and steric hindrance",
                        "Aldol condensation requires alpha hydrogens; Cannizzaro reaction occurs without them",
                        "Tollens' and Fehling's tests distinguish aldehydes from ketones",
                        "Carboxylic acids are more acidic than phenols; electron withdrawing groups increase acidity",
                    ],
                    "examples": [
                        "Acetaldehyde gives a silver mirror with Tollens' reagent, but acetone does not.",
                    ],
                },
            ],
        },
        {
            "name": "Amines",
            "number": 9,
            "ncert_url": _pdf("lech204"),
            "description": "Classification, basicity, preparation and diazonium salts.",
            "topics": [
                {
                    "name": "Amines: Basicity and Reactions",
                    "difficulty": "medium",
                    "summary": "Amines are basic because of the lone pair on nitrogen, and their strength in water is a balance of inductive, steric and solvation effects.",
                    "concepts": [
                        "Basicity in aqueous phase: 2 degree > 1 degree > 3 degree > NH3 for aliphatic amines",
                        "Aromatic amines are weaker bases because the lone pair is delocalised into the ring",
                        "Hinsberg's reagent distinguishes primary, secondary and tertiary amines",
                        "Diazotisation of aniline at 273-278 K gives benzenediazonium chloride used in coupling reactions",
                    ],
                    "examples": [
                        "Aniline is far less basic than ethylamine because its lone pair takes part in ring resonance.",
                    ],
                },
            ],
        },
        {
            "name": "Biomolecules",
            "number": 10,
            "ncert_url": _pdf("lech205"),
            "description": "Carbohydrates, proteins, enzymes, vitamins and nucleic acids.",
            "topics": [
                {
                    "name": "Carbohydrates, Proteins and Nucleic Acids",
                    "difficulty": "easy",
                    "summary": "Biomolecules are large polymers built from simple units - sugars, amino acids and nucleotides - whose structure determines their biological function.",
                    "concepts": [
                        "Monosaccharides (glucose, fructose) cannot be hydrolysed further; sucrose is a disaccharide",
                        "Amino acids exist as zwitterions; peptide bonds link them into proteins",
                        "Protein structure: primary, secondary (alpha helix, beta sheet), tertiary and quaternary",
                        "DNA is a double helix of A-T and G-C pairs; RNA is single stranded with uracil instead of thymine",
                    ],
                    "examples": [
                        "Denaturation (as in boiling an egg) destroys secondary and tertiary structure while primary structure survives.",
                    ],
                },
            ],
        },
    ],
}
