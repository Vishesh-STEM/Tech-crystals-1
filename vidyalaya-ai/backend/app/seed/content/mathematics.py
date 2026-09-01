"""Class 12 Mathematics content pack (NCERT aligned structure)."""

NCERT_BOOK_1 = "https://ncert.nic.in/textbook.php?lemh1=0-6"
NCERT_BOOK_2 = "https://ncert.nic.in/textbook.php?lemh2=0-7"


def _pdf(code: str) -> str:
    return f"https://ncert.nic.in/textbook/pdf/{code}.pdf"


SUBJECT = {
    "code": "MATH",
    "name": "Mathematics",
    "icon": "📐",
    "color": "blue",
    "description": "Relations, calculus, algebra, vectors, 3D geometry, linear programming and probability for CBSE Class 12.",
    "ncert_url": NCERT_BOOK_1,
    "chapters": [
        {
            "name": "Relations and Functions",
            "number": 1,
            "ncert_url": _pdf("lemh101"),
            "description": "Types of relations and functions, composition and invertibility.",
            "topics": [
                {
                    "name": "Types of Relations",
                    "difficulty": "easy",
                    "summary": "A relation on a set can be reflexive, symmetric or transitive; when it is all three it is an equivalence relation and it partitions the set into equivalence classes.",
                    "concepts": [
                        "Reflexive: (a,a) belongs to R for every a in A",
                        "Symmetric: (a,b) in R implies (b,a) in R",
                        "Transitive: (a,b) and (b,c) in R implies (a,c) in R",
                        "Equivalence relation = reflexive + symmetric + transitive, and it splits the set into disjoint classes",
                    ],
                    "examples": [
                        "R = {(a,b) : a - b is divisible by 3} on integers is an equivalence relation with 3 classes.",
                    ],
                },
                {
                    "name": "Types of Functions and Composition",
                    "difficulty": "medium",
                    "summary": "Functions are classified as one-one (injective), onto (surjective) or bijective, and only bijective functions have inverses.",
                    "concepts": [
                        "One-one: f(x1) = f(x2) implies x1 = x2",
                        "Onto: every element of the codomain has a pre-image",
                        "Bijective = one-one and onto, hence invertible",
                        "Composition (gof)(x) = g(f(x)); (fof^-1)(x) = x for an invertible f",
                    ],
                    "examples": [
                        "f(x) = 2x + 3 from R to R is bijective, with f^-1(y) = (y-3)/2.",
                    ],
                },
            ],
        },
        {
            "name": "Inverse Trigonometric Functions",
            "number": 2,
            "ncert_url": _pdf("lemh102"),
            "description": "Principal value branches, domains, ranges and identities.",
            "topics": [
                {
                    "name": "Principal Values and Domains",
                    "difficulty": "medium",
                    "summary": "Trigonometric functions become invertible when restricted to principal branches, which fixes the range of each inverse function.",
                    "concepts": [
                        "sin^-1 x: domain [-1,1], range [-pi/2, pi/2]",
                        "cos^-1 x: domain [-1,1], range [0, pi]",
                        "tan^-1 x: domain R, range (-pi/2, pi/2)",
                        "sin^-1 x + cos^-1 x = pi/2 and tan^-1 x + cot^-1 x = pi/2 for valid x",
                    ],
                    "examples": [
                        "sin^-1(-1/2) = -pi/6 because the principal branch lies in [-pi/2, pi/2].",
                    ],
                    "questions": [
                        {
                            "text": "The principal value of cos^-1(-1/2) is",
                            "options": ["A. pi/3", "B. 2pi/3", "C. -pi/3", "D. 4pi/3"],
                            "answer": "B. 2pi/3",
                            "explanation": "cos^-1 has range [0, pi], and cos(2pi/3) = -1/2.",
                            "difficulty": "easy",
                            "concept": "Principal values",
                        },
                    ],
                },
            ],
        },
        {
            "name": "Matrices",
            "number": 3,
            "ncert_url": _pdf("lemh103"),
            "description": "Matrix algebra, transpose, symmetric and skew-symmetric matrices, inverse by elementary operations.",
            "topics": [
                {
                    "name": "Matrix Operations and Types",
                    "difficulty": "easy",
                    "summary": "Matrices are added element-wise and multiplied row-by-column; the order of multiplication matters and many special types (diagonal, identity, symmetric) simplify calculations.",
                    "concepts": [
                        "Multiplication AB is defined only when columns of A equal rows of B, and AB is generally not equal to BA",
                        "A' (transpose): (AB)' = B'A'",
                        "Symmetric: A' = A. Skew-symmetric: A' = -A with zero diagonal",
                        "Every square matrix = symmetric part (A + A')/2 + skew part (A - A')/2",
                    ],
                    "examples": [
                        "For A of order 2x3 and B of order 3x4, AB has order 2x4 while BA is not defined.",
                    ],
                    "questions": [
                        {
                            "text": "If A is a 3x3 skew-symmetric matrix, then the diagonal elements of A are",
                            "options": ["A. All equal to 1", "B. All zero", "C. All negative", "D. Cannot be determined"],
                            "answer": "B. All zero",
                            "explanation": "For a skew-symmetric matrix a_ii = -a_ii, hence a_ii = 0.",
                            "difficulty": "easy",
                            "concept": "Symmetric and skew-symmetric matrices",
                        },
                        {
                            "text": "If A is of order 2x3 and B is of order 3x5, then the order of AB is",
                            "options": ["A. 2x5", "B. 5x2", "C. 3x3", "D. Not defined"],
                            "answer": "A. 2x5",
                            "explanation": "The product takes the rows of A and the columns of B, giving order 2x5.",
                            "difficulty": "easy",
                            "concept": "Matrix multiplication",
                        },
                        {
                            "text": "For matrices A and B, (AB)' equals",
                            "options": ["A. A'B'", "B. B'A'", "C. AB", "D. BA"],
                            "answer": "B. B'A'",
                            "explanation": "The transpose of a product reverses the order of the factors.",
                            "difficulty": "medium",
                            "concept": "Transpose",
                        },
                    ],
                },
                {
                    "name": "Inverse of a Matrix by Elementary Operations",
                    "difficulty": "medium",
                    "summary": "Row (or column) operations applied to [A | I] convert it to [I | A^-1], provided A is non-singular.",
                    "concepts": [
                        "Elementary row operations: swap rows, scale a row, add a multiple of one row to another",
                        "A is invertible if and only if |A| is not zero",
                        "(AB)^-1 = B^-1 A^-1 and (A^-1)^-1 = A",
                        "The inverse of a matrix, when it exists, is unique",
                    ],
                    "examples": [
                        "Applying row operations to [[2,1],[1,1] | I] gives the inverse [[1,-1],[-1,2]].",
                    ],
                    "prerequisites": ["matrix-operations-and-types"],
                },
            ],
        },
        {
            "name": "Determinants",
            "number": 4,
            "ncert_url": _pdf("lemh104"),
            "description": "Properties of determinants, minors and cofactors, adjoint, inverse and solving linear systems.",
            "topics": [
                {
                    "name": "Properties of Determinants",
                    "difficulty": "medium",
                    "summary": "Determinant properties turn long expansions into quick simplifications: swapping rows changes sign, identical rows give zero, and common factors can be taken out.",
                    "concepts": [
                        "|A'| = |A| and |kA| = k^n |A| for an n x n matrix",
                        "Swapping two rows changes the sign of the determinant",
                        "If two rows or columns are identical or proportional, the determinant is zero",
                        "|AB| = |A||B|",
                    ],
                    "examples": [
                        "Area of a triangle with vertices (x1,y1), (x2,y2), (x3,y3) is 1/2 |determinant of [[x1,y1,1],[x2,y2,1],[x3,y3,1]]|.",
                    ],
                },
                {
                    "name": "Adjoint, Inverse and System of Equations",
                    "difficulty": "hard",
                    "summary": "The adjoint gives a formula for the inverse, and matrix inversion solves a consistent system of linear equations in one step.",
                    "concepts": [
                        "A^-1 = adj(A)/|A| when |A| is not 0; A adj(A) = |A| I",
                        "|adj A| = |A|^(n-1) for an n x n matrix",
                        "AX = B has the unique solution X = A^-1 B when |A| is not 0",
                        "If |A| = 0 the system is either inconsistent or has infinitely many solutions",
                    ],
                    "examples": [
                        "For 2x + 3y = 8 and x - y = -1, writing AX = B and X = A^-1 B gives x = 1, y = 2.",
                    ],
                    "prerequisites": ["properties-of-determinants"],
                },
            ],
        },
        {
            "name": "Continuity and Differentiability",
            "number": 5,
            "ncert_url": _pdf("lemh105"),
            "description": "Continuity, differentiability, chain rule, implicit and logarithmic differentiation, MVT.",
            "topics": [
                {
                    "name": "Continuity and Differentiability of Functions",
                    "difficulty": "medium",
                    "summary": "A function is continuous where its limit equals its value, and differentiable where the left and right derivatives agree; differentiability always implies continuity but not the converse.",
                    "concepts": [
                        "Continuity at x = a: lim(x->a) f(x) = f(a) with both one-sided limits equal",
                        "Differentiability requires LHD = RHD at the point",
                        "|x| is continuous everywhere but not differentiable at x = 0",
                        "Sums, products and quotients (non-zero denominator) of continuous functions are continuous",
                    ],
                    "examples": [
                        "f(x) = x^2 sin(1/x) for x != 0 and f(0) = 0 is continuous and differentiable at 0.",
                    ],
                },
                {
                    "name": "Chain Rule, Implicit and Logarithmic Differentiation",
                    "difficulty": "hard",
                    "summary": "The chain rule differentiates compositions, implicit differentiation handles equations not solved for y, and taking logarithms simplifies powers and products.",
                    "concepts": [
                        "Chain rule: dy/dx = dy/du x du/dx",
                        "Implicit: differentiate both sides with respect to x and solve for dy/dx",
                        "Logarithmic differentiation is used for y = f(x)^g(x)",
                        "Parametric form: dy/dx = (dy/dt)/(dx/dt)",
                    ],
                    "examples": [
                        "For y = x^x, ln y = x ln x gives dy/dx = x^x (1 + ln x).",
                    ],
                    "prerequisites": ["continuity-and-differentiability-of-functions"],
                },
            ],
        },
        {
            "name": "Application of Derivatives",
            "number": 6,
            "ncert_url": _pdf("lemh106"),
            "description": "Rate of change, increasing/decreasing functions, tangents, normals, maxima and minima.",
            "topics": [
                {
                    "name": "Increasing, Decreasing Functions and Tangents",
                    "difficulty": "medium",
                    "summary": "The sign of the first derivative tells whether a function rises or falls, and its value gives the slope of the tangent at a point.",
                    "concepts": [
                        "f'(x) > 0 on an interval means f is increasing there; f'(x) < 0 means decreasing",
                        "Slope of tangent at (x0,y0) is f'(x0); the normal has slope -1/f'(x0)",
                        "Rate of change: dy/dt = (dy/dx)(dx/dt)",
                        "Critical points occur where f'(x) = 0 or f'(x) does not exist",
                    ],
                    "examples": [
                        "f(x) = x^3 - 3x is decreasing on (-1, 1) because f'(x) = 3x^2 - 3 < 0 there.",
                    ],
                },
                {
                    "name": "Maxima and Minima",
                    "difficulty": "hard",
                    "summary": "Local extrema are found using the first or second derivative test, and word problems are solved by writing the quantity to optimise as a function of one variable.",
                    "concepts": [
                        "First derivative test: sign change of f' from + to - gives a local maximum",
                        "Second derivative test: f'(c) = 0 with f''(c) < 0 gives a maximum, f''(c) > 0 a minimum",
                        "Absolute extrema on [a,b] are found among critical points and endpoints",
                        "In optimisation problems, reduce to one variable using the given constraint",
                    ],
                    "examples": [
                        "The rectangle of largest area with perimeter 20 m is a 5 m square of area 25 m^2.",
                    ],
                    "prerequisites": ["increasing-decreasing-functions-and-tangents"],
                },
            ],
        },
        {
            "name": "Integrals",
            "number": 7,
            "ncert_url": _pdf("lemh201"),
            "description": "Indefinite integrals, substitution, partial fractions, by parts and definite integrals.",
            "topics": [
                {
                    "name": "Indefinite Integrals and Substitution",
                    "difficulty": "medium",
                    "summary": "Integration reverses differentiation; substitution converts an awkward integral into a standard form by changing the variable.",
                    "concepts": [
                        "Integral of x^n dx = x^(n+1)/(n+1) + C for n != -1",
                        "Integral of 1/x dx = ln|x| + C",
                        "Substitution: put u = g(x), du = g'(x) dx and integrate in u",
                        "Standard forms: 1/(x^2 + a^2) -> (1/a) tan^-1(x/a); 1/sqrt(a^2 - x^2) -> sin^-1(x/a)",
                    ],
                    "examples": [
                        "Integral of 2x/(1 + x^2) dx = ln(1 + x^2) + C using u = 1 + x^2.",
                    ],
                    "questions": [
                        {
                            "text": "The integral of 1/(1 + x^2) dx is",
                            "options": ["A. ln(1+x^2) + C", "B. tan^-1 x + C", "C. sin^-1 x + C", "D. -1/(1+x^2) + C"],
                            "answer": "B. tan^-1 x + C",
                            "explanation": "It is the standard form with a = 1: integral of dx/(x^2 + a^2) = (1/a) tan^-1(x/a) + C.",
                            "difficulty": "easy",
                            "concept": "Standard integrals",
                        },
                        {
                            "text": "Integral of e^x (sin x + cos x) dx equals",
                            "options": ["A. e^x sin x + C", "B. e^x cos x + C", "C. e^x (sin x - cos x) + C", "D. e^x tan x + C"],
                            "answer": "A. e^x sin x + C",
                            "explanation": "Use the result integral of e^x [f(x) + f'(x)] dx = e^x f(x) + C with f(x) = sin x.",
                            "difficulty": "hard",
                            "concept": "Integration by parts",
                        },
                    ],
                },
                {
                    "name": "Integration by Parts and Partial Fractions",
                    "difficulty": "hard",
                    "summary": "Products are integrated by parts using the ILATE order, while rational functions are broken into partial fractions first.",
                    "concepts": [
                        "By parts: integral u v dx = u integral v dx - integral (du/dx integral v dx) dx",
                        "ILATE order for choosing u: Inverse, Logarithmic, Algebraic, Trigonometric, Exponential",
                        "Partial fractions split a proper rational function into simpler denominators",
                        "Special result: integral of e^x[f(x) + f'(x)] dx = e^x f(x) + C",
                    ],
                    "examples": [
                        "Integral of x e^x dx = x e^x - e^x + C, choosing u = x (algebraic) and v = e^x.",
                    ],
                    "prerequisites": ["indefinite-integrals-and-substitution"],
                    "questions": [
                        {
                            "text": "In integration by parts, the ILATE rule helps to choose",
                            "options": [
                                "A. The limits of integration",
                                "B. The first function u",
                                "C. The constant of integration",
                                "D. The substitution variable",
                            ],
                            "answer": "B. The first function u",
                            "explanation": "ILATE orders function types to pick the one to differentiate (u).",
                            "difficulty": "easy",
                            "concept": "Integration by parts",
                        },
                    ],
                },
                {
                    "name": "Definite Integrals and Properties",
                    "difficulty": "medium",
                    "summary": "The definite integral is evaluated with the fundamental theorem of calculus, and symmetry properties often reduce the work to a fraction.",
                    "concepts": [
                        "Fundamental theorem: integral from a to b of f(x) dx = F(b) - F(a)",
                        "Integral from a to b = -(integral from b to a); split at any interior point",
                        "Integral from 0 to a of f(x) dx = integral from 0 to a of f(a - x) dx",
                        "Even function on [-a,a] gives 2 x integral from 0 to a; odd function gives 0",
                    ],
                    "examples": [
                        "Integral from -1 to 1 of x^3 dx = 0 because x^3 is an odd function.",
                    ],
                    "prerequisites": ["indefinite-integrals-and-substitution"],
                },
            ],
        },
        {
            "name": "Application of Integrals",
            "number": 8,
            "ncert_url": _pdf("lemh202"),
            "description": "Area under simple curves and between two curves.",
            "topics": [
                {
                    "name": "Area Under Curves",
                    "difficulty": "medium",
                    "summary": "The definite integral of a curve between two limits gives the area bounded by the curve and the axis, and subtracting two integrals gives the area between curves.",
                    "concepts": [
                        "Area under y = f(x) from a to b = integral of |f(x)| dx",
                        "Area between curves = integral of (upper - lower) dx over the intersection interval",
                        "Areas with respect to the y-axis use integral of x dy",
                        "Sketch first: intersection points decide the limits",
                    ],
                    "examples": [
                        "Area between y = x^2 and y = x from 0 to 1 is integral of (x - x^2) dx = 1/6 square units.",
                    ],
                    "prerequisites": ["definite-integrals-and-properties"],
                },
            ],
        },
        {
            "name": "Differential Equations",
            "number": 9,
            "ncert_url": _pdf("lemh203"),
            "description": "Order and degree, variable separable, homogeneous and linear differential equations.",
            "topics": [
                {
                    "name": "Order, Degree and Variable Separable Equations",
                    "difficulty": "medium",
                    "summary": "The order is the highest derivative present and the degree is its power after clearing radicals; the simplest solvable type separates the variables on either side.",
                    "concepts": [
                        "Order = highest order derivative; degree defined only for polynomial form in derivatives",
                        "Variable separable: dy/dx = f(x)g(y) leads to integral dy/g(y) = integral f(x) dx",
                        "General solution contains arbitrary constants equal to the order",
                        "Particular solution is obtained by applying the initial condition",
                    ],
                    "examples": [
                        "dy/dx = xy separates to dy/y = x dx, giving ln|y| = x^2/2 + C.",
                    ],
                },
                {
                    "name": "Linear Differential Equations",
                    "difficulty": "hard",
                    "summary": "A first order linear equation is solved by multiplying with an integrating factor that makes the left side an exact derivative.",
                    "concepts": [
                        "Standard form dy/dx + P(x) y = Q(x)",
                        "Integrating factor IF = e^(integral P dx)",
                        "Solution: y x IF = integral (Q x IF) dx + C",
                        "The same method with x and y interchanged solves dx/dy + P(y)x = Q(y)",
                    ],
                    "examples": [
                        "For dy/dx + y = e^x, IF = e^x and y e^x = integral e^2x dx = e^2x/2 + C.",
                    ],
                    "prerequisites": ["order-degree-and-variable-separable-equations"],
                },
            ],
        },
        {
            "name": "Vector Algebra",
            "number": 10,
            "ncert_url": _pdf("lemh204"),
            "description": "Vectors, dot and cross products and their applications.",
            "topics": [
                {
                    "name": "Vectors, Dot Product and Cross Product",
                    "difficulty": "medium",
                    "summary": "Vectors carry both magnitude and direction; the dot product measures alignment and returns a scalar, while the cross product returns a perpendicular vector whose magnitude is an area.",
                    "concepts": [
                        "a . b = |a||b| cos theta; perpendicular vectors have a . b = 0",
                        "a x b = |a||b| sin theta n; parallel vectors have a x b = 0",
                        "Projection of a on b = (a . b)/|b|",
                        "Area of a triangle = 1/2 |a x b|; area of parallelogram = |a x b|",
                    ],
                    "examples": [
                        "For a = i + 2j and b = 2i - j, a . b = 0, so the vectors are perpendicular.",
                    ],
                },
            ],
        },
        {
            "name": "Three Dimensional Geometry",
            "number": 11,
            "ncert_url": _pdf("lemh205"),
            "description": "Direction cosines, lines and planes in space, angles and distances.",
            "topics": [
                {
                    "name": "Lines and Planes in Space",
                    "difficulty": "hard",
                    "summary": "Lines and planes in 3D are described in vector and Cartesian form, and standard formulas give angles and shortest distances between them.",
                    "concepts": [
                        "Direction cosines satisfy l^2 + m^2 + n^2 = 1",
                        "Line: r = a + lambda b; Cartesian (x-x1)/a = (y-y1)/b = (z-z1)/c",
                        "Plane: r . n = d; Cartesian Ax + By + Cz + D = 0 with normal (A,B,C)",
                        "Shortest distance between skew lines = |(a2-a1).(b1 x b2)|/|b1 x b2|",
                    ],
                    "examples": [
                        "The angle between planes 2x + y - z = 3 and x - y + 2z = 1 uses cos theta = |n1.n2|/(|n1||n2|).",
                    ],
                    "prerequisites": ["vectors-dot-product-and-cross-product"],
                },
            ],
        },
        {
            "name": "Linear Programming",
            "number": 12,
            "ncert_url": _pdf("lemh206"),
            "description": "Formulation of LPP, feasible region and optimisation by the corner point method.",
            "topics": [
                {
                    "name": "Linear Programming Problems and Graphical Solution",
                    "difficulty": "easy",
                    "summary": "An LPP maximises or minimises a linear objective subject to linear constraints; the optimum always occurs at a corner point of the feasible region.",
                    "concepts": [
                        "Objective function Z = ax + by with constraints as linear inequalities",
                        "Feasible region is the common shaded area of all constraints",
                        "Corner point method: evaluate Z at every vertex of the feasible region",
                        "An unbounded region may have no maximum; check with an open half plane test",
                    ],
                    "examples": [
                        "Maximise Z = 3x + 4y subject to x + y <= 4, x, y >= 0: the maximum 16 occurs at (0,4).",
                    ],
                },
            ],
        },
        {
            "name": "Probability",
            "number": 13,
            "ncert_url": _pdf("lemh207"),
            "description": "Conditional probability, Bayes theorem, random variables and distributions.",
            "topics": [
                {
                    "name": "Conditional Probability and Bayes' Theorem",
                    "difficulty": "hard",
                    "summary": "Conditional probability updates a probability with new information, and Bayes' theorem reverses the conditioning to find causes from observed effects.",
                    "concepts": [
                        "P(A|B) = P(A and B)/P(B), P(B) not zero",
                        "Multiplication rule P(A and B) = P(A) P(B|A)",
                        "Independent events satisfy P(A and B) = P(A)P(B)",
                        "Bayes: P(Ei|A) = P(Ei)P(A|Ei) / sum over j of P(Ej)P(A|Ej)",
                    ],
                    "examples": [
                        "Two bags with different proportions of red balls: Bayes' theorem gives the probability the ball came from bag I.",
                    ],
                },
                {
                    "name": "Random Variables and Probability Distributions",
                    "difficulty": "medium",
                    "summary": "A random variable assigns numbers to outcomes; its distribution lists probabilities, and mean and variance summarise it.",
                    "concepts": [
                        "Sum of all probabilities in a distribution is 1",
                        "Mean (expectation) E(X) = sum of x_i p_i",
                        "Variance Var(X) = E(X^2) - [E(X)]^2",
                        "Bernoulli trials and binomial distribution P(X = r) = nCr p^r q^(n-r)",
                    ],
                    "examples": [
                        "For 5 tosses of a fair coin, P(exactly 3 heads) = 5C3 (1/2)^5 = 10/32 = 0.3125.",
                    ],
                    "prerequisites": ["conditional-probability-and-bayes-theorem"],
                },
            ],
        },
    ],
}
