"""Crop Doctor Knowledge Base — Authoritative Agricultural Pathology & Damage Intelligence.

Provides deep agronomic insights for crop diseases and physiological disorders:
- Pathogen classification and scientific causal agent
- Detailed visible damage symptoms across leaf, stem, flower, and fruit
- Disease severity rating and yield loss risk assessment
- Environmental and climatic favoring factors (humidity, temperature, leaf wetness)
- Immediate curative chemical interventions (active ingredients, formulations, dosages per liter & acre, PHI)
- Organic and bio-rational controls (bio-agents, botanicals, dosages)
- Cultural and preventive field management (sanitation, irrigation, nutrition balance)
- Differential diagnosis against look-alike diseases and nutrient deficiencies

Calibrated against ICAR (Indian Council of Agricultural Research), MPKV Rahuri,
and international agricultural university pathology standards.
"""
from typing import Any, Dict, List, Optional


DISEASE_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    # ── Tomato Diseases ──
    "Tomato___Early_blight": {
        "crop": "Tomato",
        "common_name": "Early Blight",
        "pathogen_type": "Fungal",
        "causal_agent": "Alternaria solani",
        "severity_level": "High",
        "severity_score": 75,
        "yield_loss_risk": "35% to 75% yield loss due to severe defoliation, stem cankers, and fruit rot.",
        "damage_symptoms": (
            "Small, brown-to-black spots appear first on the oldest lower leaves. Lesions rapidly enlarge "
            "up to 1.5 cm with characteristic concentric target-board rings surrounded by a chlorotic yellow halo. "
            "Infected lower foliage turns brown, withers, and drops prematurely (blighting upwards). "
            "On stems, dark sunken collar-rot cankers form at soil level. On fruits, dark, leathery, sunken "
            "lesions develop at the stem calyx end, often covered with velvety black fungal spores."
        ),
        "favorable_conditions": (
            "Warm temperatures (24°C–29°C), high relative humidity (>80%), frequent rainfall, overhead irrigation, "
            "and prolonged leaf wetness exceeding 6–8 hours."
        ),
        "chemical_control": [
            {
                "product": "Mancozeb 75% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Contact protective foliar spray",
                "spray_interval": "7–10 days during humid weather",
                "pre_harvest_interval_days": 5,
                "notes": "Ensure thorough coverage of both upper and lower leaf surfaces."
            },
            {
                "product": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic translaminar curative spray",
                "spray_interval": "10–14 days",
                "pre_harvest_interval_days": 3,
                "notes": "Provides rapid curative knockdown when lesions are already expanding."
            },
            {
                "product": "Chlorothalonil 75% WP",
                "dosage_per_liter": "2.0 g / liter",
                "dosage_per_acre": "400 g in 200 L water / acre",
                "application_type": "Broad-spectrum contact protective spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Do not mix with horticultural oils or emulsifiable concentrates."
            }
        ],
        "organic_control": [
            {
                "name": "Trichoderma harzianum / viride (2x10^9 CFU/g)",
                "dosage": "5.0 g / liter foliar spray; 2 kg / acre in 100 kg farmyard manure as soil drench",
                "timing": "Preventive at first sign of humidity",
                "mechanism": "Competitive fungal mycoparasitism and induced systemic resistance (ISR)."
            },
            {
                "name": "Cold-Pressed Neem Oil (Azadirachtin 10,000 ppm)",
                "dosage": "3.0 ml / liter with 0.5 ml organic surfactant (liquid soap)",
                "timing": "Early morning or late afternoon spray",
                "mechanism": "Inhibits fungal spore germination and appressorium penetration."
            },
            {
                "name": "Copper Hydroxide (Organic certified formulation)",
                "dosage": "2.0 g / liter",
                "timing": "At first lesion appearance",
                "mechanism": "Multi-site contact disruption of fungal spore enzymes."
            }
        ],
        "cultural_ipm": [
            "Prune and safely burn the bottom 25–30 cm of leaves to prevent soil-splash inoculum transfer.",
            "Switch from furrow or overhead sprinklers to drip irrigation to keep canopy foliage completely dry.",
            "Apply straw mulch or silver-black reflective plastic mulch (30 micron) across beds.",
            "Avoid excess vegetative nitrogen; balance with potassium (K2O) and calcium nitrate to toughen leaf cuticles.",
            "Maintain a strict 3-year crop rotation avoiding all Solanaceous hosts (potato, brinjal, chili)."
        ],
        "differential_diagnosis": (
            "Differentiate from Late Blight (Phytophthora infestans): Late blight produces dark water-soaked greasy "
            "lesions without concentric rings and displays fuzzy white cottony sporulation on the leaf underside "
            "during cool wet spells. Differentiate from Septoria leaf spot: Septoria spots are smaller (2–4 mm), "
            "numerous, with distinct gray centers studded with tiny black pycnidia specks."
        )
    },

    "Tomato___Late_blight": {
        "crop": "Tomato",
        "common_name": "Late Blight",
        "pathogen_type": "Oomycete / Water Mold",
        "causal_agent": "Phytophthora infestans",
        "severity_level": "Critical",
        "severity_score": 95,
        "yield_loss_risk": "Up to 100% total crop destruction within 7–14 days during cool, foggy, humid outbreaks.",
        "damage_symptoms": (
            "Large, irregular, water-soaked dark greenish-black greasy lesions appear abruptly on leaf margins "
            "and tips. Under high humidity, a delicate white cottony or downy mildew mold growth develops "
            "on the undersides of infected leaves. Foliage turns brown, shrivels, and dies rapidly, "
            "giving the field a burned appearance. Stems develop dark greasy water-soaked lesions that "
            "cause canopy collapse. Fruit develops large, firm, bumpy, greasy olive-brown to bronze rot patches."
        ),
        "favorable_conditions": (
            "Cool to moderate temperatures (12°C–22°C), persistent cloudiness, morning fog, relative humidity >90%, "
            "and extended periods of free water on leaves."
        ),
        "chemical_control": [
            {
                "product": "Metalaxyl-M 4% + Mancozeb 64% WP (Ridomil Gold)",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Systemic and contact dual-action curative spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Apply immediately upon disease sighting to halt mycelial spread."
            },
            {
                "product": "Cymoxanil 8% + Mancozeb 64% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Translaminar kickback curative spray",
                "spray_interval": "7 days",
                "pre_harvest_interval_days": 5,
                "notes": "Effective kickback action up to 48 hours post-infection."
            },
            {
                "product": "Dimethomorph 50% WP",
                "dosage_per_liter": "1.0 g / liter",
                "dosage_per_acre": "200 g in 200 L water / acre",
                "application_type": "Anti-sporulant cell-wall lysis spray",
                "spray_interval": "8–10 days",
                "pre_harvest_interval_days": 5,
                "notes": "Stops zoospore motility and sporulation."
            }
        ],
        "organic_control": [
            {
                "name": "Bordeaux Mixture (1:1:100 / 1% formulation)",
                "dosage": "1.0 kg Copper Sulfate + 1.0 kg Slaked Lime in 100 L water",
                "timing": "Preventative spray prior to anticipated rain / cold fog",
                "mechanism": "Precipitates fungal cell proteins and protects surface tissue."
            },
            {
                "name": "Bacillus amyloliquefaciens / subtilis (strain D747)",
                "dosage": "3.0 g / liter",
                "timing": "Weekly preventive bio-spray",
                "mechanism": "Antibiosis through lipopeptide secretion and competitive colonization."
            }
        ],
        "cultural_ipm": [
            "Destroy and bury all volunteer plants and cull piles from nearby fields before monsoon/winter.",
            "Never allow sprinkler irrigation late in the evening; switch strictly to subsurface drip.",
            "Plant resistant F1 hybrid cultivars (e.g., Abhinav, US 440, ToMV-resistant lines where available).",
            "Immediately remove and bag heavily blighted plants to stop airborne zoosporangia dispersal."
        ],
        "differential_diagnosis": (
            "Differentiate from Early Blight: Late blight has NO concentric rings, lesions expand much faster, "
            "shows white downy fungal bloom on leaf underside, and thrives in cool wet conditions (below 22°C)."
        )
    },

    "Tomato___Bacterial_spot": {
        "crop": "Tomato",
        "common_name": "Bacterial Spot",
        "pathogen_type": "Bacterial",
        "causal_agent": "Xanthomonas campestris pv. vesicatoria",
        "severity_level": "High",
        "severity_score": 70,
        "yield_loss_risk": "25% to 50% yield reduction due to extensive defoliation, blossom drop, and unmarketable scabby fruit.",
        "damage_symptoms": (
            "Numerous small (1–3 mm), dark brown to black, water-soaked circular spots appear on leaves. "
            "Lesions develop a prominent greasy appearance and may be surrounded by a narrow yellow halo. "
            "Centers of older leaf lesions frequently dry out, turn brittle, and tear or fall out, giving leaves "
            "a ragged shot-hole appearance. On green fruits, small raised black blisters enlarge into rough, "
            "scabby, sunken brown craters (2–5 mm) with ruptured epidermal margins."
        ),
        "favorable_conditions": (
            "Warm temperatures (24°C–32°C), high humidity, driving rains, wind-blown spray droplets, and mechanical pruning wounds."
        ),
        "chemical_control": [
            {
                "product": "Copper Oxychloride 50% WP + Streptocycline (90:10)",
                "dosage_per_liter": "2.5 g Copper Oxychloride + 0.1 g (100 ppm) Streptocycline per liter",
                "dosage_per_acre": "500 g COC + 20 g Streptocycline in 200 L water",
                "application_type": "Protective bactericide spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Synergistic tank-mix prevents copper-resistant bacterial strains."
            },
            {
                "product": "Kasugamycin 3% SL",
                "dosage_per_liter": "2.0 ml / liter",
                "dosage_per_acre": "400 ml in 200 L water / acre",
                "application_type": "Systemic agricultural bactericide",
                "spray_interval": "10 days",
                "pre_harvest_interval_days": 3,
                "notes": "Directly inhibits bacterial protein synthesis."
            }
        ],
        "organic_control": [
            {
                "name": "Pseudomonas fluorescens (1% WP)",
                "dosage": "5.0 g / liter foliar spray; 2.5 kg / acre soil drench",
                "timing": "At seedling stage and repeated every 14 days",
                "mechanism": "Produces phenazine antibiotics and siderophores that starve bacterial pathogens."
            },
            {
                "name": "Cow Urine (Gomutra) + Hing (Asafoetida) Extract",
                "dosage": "100 ml aged cow urine + 1 g hing per 10 L water",
                "timing": "Foliar mist every 10 days",
                "mechanism": "Alkaline osmotic barrier and natural antimicrobial sulfur volatile compounds."
            }
        ],
        "cultural_ipm": [
            "Use certified pathogen-free seeds treated with hot water (50°C for 25 minutes) before sowing.",
            "Strictly avoid working in or pruning the tomato field when foliage is wet from dew or rain.",
            "Sanitize pruning shears in 10% sodium hypochlorite (bleach) or 70% alcohol between rows.",
            "Rotate out of solanaceous crops for at least 2 consecutive seasons."
        ],
        "differential_diagnosis": (
            "Differentiate from Early Blight: Bacterial spots are smaller (<3 mm), greasy/water-soaked, "
            "never exhibit target concentric rings, and fruit lesions have raised scabby craters rather than "
            "large sunken leathery stem-end decay."
        )
    },

    "Tomato___Septoria_leaf_spot": {
        "crop": "Tomato",
        "common_name": "Septoria Leaf Spot",
        "pathogen_type": "Fungal",
        "causal_agent": "Septoria lycopersici",
        "severity_level": "Moderate",
        "severity_score": 60,
        "yield_loss_risk": "20% to 45% yield loss primarily through complete sun-scald of defoliated tomato fruits.",
        "damage_symptoms": (
            "Numerous small, circular spots (2–4 mm diameter) erupt on older lower leaves. Lesions have dark brown "
            "borders with distinct ash-gray or tan centers. Inside the gray center, tiny black pepper-like specks "
            "(fruiting pycnidia) can be seen with a 10x hand lens. Heavily infected leaves turn yellow, curl up, "
            "wither, and drop off rapidly. Defoliation progresses from base to top, exposing tomatoes to severe sun-scald."
        ),
        "favorable_conditions": (
            "Moderate warm weather (20°C–26°C), prolonged leaf wetness (>10 hours), and high relative humidity (>85%)."
        ),
        "chemical_control": [
            {
                "product": "Chlorothalonil 75% WP",
                "dosage_per_liter": "2.0 g / liter",
                "dosage_per_acre": "400 g in 200 L water / acre",
                "application_type": "Contact protective spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Covers newly emerged foliage to block spore germ tubes."
            },
            {
                "product": "Tebuconazole 25.9% EC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic triazole fungicide",
                "spray_interval": "12–14 days",
                "pre_harvest_interval_days": 5,
                "notes": "Stops ergosterol biosynthesis in vegetative fungal hyphae."
            }
        ],
        "organic_control": [
            {
                "name": "Copper Oxychloride 50% WP (Bio-compatible)",
                "dosage": "2.5 g / liter",
                "timing": "At first sign of lower leaf spotting",
                "mechanism": "Multi-site protective copper barrier on leaf surface."
            },
            {
                "name": "Trichoderma viride + Compost Extract",
                "dosage": "5.0 g / liter",
                "timing": "Bi-weekly foliar application",
                "mechanism": "Competitive colonization of leaf phylloplane."
            }
        ],
        "cultural_ipm": [
            "Hand-strip lower infected leaves as soon as first 3–4 spots appear; remove from field.",
            "Keep tomato plants firmly staked and tied off the ground.",
            "Maintain wide plant spacing (60 cm x 90 cm) for fast canopy wind drying.",
            "Never compost infected tomato foliage."
        ],
        "differential_diagnosis": (
            "Differentiate from Early Blight: Septoria lesions remain small (2–4 mm) with characteristic ash-gray centers "
            "studded with black pycnidia specks, and do NOT form large 1–2 cm target-board concentric rings."
        )
    },

    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": {
        "crop": "Tomato",
        "common_name": "Tomato Yellow Leaf Curl Virus (TYLCV)",
        "pathogen_type": "Viral (Begomovirus)",
        "causal_agent": "Tomato Yellow Leaf Curl Geminivirus (transmitted by Whitefly: Bemisia tabaci)",
        "severity_level": "Critical",
        "severity_score": 90,
        "yield_loss_risk": "Up to 80%–100% loss if infected during vegetative or early flowering stages.",
        "damage_symptoms": (
            "Infected plants show severe upward cupping and curling of leaf margins, thick leathery leaf texture, "
            "and pronounced interveinal chlorosis (yellowing between green veins). Leaves become abnormally small "
            "(boat-shaped or crinkled). Plants become stunted with short internodes and take on a bushy appearance. "
            "Flower buds fail to set and drop prematurely. Any fruits already formed remain small, pale, and unmarketable."
        ),
        "favorable_conditions": (
            "Dry, hot weather (28°C–38°C) that favors massive populations and rapid reproduction of the whitefly vector."
        ),
        "chemical_control": [
            {
                "product": "Diafenthiuron 50% WP",
                "dosage_per_liter": "1.25 g / liter",
                "dosage_per_acre": "250 g in 200 L water / acre",
                "application_type": "Foliar spray targeting whitefly nymphs and adults",
                "spray_interval": "10–12 days",
                "pre_harvest_interval_days": 5,
                "notes": "Acts on insect mitochondrial ATPase; excellent knockdown of resistant whiteflies."
            },
            {
                "product": "Spiromesifen 22.9% SC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Lipid synthesis inhibitor targeting eggs and nymphs",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 3,
                "notes": "Spray specifically targeting the undersides of leaves."
            },
            {
                "product": "Thiamethoxam 25% WG",
                "dosage_per_liter": "0.35 g / liter",
                "dosage_per_acre": "80 g in 200 L water / acre",
                "application_type": "Systemic neonicotinoid spray",
                "spray_interval": "12–15 days",
                "pre_harvest_interval_days": 5,
                "notes": "Use alternatively with non-neonicotinoids to prevent insect resistance."
            }
        ],
        "organic_control": [
            {
                "name": "Yellow Sticky Traps",
                "dosage": "15 to 20 traps per acre installed at canopy level",
                "timing": "From transplanting onwards",
                "mechanism": "Physical mass trapping of adult whiteflies."
            },
            {
                "name": "Neem Seed Kernel Extract (NSKE 5%) or Azadirachtin 10,000 ppm",
                "dosage": "3.0 ml / liter",
                "timing": "Weekly spray",
                "mechanism": "Antifeedant, insect growth regulator, and oviposition deterrent."
            },
            {
                "name": "Beauveria bassiana (1x10^8 CFU/g)",
                "dosage": "5.0 g / liter",
                "timing": "Evening spray during calm wind",
                "mechanism": "Entomopathogenic fungus that parasitizes whitefly nymphs."
            }
        ],
        "cultural_ipm": [
            "Install insect-proof nylon net (40–50 mesh) in seedling nurseries for the first 30 days.",
            "Erect border trap crops: plant 2–3 dense rows of maize or jowar around the field 30 days before tomato planting.",
            "Rogue out and immediately destroy virus-infected plants during early vegetative stage in airtight plastic bags.",
            "Plant TYLCV-tolerant/resistant hybrid varieties (e.g., US 440, ToMV-resistant lines)."
        ],
        "differential_diagnosis": (
            "Differentiate from Tomato Mosaic Virus (ToMV): ToMV causes mottled dark green and light green blistering "
            "patches without upward cupping. Differentiate from physiological leaf curl: Physiological curl is caused by "
            "water stress or high heat; leaves curl upward but retain deep green color without yellowing or stunting."
        )
    },

    "Tomato___Tomato_mosaic_virus": {
        "crop": "Tomato",
        "common_name": "Tomato Mosaic Virus (ToMV)",
        "pathogen_type": "Viral (Tobamovirus)",
        "causal_agent": "Tomato Mosaic Tobamovirus (mechanically transmitted)",
        "severity_level": "High",
        "severity_score": 75,
        "yield_loss_risk": "30% to 60% reduction in fruit yield with severe internal brown browning of fruit walls.",
        "damage_symptoms": (
            "Leaves exhibit alternating light green and dark green mosaic or mottled patterns. "
            "Infected leaves may develop blister-like puckering or narrow 'shoestring' fern-like distortion. "
            "Plants are mildly stunted. Fruits exhibit uneven ripening, yellow blotches, and internal brown "
            "vascular browning (brown necrotic streaks inside fruit walls)."
        ),
        "favorable_conditions": (
            "Mechanical transfer through pruning tools, worker hands, clothing, infected seed coats, and root-to-root contact."
        ),
        "chemical_control": [
            {
                "product": "No chemical viricide exists",
                "dosage_per_liter": "N/A",
                "dosage_per_acre": "N/A",
                "application_type": "Viruses cannot be cured with chemical sprays",
                "spray_interval": "N/A",
                "pre_harvest_interval_days": 0,
                "notes": "Do not spray fungicides or bactericides; focus strictly on field sanitation and worker hygiene."
            }
        ],
        "organic_control": [
            {
                "name": "Non-Fat Skimmed Milk Spray (20% solution)",
                "dosage": "200 ml skimmed milk powder solution per liter water",
                "timing": "Spray immediately prior to mechanical pruning/trellising",
                "mechanism": "Milk proteins inactivate the virus particles on plant surfaces and tools."
            },
            {
                "name": "Trisodium Phosphate (TSP 10%) Tool Dip",
                "dosage": "100 g TSP per liter water",
                "timing": "Dip tools and hands between touching every plant",
                "mechanism": "Chemical denaturation of stable viral capsid coat."
            }
        ],
        "cultural_ipm": [
            "Use certified virus-free seed treated with 10% trisodium phosphate for 30 minutes.",
            "Prohibit smoking, chewing, or handling raw tobacco near tomato plants (tobacco mosaic virus cross-infection).",
            "Wash hands thoroughly with soap and warm water before handling seedlings.",
            "Rogue out and destroy infected plants with their root balls immediately."
        ],
        "differential_diagnosis": (
            "Differentiate from TYLCV: ToMV causes light/dark green mottling and leaf blister puckering without "
            "interveinal yellowing, and is spread by mechanical contact rather than whiteflies."
        )
    },

    "Tomato___Spider_mites Two-spotted_spider_mite": {
        "crop": "Tomato",
        "common_name": "Two-Spotted Spider Mites",
        "pathogen_type": "Pest / Acarid",
        "causal_agent": "Tetranychus urticae (Arachnida: Acari)",
        "severity_level": "High",
        "severity_score": 75,
        "yield_loss_risk": "30% to 65% loss; complete bronzing and defoliation under hot dry spells.",
        "damage_symptoms": (
            "Fine yellow, white, or stippled specks appear on the upper surface of leaves. As feeding progresses, "
            "leaves turn yellow, bronze, dry out, and drop prematurely. Fine silken webbing covers the undersides "
            "of leaves, growing tips, and flower clusters. Tiny yellow-green or reddish mites with two dark body "
            "spots can be seen scurrying within the webs under 10x magnification."
        ),
        "favorable_conditions": (
            "Hot, dry, and dusty weather (temperatures >30°C, relative humidity <50%), and excessive broad-spectrum pyrethroid insecticide sprays that kill beneficial predatory mites."
        ),
        "chemical_control": [
            {
                "product": "Spiromesifen 22.9% SC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Acaricide targeting eggs and nymphs",
                "spray_interval": "10–12 days",
                "pre_harvest_interval_days": 3,
                "notes": "Direct spray to the undersides of leaves."
            },
            {
                "product": "Abamectin 1.9% EC",
                "dosage_per_liter": "0.75 ml / liter",
                "dosage_per_acre": "150 ml in 200 L water / acre",
                "application_type": "Translaminar miticide",
                "spray_interval": "10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Fast-acting translaminar knockdown."
            },
            {
                "product": "Propargite 57% EC",
                "dosage_per_liter": "2.0 ml / liter",
                "dosage_per_acre": "400 ml in 200 L water / acre",
                "application_type": "Contact miticide",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 5,
                "notes": "Effective on adult mite stages."
            }
        ],
        "organic_control": [
            {
                "name": "Wettable Sulfur 80% WDG",
                "dosage": "3.0 g / liter",
                "timing": "Early morning spray when temp is <32°C",
                "mechanism": "Multi-site respiratory miticide and powdery mildew preventative."
            },
            {
                "name": "Predatory Mites (Neoseiulus californicus or Phytoseiulus persimilis)",
                "dosage": "2 to 5 predatory mites per plant",
                "timing": "At first stippling detection",
                "mechanism": "Active biological predation on spider mite eggs, nymphs, and adults."
            },
            {
                "name": "Cold-Pressed Neem Oil (10,000 ppm)",
                "dosage": "4.0 ml / liter + organic liquid soap",
                "timing": "Weekly spray",
                "mechanism": "Suffocates mites and disrupts juvenile hormonal molting."
            }
        ],
        "cultural_ipm": [
            "Hose down dusty farm bunds and roadways adjacent to the crop to suppress dust mite drift.",
            "Avoid broad-spectrum synthetic pyrethroids (cypermethrin, deltamethrin) that kill natural predators.",
            "Maintain adequate soil irrigation; drought-stressed plants are preferred mite hosts."
        ],
        "differential_diagnosis": (
            "Differentiate from leaf spot diseases: Spider mite damage consists of millions of microscopic pale "
            "yellow stippled pinpricks and distinctive silken webbing on leaf undersides, rather than defined circular lesions."
        )
    },

    "Tomato___healthy": {
        "crop": "Tomato",
        "common_name": "Healthy Tomato Foliage",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0% (Crop foliage is robust and disease-free).",
        "damage_symptoms": (
            "Leaves exhibit vigorous deep green color, smooth turgid laminae, clean margins, and active vegetative growth. "
            "No necrotic lesions, water-soaking, fungal sporulation, chlorosis, or insect webbing present."
        ),
        "favorable_conditions": "Balanced soil nutrition, optimal drip moisture, well-aerated soil pH 6.0–7.0.",
        "chemical_control": [],
        "organic_control": [
            {
                "name": "Preventive Bio-Fungicide (Trichoderma viride)",
                "dosage": "5.0 g / liter monthly foliar spray",
                "timing": "Routine maintenance",
                "mechanism": "Maintains beneficial microbial barrier against opportunistic spore settlement."
            }
        ],
        "cultural_ipm": [
            "Maintain balanced N-P-K fertilization according to Soil Health Card test results.",
            "Prune side suckers cleanly in dry morning weather to preserve single/double leaders.",
            "Maintain consistent drip scheduling to prevent physiological blossom end rot.",
            "Conduct routine scouting twice a week across leaves, stem nodes, and fruit calyxes."
        ],
        "differential_diagnosis": "No symptoms detected."
    },

    # ── Potato Diseases ──
    "Potato___Early_blight": {
        "crop": "Potato",
        "common_name": "Early Blight",
        "pathogen_type": "Fungal",
        "causal_agent": "Alternaria solani",
        "severity_level": "High",
        "severity_score": 70,
        "yield_loss_risk": "25% to 50% tuber yield loss due to premature vine death and undersized tubers.",
        "damage_symptoms": (
            "Dark brown to black circular-to-oval spots with prominent concentric rings appear on older lower leaves. "
            "Leaves turn yellow and drop prematurely. On tubers, sunken, dark, irregular lesions with raised purplish "
            "margins develop, with dry corky brown rot underneath."
        ),
        "favorable_conditions": "Warm temperatures (22°C–30°C), alternating wet and dry weather, nutrient-stressed vines.",
        "chemical_control": [
            {
                "product": "Mancozeb 75% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Protective contact spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Spray at first sign of lower canopy spotting."
            },
            {
                "product": "Azoxystrobin 23% SC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic curative spray",
                "spray_interval": "10–12 days",
                "pre_harvest_interval_days": 10,
                "notes": "Excellent translaminar leaf protection."
            }
        ],
        "organic_control": [
            {
                "name": "Trichoderma harzianum (2x10^9 CFU/g)",
                "dosage": "5.0 g / liter foliar; 2.5 kg / acre soil drench",
                "timing": "At tuber initiation and 20 days later",
                "mechanism": "Competitive exclusion of Alternaria spores."
            }
        ],
        "cultural_ipm": [
            "Maintain adequate nitrogen and potassium; nitrogen-deficient potato plants are severely susceptible.",
            "Kill potato vines (haulm cutting) 10–14 days before harvest to allow tuber skins to harden.",
            "Avoid overhead irrigation in late afternoon."
        ],
        "differential_diagnosis": (
            "Differentiate from Potato Late Blight: Early blight lesions have concentric target rings and dry texture, "
            "while Late blight lesions are water-soaked, expand in 2–3 days, and show white mold on undersides."
        )
    },

    "Potato___Late_blight": {
        "crop": "Potato",
        "common_name": "Late Blight",
        "pathogen_type": "Oomycete / Water Mold",
        "causal_agent": "Phytophthora infestans",
        "severity_level": "Critical",
        "severity_score": 95,
        "yield_loss_risk": "Up to 100% total crop loss; destroys canopy and causes tuber rot in storage.",
        "damage_symptoms": (
            "Water-soaked, irregular blackish-brown lesions develop rapidly on leaf tips and margins. "
            "Under humid conditions, fine white downy fungal growth appears at the margin of lesions on the leaf "
            "underside. Stems develop dark brown to black greasy water-soaked girdling lesions that cause plants "
            "to collapse. Infected tubers show irregular, slightly sunken, reddish-brown to purplish surface rot "
            "extending into the flesh as a dry, granular, reddish-brown decay."
        ),
        "favorable_conditions": "Cool temperatures (10°C–20°C), relative humidity >90%, persistent rainfall, dew, or morning fog.",
        "chemical_control": [
            {
                "product": "Metalaxyl-M 4% + Mancozeb 64% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Systemic and contact curative spray",
                "spray_interval": "7 days",
                "pre_harvest_interval_days": 7,
                "notes": "Apply immediately upon symptom detection."
            },
            {
                "product": "Cymoxanil 8% + Mancozeb 64% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Translaminar kickback spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Arrests established mycelium."
            }
        ],
        "organic_control": [
            {
                "name": "Bordeaux Mixture (1%)",
                "dosage": "1.0 kg CuSO4 + 1.0 kg lime in 100 L water",
                "timing": "Preventative spray prior to fog/rain spells",
                "mechanism": "Forms durable protective copper film."
            }
        ],
        "cultural_ipm": [
            "Plant only certified, disease-free seed tubers.",
            "Hill soil well over potato ridges (10–15 cm soil cover) to prevent zoospores washing down to tubers.",
            "Destroy all cull piles and volunteer potatoes in the vicinity before planting.",
            "Cut haulms (vines) completely and allow 10 days for tuber skins to set before digging."
        ],
        "differential_diagnosis": "Differentiate from Early Blight: Late blight spreads explosively during cool foggy weather."
    },

    "Potato___healthy": {
        "crop": "Potato",
        "common_name": "Healthy Potato Vines",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0%",
        "damage_symptoms": "Clean, vigorous, dark green compound leaves without spots, wilting, or stem rot.",
        "favorable_conditions": "Cool nights (15°C–18°C), well-drained fertile loamy soil.",
        "chemical_control": [],
        "organic_control": [],
        "cultural_ipm": [
            "Ensure ridge earthing-up (hilling) is completed by 30–40 days after sowing.",
            "Maintain soil moisture at 65–75% field capacity during tuber bulking.",
            "Scout weekly for aphids and leafhopper vectors."
        ],
        "differential_diagnosis": "No symptoms detected."
    },

    # ── Corn / Maize Diseases ──
    "Corn_(maize)___Common_rust_": {
        "crop": "Corn (Maize)",
        "common_name": "Common Rust",
        "pathogen_type": "Fungal",
        "causal_agent": "Puccinia sorghi",
        "severity_level": "Moderate",
        "severity_score": 55,
        "yield_loss_risk": "15% to 35% reduction in grain yield through reduced photosynthetic leaf area.",
        "damage_symptoms": (
            "Small, oval to elongate, golden-brown to cinnamon-brown powdery pustules (uredinia) erupt on both "
            "upper and lower leaf surfaces. Pustules rupture the epidermis, releasing mass powdery rust spores. "
            "As season progresses, pustules turn dark brown to black (telia stage). Severe infection causes leaves "
            "to turn yellow, desiccate, and die prematurely."
        ),
        "favorable_conditions": "Cool to moderate temperatures (16°C–25°C), high relative humidity (>95%), and 6 hours of dew.",
        "chemical_control": [
            {
                "product": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic curative fungicide",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 14,
                "notes": "Spray at first sign of pustules on ear leaf or leaves below."
            },
            {
                "product": "Mancozeb 75% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Contact protective spray",
                "spray_interval": "10 days",
                "pre_harvest_interval_days": 14,
                "notes": "Cost-effective protective cover."
            }
        ],
        "organic_control": [
            {
                "name": "Wettable Sulfur 80% WDG",
                "dosage": "3.0 g / liter",
                "timing": "At first rust pustule appearance",
                "mechanism": "Sulfur vapor action inhibits rust urediniospore germination."
            }
        ],
        "cultural_ipm": [
            "Plant rust-resistant hybrid corn varieties.",
            "Avoid planting very late in the season when rust spore showers from early crops are intense.",
            "Avoid excess nitrogen fertilizer which creates lush, thin-walled leaf tissue."
        ],
        "differential_diagnosis": (
            "Differentiate from Southern Rust (Puccinia polysora): Common rust pustules appear equally on both leaf "
            "surfaces and prefer cool temperatures; Southern rust pustules are smaller, orange-brown, concentrated "
            "almost exclusively on the upper leaf surface, and thrive in hot humid weather (>28°C)."
        )
    },

    "Corn_(maize)___Northern_Leaf_Blight": {
        "crop": "Corn (Maize)",
        "common_name": "Northern Corn Leaf Blight (NCLB)",
        "pathogen_type": "Fungal",
        "causal_agent": "Exserohilum turcicum (syn. Helminthosporium turcicum)",
        "severity_level": "High",
        "severity_score": 75,
        "yield_loss_risk": "30% to 50% grain yield loss if infection hits upper canopy prior to silking.",
        "damage_symptoms": (
            "Long, elliptical, cigar-shaped or spindle-shaped grayish-green to tan lesions (2.5 to 15 cm long) "
            "form on leaves. As lesions mature, they become necrotic and tan with dark margins. During damp weather, "
            "dark olive-green to black velvety fungal spore mats develop within the center of lesions. Lesions can "
            "coalesce to destroy entire leaf blades."
        ),
        "favorable_conditions": "Moderate temperatures (18°C–27°C), heavy dews, frequent rain showers, and minimum tillage corn residue.",
        "chemical_control": [
            {
                "product": "Azoxystrobin 18.2% + Difenoconazole 11.4% SC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic protective & curative spray",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 14,
                "notes": "Highly effective on NCLB."
            },
            {
                "product": "Propiconazole 25% EC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic triazole spray",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 21,
                "notes": "Apply between V8 and tasseling."
            }
        ],
        "organic_control": [
            {
                "name": "Trichoderma viride foliar spray",
                "dosage": "5.0 g / liter",
                "timing": "At V6–V8 stage",
                "mechanism": "Colonizes leaf surface to inhibit germ tube elongation."
            }
        ],
        "cultural_ipm": [
            "Plant resistant maize hybrids.",
            "Rotate crops with soybean, chickpea, or cotton for at least 1–2 years.",
            "Practice deep summer plowing to bury infested corn stubble and accelerate residue decomposition."
        ],
        "differential_diagnosis": (
            "Differentiate from Gray Leaf Spot: NCLB lesions are large, cigar-shaped with rounded ends; "
            "Gray leaf spot lesions are strictly rectangular, blocky, and bounded by leaf veins."
        )
    },

    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": {
        "crop": "Corn (Maize)",
        "common_name": "Gray Leaf Spot",
        "pathogen_type": "Fungal",
        "causal_agent": "Cercospora zeae-maydis",
        "severity_level": "High",
        "severity_score": 70,
        "yield_loss_risk": "25% to 45% grain yield reduction through premature canopy death.",
        "damage_symptoms": (
            "Small tan spots with yellow halos appear first on lower leaves. Lesions expand into distinctive "
            "long, narrow, rectangular gray-to-tan stripes (2 to 5 cm long) with sharp parallel margins strictly "
            "delimited by leaf veins. Under humid conditions, lesions turn gray as spores form. Coalescing lesions "
            "cause extensive leaf blighting and stalk lodging."
        ),
        "favorable_conditions": "Warm temperatures (24°C–32°C), high relative humidity (>90%), and continuous corn cropping.",
        "chemical_control": [
            {
                "product": "Pyraclostrobin 20% WG",
                "dosage_per_liter": "1.0 g / liter",
                "dosage_per_acre": "200 g in 200 L water / acre",
                "application_type": "Strobilurin translaminar spray",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 14,
                "notes": "Apply at tasseling/silking stage."
            }
        ],
        "organic_control": [
            {
                "name": "Pseudomonas fluorescens (1% WP)",
                "dosage": "5.0 g / liter",
                "timing": "Vegetative stage foliar spray",
                "mechanism": "Antibiosis and phyllosphere competitive exclusion."
            }
        ],
        "cultural_ipm": [
            "Rotate with non-host crops like pulses, groundnut, or cotton for at least 1 year.",
            "Shred and bury crop residue with deep plowing.",
            "Select resistant maize cultivars."
        ],
        "differential_diagnosis": "Differentiate from NCLB: Gray leaf spot lesions are strictly rectangular with parallel straight edges."
    },

    "Corn_(maize)___healthy": {
        "crop": "Corn (Maize)",
        "common_name": "Healthy Corn Foliage",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0%",
        "damage_symptoms": "Broad, vibrant deep-green leaves with sturdy stalks, clear veins, and no necrotic lesions or rust pustules.",
        "favorable_conditions": "Warm sunny days, adequate soil nitrogen and moisture during knee-high to tasseling stages.",
        "chemical_control": [],
        "organic_control": [],
        "cultural_ipm": [
            "Apply split nitrogen doses (1/3 at sowing, 1/3 at knee-high V6 stage, 1/3 at tasseling).",
            "Monitor for Fall Armyworm (Spodoptera frugiperda) in the central whorl.",
            "Maintain weed-free conditions during the first 30 days."
        ],
        "differential_diagnosis": "No symptoms detected."
    },

    # ── Grape Diseases ──
    "Grape___Black_rot": {
        "crop": "Grape",
        "common_name": "Black Rot",
        "pathogen_type": "Fungal",
        "causal_agent": "Guignardia bidwellii (syn. Phyllosticta ampelicida)",
        "severity_level": "High",
        "severity_score": 80,
        "yield_loss_risk": "50% to 100% loss of fruit clusters under wet conditions if unchecked.",
        "damage_symptoms": (
            "Small circular reddish-brown spots appear on leaves in spring, developing dark margins with tiny "
            "black pimple-like pycnidia arranged in rings inside the spot. On berries, small white spots quickly "
            "turn brown, rot the entire berry within 48 hours, and shrivel the grape into a hard, black, wrinkled "
            "'mummy' that stays attached to the bunch."
        ),
        "favorable_conditions": "Warm wet weather (21°C–27°C) with 6–24 hours of continuous leaf and berry wetness.",
        "chemical_control": [
            {
                "product": "Mancozeb 75% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Protective contact spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 14,
                "notes": "Start sprays from bud break through 4 weeks post-bloom."
            },
            {
                "product": "Myclobutanil 10% WP",
                "dosage_per_liter": "0.5 g / liter",
                "dosage_per_acre": "100 g in 200 L water / acre",
                "application_type": "Systemic triazole fungicide",
                "spray_interval": "14 days",
                "pre_harvest_interval_days": 14,
                "notes": "Offers 72-hour reach-back curative activity."
            }
        ],
        "organic_control": [
            {
                "name": "Copper Oxychloride 50% WP",
                "dosage": "2.5 g / liter",
                "timing": "Pre-bloom and post-bloom protective cover",
                "mechanism": "Multi-site contact inhibition of spore germination."
            }
        ],
        "cultural_ipm": [
            "Crucial: Collect and destroy all mummified grape berries from vines and vineyard floor during winter pruning.",
            "Canopy management: Prune and shoot-thin to allow direct sunlight and wind circulation through fruit zones.",
            "Keep vines trained well off the ground on trellises."
        ],
        "differential_diagnosis": "Differentiate from Downy Mildew: Black rot forms hard dry black mummies; Downy mildew produces soft oily berries with white downy growth."
    },

    "Grape___healthy": {
        "crop": "Grape",
        "common_name": "Healthy Grape Vines",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0%",
        "damage_symptoms": "Vigorous green palmate leaves, clean canes, and well-formed clusters free of mummies or mold.",
        "favorable_conditions": "Arid to semi-arid climate with warm dry summers and well-drained gravelly/loamy soils.",
        "chemical_control": [],
        "organic_control": [],
        "cultural_ipm": [
            "Perform shoot positioning and canopy thinning to optimize sunlight penetration.",
            "Maintain regulated deficit irrigation (RDI) after veraison for high berry brix."
        ],
        "differential_diagnosis": "No symptoms detected."
    },

    # ── Apple Diseases ──
    "Apple___Apple_scab": {
        "crop": "Apple",
        "common_name": "Apple Scab",
        "pathogen_type": "Fungal",
        "causal_agent": "Venturia inaequalis",
        "severity_level": "High",
        "severity_score": 75,
        "yield_loss_risk": "40% to 70% reduction in marketable grade fruit due to cracking and deformities.",
        "damage_symptoms": (
            "Dull olive-green to velvety brown-black circular spots appear on leaves and fruit. "
            "Lesions develop indistinct margins, becoming raised and corky. Heavily infected leaves turn yellow "
            "and drop prematurely. On fruit, spots turn into dark, scabby, corky craters that crack open, "
            "allowing secondary rot pathogens to enter."
        ),
        "favorable_conditions": "Cool, wet spring weather (13°C–24°C) with persistent leaf wetness for 9–18 hours.",
        "chemical_control": [
            {
                "product": "Difenoconazole 25% EC",
                "dosage_per_liter": "0.5 ml / liter",
                "dosage_per_acre": "100 ml in 200 L water / acre",
                "application_type": "Systemic curative fungicide",
                "spray_interval": "10–14 days",
                "pre_harvest_interval_days": 14,
                "notes": "96-hour post-infection reach-back activity."
            },
            {
                "product": "Captan 50% WP",
                "dosage_per_liter": "2.5 g / liter",
                "dosage_per_acre": "500 g in 200 L water / acre",
                "application_type": "Broad-spectrum contact protective spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 14,
                "notes": "Excellent multi-site protectant."
            }
        ],
        "organic_control": [
            {
                "name": "Lime Sulfur Solution (2–3%)",
                "dosage": "20–30 ml / liter during green tip / dormant stage",
                "timing": "Early spring dormant / green tip",
                "mechanism": "Destroys overwintering perithecia in fallen leaf litter."
            }
        ],
        "cultural_ipm": [
            "Rake, shred, or apply 5% urea spray to fallen autumn apple leaves to accelerate decomposition of overwintering fungi.",
            "Prune tree canopy with open-center or central-leader framework for maximum sunlight and airflow."
        ],
        "differential_diagnosis": "Differentiate from Cedar Apple Rust: Scab forms dark olive-green velvety spots; rust forms bright yellow-orange spots with cups."
    },

    "Apple___healthy": {
        "crop": "Apple",
        "common_name": "Healthy Apple Tree Foliage",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0%",
        "damage_symptoms": "Clean, smooth, glossy green leaves and developing fruit free of scabs, lesions, or powdery coats.",
        "favorable_conditions": "Cool temperate climates with adequate winter chilling hours (>800 hrs below 7°C).",
        "chemical_control": [],
        "organic_control": [],
        "cultural_ipm": [
            "Perform winter pruning for canopy illumination.",
            "Thin excess fruitlets at marble stage to ensure uniform fruit size."
        ],
        "differential_diagnosis": "No symptoms detected."
    },

    # ── Indian Field Crops (Soybean, Cotton, Chilli, Chickpea) ──
    "Soybean___healthy": {
        "crop": "Soybean",
        "common_name": "Healthy Soybean Crop",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0%",
        "damage_symptoms": "Broad, vibrant trifoliate green leaves with sturdy stems and no rust pustules, yellow mosaic, or pod blight.",
        "favorable_conditions": "Warm temperatures (25°C–32°C), well-drained loamy soil, adequate moisture during flowering and pod fill.",
        "chemical_control": [],
        "organic_control": [],
        "cultural_ipm": [
            "Ensure seed treatment with Bradyrhizobium japonicum and Trichoderma at sowing.",
            "Maintain weed-free field for the critical first 45 days.",
            "Scout for girdle beetle (Obereopsis brevis) and spodoptera caterpillars."
        ],
        "differential_diagnosis": "No symptoms detected."
    },

    "Soybean___Rust": {
        "crop": "Soybean",
        "common_name": "Asian Soybean Rust",
        "pathogen_type": "Fungal",
        "causal_agent": "Phakopsora pachyrhizi",
        "severity_level": "Critical",
        "severity_score": 90,
        "yield_loss_risk": "40% to 80% yield loss; rapid defoliation during pod filling causes empty pods and shriveled seeds.",
        "damage_symptoms": (
            "Tiny, water-soaked spots appear on lower leaves, rapidly turning into polygonal brown to reddish-brown "
            "lesions delimited by veins. On the underside of leaves, small cone-shaped raised pustules (uredinia) "
            "erupt, releasing tan powdery spores. Leaves turn golden brown, dry out, and drop prematurely. "
            "Fields take on a scorched brown appearance."
        ),
        "favorable_conditions": "Moderate temperatures (18°C–26°C), prolonged leaf wetness (>6 hours), and cloud cover.",
        "chemical_control": [
            {
                "product": "Hexaconazole 5% EC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic triazole fungicide",
                "spray_interval": "10–14 days",
                "pre_harvest_interval_days": 15,
                "notes": "Apply at first sign of rust pustules on lower canopy."
            },
            {
                "product": "Tebuconazole 25.9% EC",
                "dosage_per_liter": "1.0 ml / liter",
                "dosage_per_acre": "200 ml in 200 L water / acre",
                "application_type": "Systemic curative spray",
                "spray_interval": "12–14 days",
                "pre_harvest_interval_days": 15,
                "notes": "Arrests mycelial expansion inside leaf tissue."
            }
        ],
        "organic_control": [
            {
                "name": "Wettable Sulfur 80% WDG",
                "dosage": "3.0 g / liter",
                "timing": "Preventative spray at flowering stage",
                "mechanism": "Sulfur vapor disrupts rust spore respiration."
            }
        ],
        "cultural_ipm": [
            "Plant early-maturing rust-tolerant soybean cultivars (e.g., Phule Kalyani / DSb 21).",
            "Avoid excessive plant densities that trap humidity in the canopy.",
            "Rotate crops with non-leguminous cereals (maize, jowar)."
        ],
        "differential_diagnosis": "Differentiate from Bacterial Pustule: Rust pustules have raised volcanoid pores releasing tan spores without a broad yellow halo."
    },

    "Pepper,_bell___Bacterial_spot": {
        "crop": "Pepper / Chilli",
        "common_name": "Bacterial Spot of Pepper",
        "pathogen_type": "Bacterial",
        "causal_agent": "Xanthomonas campestris pv. vesicatoria",
        "severity_level": "High",
        "severity_score": 75,
        "yield_loss_risk": "30% to 50% loss due to severe defoliation and fruit spotting.",
        "damage_symptoms": (
            "Small, circular-to-irregular water-soaked dark spots appear on leaves. Spots turn brown with dark "
            "greasy margins. Leaves yellow and drop rapidly. On green peppers/chillies, raised blister-like "
            "warty spots develop with rough, cracked brown crusts."
        ),
        "favorable_conditions": "Warm temperatures (24°C–32°C), high humidity, and driving rains.",
        "chemical_control": [
            {
                "product": "Copper Oxychloride 50% WP + Streptocycline",
                "dosage_per_liter": "2.5 g COC + 0.1 g Streptocycline per liter",
                "dosage_per_acre": "500 g COC + 20 g Streptocycline in 200 L water / acre",
                "application_type": "Contact bactericide spray",
                "spray_interval": "7–10 days",
                "pre_harvest_interval_days": 7,
                "notes": "Covers both leaf surfaces."
            }
        ],
        "organic_control": [
            {
                "name": "Pseudomonas fluorescens (1% WP)",
                "dosage": "5.0 g / liter",
                "timing": "Every 14 days",
                "mechanism": "Induced systemic resistance against bacterial invasion."
            }
        ],
        "cultural_ipm": [
            "Hot water treatment of seeds (50°C for 25 min) before sowing.",
            "Use drip irrigation instead of furrow/overhead watering.",
            "Rotate out of solanaceous crops for 2 years."
        ],
        "differential_diagnosis": "Differentiate from Cercospora leaf spot: Bacterial spots are smaller, greasy, and have rough warty fruit lesions."
    },

    "Pepper,_bell___healthy": {
        "crop": "Pepper / Chilli",
        "common_name": "Healthy Pepper Foliage",
        "pathogen_type": "None (Healthy)",
        "causal_agent": "None",
        "severity_level": "None",
        "severity_score": 0,
        "yield_loss_risk": "0%",
        "damage_symptoms": "Clean, smooth, dark green leaves with active flowering and firm, glossy, unblemished fruit set.",
        "favorable_conditions": "Well-drained sandy-loam soil, temperatures 20°C–30°C.",
        "chemical_control": [],
        "organic_control": [],
        "cultural_ipm": [
            "Stake plants to support heavy fruit load.",
            "Scout weekly for thrips and mites on growing tips."
        ],
        "differential_diagnosis": "No symptoms detected."
    }
}


