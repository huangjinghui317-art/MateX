# -*- coding: utf-8 -*-
MOCK_MATERIALS = [
    {
        "material_id": "mp-149", "formula_pretty": "Si", "spacegroup": "Fd-3m", "crystal_system": "cubic",
        "density": 2.329, "band_gap": 0.60, "energy_above_hull": 0.0, "formation_energy_per_atom": 0.0,
        "is_stable": True, "elements": ["Si"], "material_class": "inorganic",
        "sites": [{"element":"Si","frac_coords":[0,0,0]},{"element":"Si","frac_coords":[0.25,0.25,0.25]}]
    },
    {
        "material_id": "mp-19017", "formula_pretty": "LiFePO4", "spacegroup": "Pnma", "crystal_system": "orthorhombic",
        "density": 3.45, "band_gap": 3.78, "energy_above_hull": 0.0, "formation_energy_per_atom": -2.91,
        "is_stable": True, "elements": ["Li","Fe","P","O"], "material_class": "inorganic",
        "sites": [
            {"element":"Li","frac_coords":[0.25,0.33,0.02]}, {"element":"Fe","frac_coords":[0,0,0]},
            {"element":"P","frac_coords":[0.10,0.25,0.42]}, {"element":"O","frac_coords":[0.21,0.04,0.32]},
            {"element":"O","frac_coords":[0.45,0.31,0.62]}, {"element":"O","frac_coords":[0.78,0.18,0.11]}
        ]
    },
    {
        "material_id": "mp-5020", "formula_pretty": "BaTiO3", "spacegroup": "P4mm", "crystal_system": "tetragonal",
        "density": 6.02, "band_gap": 1.83, "energy_above_hull": 0.018, "formation_energy_per_atom": -3.12,
        "is_stable": False, "elements": ["Ba","Ti","O"], "material_class": "inorganic",
        "sites": [
            {"element":"Ba","frac_coords":[0,0,0]}, {"element":"Ti","frac_coords":[0.5,0.5,0.51]},
            {"element":"O","frac_coords":[0.5,0.5,0.02]}, {"element":"O","frac_coords":[0.5,0,0.49]}, {"element":"O","frac_coords":[0,0.5,0.49]}
        ]
    },
    {
        "material_id": "mp-2657", "formula_pretty": "TiO2", "spacegroup": "P42/mnm", "crystal_system": "tetragonal",
        "density": 4.25, "band_gap": 1.78, "energy_above_hull": 0.0, "formation_energy_per_atom": -3.05,
        "is_stable": True, "elements": ["Ti","O"], "material_class": "inorganic",
        "sites": [
            {"element":"Ti","frac_coords":[0,0,0]}, {"element":"Ti","frac_coords":[0.5,0.5,0.5]},
            {"element":"O","frac_coords":[0.3,0.3,0]}, {"element":"O","frac_coords":[0.7,0.7,0]},
            {"element":"O","frac_coords":[0.2,0.8,0.5]}, {"element":"O","frac_coords":[0.8,0.2,0.5]}
        ]
    },
    {
        "material_id": "mp-22862", "formula_pretty": "Fe3O4", "spacegroup": "Fd-3m", "crystal_system": "cubic",
        "density": 5.18, "band_gap": 0.10, "energy_above_hull": 0.0, "formation_energy_per_atom": -1.73,
        "is_stable": True, "elements": ["Fe","O"], "material_class": "inorganic",
        "sites": [
            {"element":"Fe","frac_coords":[0,0,0]}, {"element":"Fe","frac_coords":[0.125,0.125,0.125]},
            {"element":"Fe","frac_coords":[0.5,0.5,0.5]}, {"element":"O","frac_coords":[0.25,0.25,0.25]},
            {"element":"O","frac_coords":[0.75,0.75,0.75]}, {"element":"O","frac_coords":[0.25,0.75,0.25]}
        ]
    },
    {
        "material_id": "mp-804", "formula_pretty": "GaN", "spacegroup": "P63mc", "crystal_system": "hexagonal",
        "density": 6.10, "band_gap": 1.72, "energy_above_hull": 0.0, "formation_energy_per_atom": -1.16,
        "is_stable": True, "elements": ["Ga","N"], "material_class": "inorganic",
        "sites": [
            {"element":"Ga","frac_coords":[0.333,0.667,0]}, {"element":"Ga","frac_coords":[0.667,0.333,0.5]},
            {"element":"N","frac_coords":[0.333,0.667,0.375]}, {"element":"N","frac_coords":[0.667,0.333,0.875]}
        ]
    },
]

