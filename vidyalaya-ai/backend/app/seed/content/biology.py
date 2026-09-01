"""Class 12 Biology content pack (NCERT aligned structure)."""

NCERT_BOOK = "https://ncert.nic.in/textbook.php?lebo1=0-13"


def _pdf(code: str) -> str:
    return f"https://ncert.nic.in/textbook/pdf/{code}.pdf"


SUBJECT = {
    "code": "BIO",
    "name": "Biology",
    "icon": "🧬",
    "color": "green",
    "description": "Reproduction, genetics, evolution, human health, biotechnology and ecology for CBSE Class 12.",
    "ncert_url": NCERT_BOOK,
    "chapters": [
        {
            "name": "Sexual Reproduction in Flowering Plants",
            "number": 1,
            "ncert_url": _pdf("lebo101"),
            "description": "Flower structure, pollination, double fertilisation and seed formation.",
            "topics": [
                {
                    "name": "Pollination and Double Fertilisation",
                    "difficulty": "medium",
                    "summary": "Pollen transfer can be self or cross pollination, and flowering plants are unique in performing double fertilisation that produces both a zygote and the nutritive endosperm.",
                    "concepts": [
                        "Autogamy, geitonogamy and xenogamy are the three pollination categories",
                        "Pollen tube carries two male gametes to the embryo sac",
                        "Double fertilisation: syngamy (n + n = 2n zygote) and triple fusion (2n + n = 3n endosperm)",
                        "Outbreeding devices such as dichogamy, self incompatibility and unisexuality prevent inbreeding",
                    ],
                    "examples": [
                        "In maize the 3n endosperm is the edible part that nourishes the developing embryo.",
                    ],
                    "questions": [
                        {
                            "text": "The ploidy of the endosperm in angiosperms is",
                            "options": ["A. Haploid (n)", "B. Diploid (2n)", "C. Triploid (3n)", "D. Tetraploid (4n)"],
                            "answer": "C. Triploid (3n)",
                            "explanation": "Triple fusion of one male gamete with two polar nuclei gives the 3n primary endosperm nucleus.",
                            "difficulty": "easy",
                            "concept": "Double fertilisation",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Human Reproduction",
            "number": 2,
            "ncert_url": _pdf("lebo102"),
            "description": "Reproductive systems, gametogenesis, menstrual cycle, fertilisation and embryonic development.",
            "topics": [
                {
                    "name": "Gametogenesis and the Menstrual Cycle",
                    "difficulty": "medium",
                    "summary": "Spermatogenesis and oogenesis produce haploid gametes under hormonal control, and the menstrual cycle prepares the uterus for implantation each month.",
                    "concepts": [
                        "Spermatogenesis is continuous after puberty; oogenesis begins in fetal life and pauses in prophase I",
                        "FSH and LH from the pituitary control gamete formation and ovulation",
                        "Ovulation occurs around day 14 triggered by an LH surge",
                        "Corpus luteum secretes progesterone to maintain the endometrium",
                    ],
                    "examples": [
                        "A rise in progesterone after ovulation thickens the endometrium; its fall triggers menstruation.",
                    ],
                },
                {
                    "name": "Fertilisation, Implantation and Placenta",
                    "difficulty": "medium",
                    "summary": "Fertilisation in the ampullary-isthmic junction forms a zygote that becomes a blastocyst and implants, after which the placenta takes over exchange and hormone production.",
                    "concepts": [
                        "Fertilisation occurs at the ampullary-isthmic junction of the fallopian tube",
                        "Cleavage produces morula and then blastocyst with trophoblast and inner cell mass",
                        "Placenta exchanges nutrients, gases and wastes and secretes hCG, hPL, oestrogen and progesterone",
                        "Gestation is about 9 months; parturition is triggered by the foetal ejection reflex and oxytocin",
                    ],
                    "examples": [
                        "hCG detected in urine is the basis of the common home pregnancy test.",
                    ],
                    "prerequisites": ["gametogenesis-and-the-menstrual-cycle"],
                },
            ],
        },
        {
            "name": "Reproductive Health",
            "number": 3,
            "ncert_url": _pdf("lebo103"),
            "description": "Population control, contraception, STIs and assisted reproductive technologies.",
            "topics": [
                {
                    "name": "Contraception and Assisted Reproductive Technologies",
                    "difficulty": "easy",
                    "summary": "Contraceptive methods work at different points of the reproductive process, and ART helps couples who cannot conceive naturally.",
                    "concepts": [
                        "Contraceptive categories: barrier, IUD, hormonal, surgical (tubectomy, vasectomy)",
                        "MTP and its legal and ethical framework in India",
                        "STIs such as gonorrhoea, syphilis and HIV are largely preventable through awareness",
                        "ART techniques: IVF-ET, ZIFT, GIFT, ICSI and artificial insemination",
                    ],
                    "examples": [
                        "In IVF, fertilisation happens in the laboratory and the embryo is transferred to the uterus (commonly called test tube baby).",
                    ],
                },
            ],
        },
        {
            "name": "Principles of Inheritance and Variation",
            "number": 4,
            "ncert_url": _pdf("lebo104"),
            "description": "Mendelian genetics, deviations, linkage, sex determination and genetic disorders.",
            "topics": [
                {
                    "name": "Mendel's Laws and Deviations",
                    "difficulty": "medium",
                    "summary": "Mendel's laws of dominance, segregation and independent assortment explain most inheritance, while codominance, incomplete dominance and polygenic traits are important exceptions.",
                    "concepts": [
                        "Monohybrid cross phenotypic ratio 3:1; dihybrid 9:3:3:1",
                        "Law of segregation: alleles separate during gamete formation",
                        "Incomplete dominance (snapdragon pink) and codominance (AB blood group)",
                        "Test cross with the recessive parent reveals an unknown genotype",
                    ],
                    "examples": [
                        "Crossing a heterozygous tall pea plant (Tt) with a dwarf (tt) gives 50% tall and 50% dwarf offspring.",
                    ],
                    "questions": [
                        {
                            "text": "The phenotypic ratio of a dihybrid cross in F2 is",
                            "options": ["A. 3:1", "B. 1:2:1", "C. 9:3:3:1", "D. 1:1:1:1"],
                            "answer": "C. 9:3:3:1",
                            "explanation": "Two independently assorting gene pairs give the classic 9:3:3:1 F2 phenotypic ratio.",
                            "difficulty": "easy",
                            "concept": "Mendelian genetics",
                        },
                    ],
                },
                {
                    "name": "Sex Determination, Linkage and Genetic Disorders",
                    "difficulty": "hard",
                    "summary": "Genes on the same chromosome are linked and inherited together, sex chromosomes determine sex, and errors in genes or chromosomes cause inherited disorders.",
                    "concepts": [
                        "Human sex determination is XX (female) and XY (male); the sperm decides the sex",
                        "Linked genes show reduced recombination; recombination frequency maps gene distance",
                        "Mendelian disorders: haemophilia and colour blindness (X-linked recessive), sickle cell anaemia (autosomal recessive)",
                        "Chromosomal disorders: Down syndrome (trisomy 21), Turner (XO), Klinefelter (XXY)",
                    ],
                    "examples": [
                        "A carrier mother and a normal father can have haemophilic sons with 50% probability.",
                    ],
                    "prerequisites": ["mendels-laws-and-deviations"],
                },
            ],
        },
        {
            "name": "Molecular Basis of Inheritance",
            "number": 5,
            "ncert_url": _pdf("lebo105"),
            "description": "DNA structure, replication, transcription, genetic code, translation and regulation.",
            "topics": [
                {
                    "name": "DNA Structure and Replication",
                    "difficulty": "medium",
                    "summary": "DNA is an antiparallel double helix whose complementary strands allow semiconservative replication.",
                    "concepts": [
                        "Watson-Crick model: 2 nm width, 3.4 nm per turn, 10 base pairs per turn",
                        "A pairs with T (two H bonds), G with C (three H bonds); Chargaff's rule A=T, G=C",
                        "Replication is semiconservative (Meselson and Stahl experiment)",
                        "DNA polymerase works 5' to 3', giving a continuous leading and discontinuous lagging strand",
                    ],
                    "examples": [
                        "In Meselson and Stahl's experiment, 15N labelled DNA gave a hybrid band after one generation in 14N medium.",
                    ],
                },
                {
                    "name": "Transcription, Genetic Code and Translation",
                    "difficulty": "hard",
                    "summary": "Genetic information flows from DNA to RNA to protein, with a triplet code read by ribosomes and tRNA adaptors.",
                    "concepts": [
                        "Central dogma: DNA -> RNA -> protein (with reverse transcription in retroviruses)",
                        "Genetic code is triplet, degenerate, non-overlapping and universal; AUG is the start codon",
                        "Stop codons UAA, UAG and UGA terminate translation",
                        "Lac operon is an example of negative regulation of transcription in prokaryotes",
                    ],
                    "examples": [
                        "In the lac operon, lactose acts as an inducer that inactivates the repressor and switches on transcription.",
                    ],
                    "prerequisites": ["dna-structure-and-replication"],
                },
            ],
        },
        {
            "name": "Evolution",
            "number": 6,
            "ncert_url": _pdf("lebo106"),
            "description": "Origin of life, evidence for evolution, Darwinism, Hardy-Weinberg and human evolution.",
            "topics": [
                {
                    "name": "Evidence, Mechanisms and Hardy-Weinberg Principle",
                    "difficulty": "medium",
                    "summary": "Fossils, homology and molecular data support evolution by natural selection, and the Hardy-Weinberg equation describes when allele frequencies stay constant.",
                    "concepts": [
                        "Homologous organs show divergent evolution; analogous organs show convergent evolution",
                        "Natural selection types: stabilising, directional and disruptive",
                        "Hardy-Weinberg: p^2 + 2pq + q^2 = 1, disturbed by mutation, migration, drift, selection and non-random mating",
                        "Founder effect and genetic drift matter most in small populations",
                    ],
                    "examples": [
                        "Industrial melanism in peppered moths is a documented case of directional natural selection.",
                    ],
                },
            ],
        },
        {
            "name": "Human Health and Disease",
            "number": 7,
            "ncert_url": _pdf("lebo107"),
            "description": "Pathogens, immunity, AIDS, cancer and drug abuse.",
            "topics": [
                {
                    "name": "Immunity and Common Human Diseases",
                    "difficulty": "medium",
                    "summary": "Innate and acquired immunity defend the body, and knowing the causative agent of common diseases guides prevention.",
                    "concepts": [
                        "Innate immunity is non-specific; acquired immunity is specific with memory (B and T lymphocytes)",
                        "Active immunity develops after infection or vaccination; passive immunity is transferred antibodies",
                        "Malaria (Plasmodium), typhoid (Salmonella typhi), amoebiasis (Entamoeba), ascariasis (Ascaris)",
                        "HIV attacks helper T cells; cancer arises from uncontrolled division and loss of contact inhibition",
                    ],
                    "examples": [
                        "Colostrum is rich in IgA antibodies and gives the newborn passive immunity.",
                    ],
                },
            ],
        },
        {
            "name": "Microbes in Human Welfare",
            "number": 8,
            "ncert_url": _pdf("lebo108"),
            "description": "Microbes in food, industry, sewage treatment, biogas and biocontrol.",
            "topics": [
                {
                    "name": "Useful Microbes in Industry and Agriculture",
                    "difficulty": "easy",
                    "summary": "Microorganisms are used to make food, antibiotics and biogas, to treat sewage and to control pests biologically.",
                    "concepts": [
                        "Lactobacillus curdles milk; Saccharomyces cerevisiae ferments dough and alcohol",
                        "Penicillium notatum gives penicillin; Streptococcus gives streptokinase; Monascus purpureus gives statins",
                        "Sewage treatment: primary (physical) then secondary (biological) with activated sludge and flocs",
                        "Biofertilisers (Rhizobium, mycorrhiza, Azospirillum) and biocontrol (Bacillus thuringiensis, Trichoderma)",
                    ],
                    "examples": [
                        "Methanogens in an anaerobic sludge digester produce biogas that is about 50-70 percent methane.",
                    ],
                },
            ],
        },
        {
            "name": "Biotechnology: Principles and Processes",
            "number": 9,
            "ncert_url": _pdf("lebo109"),
            "description": "Restriction enzymes, vectors, PCR, gel electrophoresis and bioreactors.",
            "topics": [
                {
                    "name": "Tools and Steps of Recombinant DNA Technology",
                    "difficulty": "hard",
                    "summary": "Recombinant DNA technology cuts DNA with restriction enzymes, joins it into a vector with ligase, transfers it into a host and amplifies the product.",
                    "concepts": [
                        "Restriction endonucleases cut at palindromic sites producing sticky ends",
                        "Cloning vector needs an origin of replication, selectable marker and recognition sites",
                        "PCR steps: denaturation, annealing, extension using thermostable Taq polymerase",
                        "Gel electrophoresis separates DNA fragments by size; smaller fragments travel farther",
                    ],
                    "examples": [
                        "EcoRI cuts GAATTC between G and A on both strands, leaving complementary sticky ends.",
                    ],
                },
            ],
        },
        {
            "name": "Biotechnology and its Applications",
            "number": 10,
            "ncert_url": _pdf("lebo110"),
            "description": "Bt crops, RNA interference, gene therapy, molecular diagnosis and biopiracy.",
            "topics": [
                {
                    "name": "Applications in Agriculture and Medicine",
                    "difficulty": "medium",
                    "summary": "Genetic engineering gives pest resistant crops, human insulin, gene therapy and sensitive molecular diagnostics.",
                    "concepts": [
                        "Bt cotton carries cry genes whose toxin activates in the alkaline insect gut",
                        "RNAi silences a target mRNA and protects plants from nematodes",
                        "Humulin is human insulin produced in E. coli with the A and B chains joined by disulphide bonds",
                        "ADA deficiency was the first disorder treated by gene therapy",
                    ],
                    "examples": [
                        "PCR and ELISA detect infections much earlier than symptom-based diagnosis.",
                    ],
                    "prerequisites": ["tools-and-steps-of-recombinant-dna-technology"],
                },
            ],
        },
        {
            "name": "Organisms and Populations",
            "number": 11,
            "ncert_url": _pdf("lebo111"),
            "description": "Adaptations, population attributes, growth models and interactions.",
            "topics": [
                {
                    "name": "Population Growth and Interactions",
                    "difficulty": "medium",
                    "summary": "Populations grow exponentially when resources are unlimited and logistically when they are limited, while species interact as competitors, predators, parasites or mutualists.",
                    "concepts": [
                        "Exponential growth dN/dt = rN gives a J-shaped curve",
                        "Logistic growth dN/dt = rN(K-N)/K gives an S-shaped curve, K being carrying capacity",
                        "Interactions: mutualism (+,+), competition (-,-), predation and parasitism (+,-), commensalism (+,0)",
                        "Gause's competitive exclusion principle and resource partitioning",
                    ],
                    "examples": [
                        "The fig and fig wasp relationship is a classic obligate mutualism.",
                    ],
                },
            ],
        },
        {
            "name": "Ecosystem",
            "number": 12,
            "ncert_url": _pdf("lebo112"),
            "description": "Productivity, decomposition, energy flow, ecological pyramids and nutrient cycling.",
            "topics": [
                {
                    "name": "Energy Flow and Ecological Pyramids",
                    "difficulty": "medium",
                    "summary": "Energy enters an ecosystem through producers and moves up trophic levels with heavy losses, which is why food chains are short.",
                    "concepts": [
                        "10 percent law: only about 10 percent of energy passes to the next trophic level",
                        "GPP minus respiration equals NPP",
                        "Pyramids of number, biomass and energy; the energy pyramid is always upright",
                        "Decomposition steps: fragmentation, leaching, catabolism, humification and mineralisation",
                    ],
                    "examples": [
                        "An inverted biomass pyramid is seen in a pond where small phytoplankton support larger zooplankton biomass.",
                    ],
                },
            ],
        },
        {
            "name": "Biodiversity and Conservation",
            "number": 13,
            "ncert_url": _pdf("lebo113"),
            "description": "Patterns of biodiversity, causes of loss and conservation strategies.",
            "topics": [
                {
                    "name": "Biodiversity Patterns and Conservation",
                    "difficulty": "easy",
                    "summary": "Biodiversity is highest in the tropics and is threatened by habitat loss, invasive species, over-exploitation and co-extinction; conservation may be in situ or ex situ.",
                    "concepts": [
                        "Species-area relationship: log S = log C + Z log A",
                        "The Evil Quartet: habitat loss and fragmentation, over-exploitation, alien species invasion, co-extinction",
                        "In situ: biosphere reserves, national parks, sanctuaries, sacred groves",
                        "Ex situ: zoos, botanical gardens, seed banks, cryopreservation",
                    ],
                    "examples": [
                        "The Western Ghats is one of the biodiversity hotspots recognised in India.",
                    ],
                },
            ],
        },
    ],
}