# Default generic fallback for unlisted or newly added classes
GENERIC_DISEASE_TEMPLATE: Dict[str, Any] = {
    "crop": "Crop",
    "common_name": "Plant Pathogen Symptom",
    "pathogen_type": "Fungal / Microbial",
    "causal_agent": "Plant pathogen complex",
    "severity_level": "Moderate",
    "severity_score": 50,
    "yield_loss_risk": "15% to 35% yield reduction depending on stage of infection and canopy coverage.",
    "damage_symptoms": (
        "Visible leaf lesions, discoloration, necrotic spots, or wilting. "
        "Foliar symptoms impair photosynthetic efficiency and can cause premature leaf drop if not addressed."
    ),
    "favorable_conditions": "High relative humidity, prolonged leaf wetness, and dense canopies with poor ventilation.",
    "chemical_control": [
        {
            "product": "Mancozeb 75% WP",
            "dosage_per_liter": "2.5 g / liter",
            "dosage_per_acre": "500 g in 200 L water / acre",
            "application_type": "Broad-spectrum contact protective spray",
            "spray_interval": "7–10 days",
            "pre_harvest_interval_days": 7,
            "notes": "Provides broad multi-site protective barrier on healthy foliage."
        },
        {
            "product": "Copper Oxychloride 50% WP",
            "dosage_per_liter": "2.5 g / liter",
            "dosage_per_acre": "500 g in 200 L water / acre",
            "application_type": "Contact fungicide / bactericide",
            "spray_interval": "10 days",
            "pre_harvest_interval_days": 7,
            "notes": "Effective across broad fungal and bacterial leaf spots."
        }
    ],
    "organic_control": [
        {
            "name": "Trichoderma viride / harzianum (2x10^9 CFU/g)",
            "dosage": "5.0 g / liter foliar spray",
            "timing": "At first symptom detection",
            "mechanism": "Competitive colonization and mycoparasitism."
        },
        {
            "name": "Cold-Pressed Neem Oil (10,000 ppm)",
            "dosage": "3.0 ml / liter with mild liquid soap",
            "timing": "Weekly spray",
            "mechanism": "Natural broad-spectrum antifungal and insect repellent."
        }
    ],
    "cultural_ipm": [
        "Prune and destroy infected plant foliage; do not leave infected debris on the field floor.",
        "Ensure proper plant spacing to facilitate rapid wind drying of foliage.",
        "Avoid overhead irrigation; water at the root zone via drip lines.",
        "Practice crop rotation with non-host species for at least 2 seasons."
    ],
    "differential_diagnosis": "Consult your local Krishi Vigyan Kendra (KVK) officer for laboratory slide verification."
}