PERIODIC_ELEMENTS = [
    # row, col, symbol, category
    (1,1,"H","nonmetal"),(1,18,"He","noble"),
    (2,1,"Li","alkali"),(2,2,"Be","alkaline"),(2,13,"B","metalloid"),(2,14,"C","nonmetal"),(2,15,"N","nonmetal"),(2,16,"O","nonmetal"),(2,17,"F","halogen"),(2,18,"Ne","noble"),
    (3,1,"Na","alkali"),(3,2,"Mg","alkaline"),(3,13,"Al","post"),(3,14,"Si","metalloid"),(3,15,"P","nonmetal"),(3,16,"S","nonmetal"),(3,17,"Cl","halogen"),(3,18,"Ar","noble"),
    (4,1,"K","alkali"),(4,2,"Ca","alkaline"),(4,3,"Sc","transition"),(4,4,"Ti","transition"),(4,5,"V","transition"),(4,6,"Cr","transition"),(4,7,"Mn","transition"),(4,8,"Fe","transition"),(4,9,"Co","transition"),(4,10,"Ni","transition"),(4,11,"Cu","transition"),(4,12,"Zn","transition"),(4,13,"Ga","post"),(4,14,"Ge","metalloid"),(4,15,"As","metalloid"),(4,16,"Se","nonmetal"),(4,17,"Br","halogen"),(4,18,"Kr","noble"),
    (5,1,"Rb","alkali"),(5,2,"Sr","alkaline"),(5,3,"Y","transition"),(5,4,"Zr","transition"),(5,5,"Nb","transition"),(5,6,"Mo","transition"),(5,7,"Tc","transition"),(5,8,"Ru","transition"),(5,9,"Rh","transition"),(5,10,"Pd","transition"),(5,11,"Ag","transition"),(5,12,"Cd","transition"),(5,13,"In","post"),(5,14,"Sn","post"),(5,15,"Sb","metalloid"),(5,16,"Te","metalloid"),(5,17,"I","halogen"),(5,18,"Xe","noble"),
    (6,1,"Cs","alkali"),(6,2,"Ba","alkaline"),(6,3,"La-Lu","lanthanide"),(6,4,"Hf","transition"),(6,5,"Ta","transition"),(6,6,"W","transition"),(6,7,"Re","transition"),(6,8,"Os","transition"),(6,9,"Ir","transition"),(6,10,"Pt","transition"),(6,11,"Au","transition"),(6,12,"Hg","transition"),(6,13,"Tl","post"),(6,14,"Pb","post"),(6,15,"Bi","post"),(6,16,"Po","post"),(6,17,"At","halogen"),(6,18,"Rn","noble"),
    (7,1,"Fr","alkali"),(7,2,"Ra","alkaline"),(7,3,"Ac-Lr","actinide"),(7,4,"Rf","transition"),(7,5,"Db","transition"),(7,6,"Sg","transition"),(7,7,"Bh","transition"),(7,8,"Hs","transition"),(7,9,"Mt","transition"),(7,10,"Ds","transition"),(7,11,"Rg","transition"),(7,12,"Cn","transition"),(7,13,"Nh","post"),(7,14,"Fl","post"),(7,15,"Mc","post"),(7,16,"Lv","post"),(7,17,"Ts","halogen"),(7,18,"Og","noble"),
    # f-block displayed explicitly
    (8,4,"La","lanthanide"),(8,5,"Ce","lanthanide"),(8,6,"Pr","lanthanide"),(8,7,"Nd","lanthanide"),(8,8,"Pm","lanthanide"),(8,9,"Sm","lanthanide"),(8,10,"Eu","lanthanide"),(8,11,"Gd","lanthanide"),(8,12,"Tb","lanthanide"),(8,13,"Dy","lanthanide"),(8,14,"Ho","lanthanide"),(8,15,"Er","lanthanide"),(8,16,"Tm","lanthanide"),(8,17,"Yb","lanthanide"),(8,18,"Lu","lanthanide"),
    (9,4,"Ac","actinide"),(9,5,"Th","actinide"),(9,6,"Pa","actinide"),(9,7,"U","actinide"),(9,8,"Np","actinide"),(9,9,"Pu","actinide"),(9,10,"Am","actinide"),(9,11,"Cm","actinide"),(9,12,"Bk","actinide"),(9,13,"Cf","actinide"),(9,14,"Es","actinide"),(9,15,"Fm","actinide"),(9,16,"Md","actinide"),(9,17,"No","actinide"),(9,18,"Lr","actinide"),
]