def normalize_label(label: str) -> str:
    """Normalizes label string to match knowledge base keys."""
    # Handle model label quirks:
    # 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot' -> 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot'
    # Also support aliases
    l = label.strip()
    if l in DISEASE_KNOWLEDGE_BASE:
        return l

    # Try mapping aliases
    aliases = {
        "Corn___Cercospora_leaf_spot_Gray_leaf_spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
        "Corn___Common_rust": "Corn_(maize)___Common_rust_",
        "Corn___Northern_Leaf_Blight": "Corn_(maize)___Northern_Leaf_Blight",
        "Corn___healthy": "Corn_(maize)___healthy",
        "Cherry___Powdery_mildew": "Cherry_(including_sour)___Powdery_mildew",
        "Cherry___healthy": "Cherry_(including_sour)___healthy",
        "Tomato___Spider_mites_Two-spotted_spider_mite": "Tomato___Spider_mites Two-spotted_spider_mite",
    }
    if l in aliases and aliases[l] in DISEASE_KNOWLEDGE_BASE:
        return aliases[l]

    # Inverse alias check
    inv_aliases = {v: k for k, v in aliases.items()}
    if l in inv_aliases and inv_aliases[l] in DISEASE_KNOWLEDGE_BASE:
        return inv_aliases[l]

    return l


def get_detailed_disease_insight(label: str) -> Dict[str, Any]:
    """Returns rich structured pathology insights for a given disease label."""
    norm_key = normalize_label(label)
    if norm_key in DISEASE_KNOWLEDGE_BASE:
        return DISEASE_KNOWLEDGE_BASE[norm_key]

    # Build smart dynamic fallback based on crop and disease tokens
    crop, _, disease = label.partition("___")
    crop_clean = crop.replace("_", " ").strip() if crop else "Crop"
    disease_clean = disease.replace("_", " ").strip() if disease else label
    is_healthy = "healthy" in label.lower()

    if is_healthy:
        return {
            "crop": crop_clean,
            "common_name": f"Healthy {crop_clean} Foliage",
            "pathogen_type": "None (Healthy)",
            "causal_agent": "None",
            "severity_level": "None",
            "severity_score": 0,
            "yield_loss_risk": "0%",
            "damage_symptoms": f"Healthy, vibrant {crop_clean} foliage with clean leaf margins, turgid leaves, and no visual lesions.",
            "favorable_conditions": "Optimal growth conditions with balanced nutrition and proper moisture.",
            "chemical_control": [],
            "organic_control": [
                {
                    "name": "Preventive Bio-agent (Trichoderma viride)",
                    "dosage": "5.0 g / liter",
                    "timing": "Monthly preventive foliar spray",
                    "mechanism": "Natural phylloplane protection against fungal spore settlement."
                }
            ],
            "cultural_ipm": [
                "Maintain balanced N-P-K nutrition according to soil test recommendations.",
                "Scout fields weekly for early pest and disease symptoms.",
                "Ensure proper irrigation drainage to prevent waterlogging."
            ],
            "differential_diagnosis": "No symptoms detected."
        }

    # Generate custom structured entry from generic template
    entry = dict(GENERIC_DISEASE_TEMPLATE)
    entry["crop"] = crop_clean
    entry["common_name"] = disease_clean
    entry["damage_symptoms"] = (
        f"Symptoms of {disease_clean} on {crop_clean} leaves. "
        "Foliar lesions or chlorotic spots interfere with photosynthesis and can cause premature leaf loss."
    )
    return entry


def get_all_supported_diseases() -> List[Dict[str, Any]]:
    """Returns a catalogue of all supported crop diseases with preview summaries."""
    items = []
    for key, data in DISEASE_KNOWLEDGE_BASE.items():
        crop, _, disease = key.partition("___")
        items.append({
            "key": key,
            "crop": data.get("crop", crop.replace("_", " ")),
            "common_name": data.get("common_name", disease.replace("_", " ")),
            "pathogen_type": data.get("pathogen_type", "Unknown"),
            "severity_level": data.get("severity_level", "Moderate"),
            "yield_loss_risk": data.get("yield_loss_risk", "Moderate"),
            "is_healthy": "healthy" in key.lower()
        })
    return items
