"""
Jerusalem Meal Planner — Local Web App
Run: python app.py
Then open http://localhost:5000 (or your local IP on iPhone)
"""

import os, json, random, datetime, socket
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests as req_lib
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

app = Flask(__name__)
app.secret_key = os.urandom(24)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # allow http for localhost

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

# ─── ICLOUD REMINDERS CONFIG ───────────────────────────────────────────────
# Generate an app-specific password at appleid.apple.com
#   -> Sign-In and Security -> App-Specific Passwords
# Use your iCloud email as ICLOUD_USER.
ICLOUD_USER     = ""   # e.g. "elliot@icloud.com"
ICLOUD_PASSWORD = ""   # app-specific password e.g. "xxxx-xxxx-xxxx-xxxx"
ICLOUD_SERVER   = ""  # your per-account server
REMINDERS_LIST  = "Meal Planner"

# ─── RECIPE DATABASE ───────────────────────────────────────────────────────────

RECIPES = {
    # ── PLANT-BASED ──────────────────────────────────────────────────────────────
    "mejadra": {
        "name": "Mejadra",
        "type": "plant",
        "kcal": 440, "protein": 13, "cook_mins": 45,
        "desc": "Lentil & caramelised onion rice — a complete one-bowl meal with yogurt",
        "batch": True, "quick": False,
        "veg_side": "None",
        "carb_side": None,
        "ingredients": [
            "1¼ cups / 250g green or brown lentils", "4 medium onions (700g)",
            "3 tbsp plain flour", "~1 cup / 250ml sunflower oil",
            "2 tsp cumin seeds", "1½ tbsp coriander seeds",
            "1 cup / 200g basmati rice", "2 tbsp olive oil",
            "½ tsp ground turmeric", "1½ tsp ground allspice",
            "1½ tsp ground cinnamon", "1 tsp sugar",
            "1½ cups / 350ml water", "Salt & black pepper",
            "Greek yogurt, to serve"
        ],
        "method": [
            "Boil lentils in plenty of water for 12–15 min until just softened but with bite. Drain.",
            "Thinly slice onions. Toss with flour and 1 tsp salt. Fry in batches in hot sunflower oil over medium-high heat, 5–7 min per batch until golden and crispy. Drain on paper towels.",
            "In the same pan, toast cumin and coriander seeds 1–2 min. Add rice, olive oil, turmeric, allspice, cinnamon, sugar, ½ tsp salt and pepper. Stir, add lentils and water. Boil, cover, simmer very low 15 min.",
            "Remove from heat. Cover with a tea towel then lid and rest 10 min. Fold through half the crispy onion, pile into bowls, top with the rest and a spoonful of Greek yogurt."
        ],
        "tip": "Batch cook a big pot on Sunday — lasts 4 days. The best comfort food in the book. Air fryer: toss floured onion with 1 tbsp oil instead of 250ml — air fry at 200°C for 10–12 min, shaking halfway, until dark and crispy.",
        "shopping": ["green lentils (250g)", "onions (x4)", "plain flour", "sunflower oil",
                     "cumin seeds", "coriander seeds", "basmati rice", "turmeric",
                     "ground allspice", "ground cinnamon", "Greek yogurt"]
    },
    "shakshuka": {
        "name": "Shakshuka",
        "type": "plant",
        "kcal": 420, "protein": 22, "cook_mins": 25,
        "desc": "Eggs baked in spiced tomato & red pepper sauce — serve with good bread",
        "batch": False, "quick": True,
        "veg_side": "Simple green salad — cucumber, mint, olive oil & lemon",
        "carb_side": "Extra sourdough or pitta bread",
        "ingredients": [
            "2 tbsp olive oil", "2 tbsp harissa or pilpelchuma",
            "2 tsp tomato paste", "2 large red peppers, ¼-inch dice",
            "4 cloves garlic, finely chopped", "1 tsp ground cumin",
            "5 large ripe tomatoes, chopped (or 1 tin)", "4 large free-range eggs, plus 4 egg yolks",
            "½ cup / 120g labneh or thick yogurt",
            "Salt", "Good crusty bread, to serve"
        ],
        "method": [
            "Heat olive oil over medium. Add harissa, tomato paste, peppers, garlic, cumin, ¾ tsp salt. Cook 8 min until peppers soften.",
            "Add tomatoes, simmer 10 min until thick. Taste and season.",
            "Make 8 dips in the sauce. Gently break each egg and yolk into its own dip. Swirl the whites lightly with a fork, taking care not to break the yolks. Simmer gently for 8 to 10 minutes, until the whites are set but the yolks still runny. Cover with a lid to speed this up if you like.",
            "Rest 2 min. Spoon into bowls, dollop with labneh or yogurt. Eat immediately with plenty of bread."
        ],
        "tip": "25 mins start to finish. Double the sauce and freeze half — then dinner is 10 mins.",
        "shopping": ["harissa paste", "red peppers (x2)", "garlic", "tomatoes (x5 or 1 tin)",
                     "eggs (x6)", "labneh or thick yogurt", "tomato paste", "crusty bread"]
    },
    "chermoula_eggplant": {
        "name": "Chermoula Eggplant with Bulgur & Yogurt",
        "type": "plant",
        "kcal": 700, "protein": 20, "cook_mins": 50,
        "desc": "Roasted aubergine in a North African spice paste over a herbed bulgur salad — a full vegetarian meal",
        "batch": False, "quick": False,
        "veg_side": "None",
        "carb_side": None,
        "ingredients": [
            "2 medium aubergines", "2 cloves garlic, crushed",
            "2 tsp ground cumin", "2 tsp ground coriander",
            "1 tsp chilli flakes", "1 tsp sweet paprika",
            "2 tbsp preserved lemon peel, finely chopped",
            "⅔ cup / 140ml olive oil, plus extra to finish",
            "1 cup / 150g fine bulgur", "⅔ cup / 140ml boiling water",
            "⅓ cup / 50g golden raisins", "3½ tbsp / 50ml warm water",
            "10g fresh coriander, chopped", "10g fresh mint, chopped",
            "⅓ cup / 50g pitted green olives, halved",
            "⅓ cup / 30g sliced almonds, toasted",
            "3 spring onions, chopped", "1½ tbsp lemon juice",
            "½ cup / 120g Greek yogurt", "Salt"
        ],
        "method": [
            "Preheat oven to 200°C. Make chermoula: mix garlic, cumin, ground coriander, chilli, paprika, preserved lemon, ⅔ of the oil, and ½ tsp salt.",
            "Halve aubergines lengthwise. Score flesh deeply in a crisscross without piercing skin. Spoon chermoula over each half. Roast cut-side up 40 min until completely soft.",
            "Pour boiling water over bulgur in a bowl. Soak raisins in warm water 10 min, drain. Add raisins and remaining oil to bulgur. Stir in herbs, olives, almonds, spring onions, lemon juice, and salt.",
            "Place one aubergine half per plate, spoon bulgur on top, add a generous dollop of yogurt, scatter more coriander, drizzle oil."
        ],
        "tip": "Roasting is entirely hands-off — use the 40 min to prep the bulgur and do other things.",
        "shopping": ["aubergines (x2)", "preserved lemon", "fine bulgur (150g)", "golden raisins",
                     "green olives", "sliced almonds", "fresh mint", "fresh coriander", "spring onions"]
    },
    "conchiglie": {
        "name": "Conchiglie with Yogurt, Peas & Chilli",
        "type": "plant",
        "kcal": 850, "protein": 35, "cook_mins": 25,
        "desc": "Shell pasta in a garlicky yogurt sauce with sweet peas, feta and a chilli-toasted pine nut oil",
        "batch": False, "quick": True,
        "veg_side": "None",
        "carb_side": None,
        "ingredients": [
            "500g conchiglie pasta", "500g Greek yogurt",
            "⅔ cup / 150ml olive oil", "4 cloves garlic, crushed",
            "500g fresh or frozen peas", "60g pine nuts",
            "2 tsp chilli flakes (Turkish/Aleppo if possible)",
            "40g fresh basil leaves, torn",
            "240g feta, broken into chunks",
            "Salt & white pepper"
        ],
        "method": [
            "Blitz yogurt, 6 tbsp olive oil, garlic, and 100g peas in a food processor to a pale green sauce. Transfer to a large bowl.",
            "Cook pasta in plenty of salted boiling water until al dente. Meanwhile, fry pine nuts and chilli flakes in remaining olive oil over medium heat for 4 min until nuts are golden and oil is deep red.",
            "Heat remaining peas in boiling water, drain. Drain pasta and add gradually to the yogurt sauce (adding all at once may split the yogurt). Add warm peas, basil, feta, 1 tsp salt, ½ tsp white pepper.",
            "Toss gently. Divide into bowls and drizzle the chilli pine nut oil over the top. Serve immediately."
        ],
        "tip": "Ready in 25 min. Use the best quality chilli flakes you can find — Aleppo or Urfa from Middle Eastern shops are worth it.",
        "shopping": ["conchiglie pasta (500g)", "Greek yogurt (500g)", "frozen peas (500g)",
                     "pine nuts (60g)", "Aleppo or Turkish chilli flakes", "fresh basil", "feta (240g)"]
    },
    "barley_risotto": {
        "name": "Barley Risotto with Marinated Feta",
        "type": "plant",
        "kcal": 750, "protein": 24, "cook_mins": 55,
        "desc": "Slow-cooked pearl barley in a rich tomato herb sauce, topped with tangy marinated feta",
        "batch": True, "quick": False,
        "veg_side": "None",
        "carb_side": None,
        "ingredients": [
            "1 cup / 200g pearl barley", "2 tbsp / 30g unsalted butter",
            "6 tbsp / 90ml olive oil", "2 small celery stalks, finely diced",
            "2 small shallots, finely diced", "4 cloves garlic, very finely diced",
            "4 thyme sprigs", "½ tsp smoked paprika", "1 bay leaf",
            "4 strips lemon peel", "¼ tsp chilli flakes",
            "1 tin (400g) chopped tomatoes", "700ml vegetable stock",
            "300ml passata", "1 tbsp caraway seeds",
            "300g feta, broken into chunks",
            "1 tbsp fresh oregano leaves", "Salt"
        ],
        "method": [
            "Rinse pearl barley under cold water and drain well.",
            "Melt butter and 2 tbsp oil in a very large frying pan. Cook celery, shallots, and garlic gently 5 min until soft.",
            "Add barley, thyme, paprika, bay leaf, lemon peel, chilli, tomatoes, stock, passata, and ½ tsp salt. Stir, bring to boil, then simmer very gently 45 min, stirring frequently, until barley is tender and liquid mostly absorbed.",
            "Toast caraway seeds in a dry pan 2 min, lightly crush. Mix with feta and remaining 4 tbsp olive oil. Divide risotto into bowls and top with the marinated feta and oregano."
        ],
        "tip": "Unlike proper risotto you can walk away from it. Leftovers are excellent cold or reheated for lunch.",
        "shopping": ["pearl barley (200g)", "celery", "shallots", "thyme", "smoked paprika",
                     "tinned chopped tomatoes", "vegetable stock", "passata",
                     "caraway seeds", "feta (300g)", "fresh oregano"]
    },
    # ── FISH ─────────────────────────────────────────────────────────────────────
    "salmon_chraimeh": {
        "name": "Salmon in Chraimeh Sauce",
        "type": "fish",
        "kcal": 680, "protein": 44, "cook_mins": 35,
        "desc": "Salmon steaks in a bold Libyan-Jewish spiced tomato sauce — serve with couscous or rice",
        "batch": False, "quick": False,
        "veg_side": "Steamed green beans or wilted spinach with garlic & olive oil",
        "carb_side": "Plain basmati rice or couscous",
        "ingredients": [
            "4 salmon steaks (~950g total)", "scant ½ cup / 110ml sunflower oil",
            "3 tbsp plain flour", "6 cloves garlic, chopped",
            "2 tsp sweet paprika", "1 tbsp caraway seeds, toasted & ground",
            "1½ tsp ground cumin", "¼ tsp cayenne pepper",
            "¼ tsp ground cinnamon", "1 green chilli, chopped",
            "⅔ cup / 150ml water", "3 tbsp tomato paste",
            "2 tsp sugar", "1 lemon (wedges + 2 tbsp juice)",
            "2 tbsp fresh coriander, chopped", "Salt & black pepper",
            "Couscous or rice, to serve"
        ],
        "method": [
            "Heat 2 tbsp oil in a large lidded frying pan. Season flour with salt and pepper, coat salmon, shake off excess. Sear 1–2 min per side until golden. Remove and wipe pan.",
            "Blitz garlic, all spices, chilli, and 2 tbsp oil in a food processor to a thick paste.",
            "Heat remaining oil, add spice paste, fry 30 seconds. Immediately add water and tomato paste. Simmer, then add sugar, lemon juice, ¾ tsp salt and pepper.",
            "Return salmon to pan, cover, cook 7–11 min until just done. Serve with couscous or rice, garnished with coriander and lemon wedges."
        ],
        "tip": "The sauce can be made ahead — just drop the salmon in when you get home. Reheats perfectly.",
        "shopping": ["salmon steaks (x4, ~950g)", "caraway seeds", "sweet paprika", "cayenne pepper",
                     "green chilli", "tomato paste", "fresh coriander", "lemons", "couscous or rice"]
    },
    "sea_bass": {
        "name": "Panfried Sea Bass with Harissa & Rose",
        "type": "fish",
        "kcal": 380, "protein": 22, "cook_mins": 30,
        "desc": "Crispy sea bass in a sweet-spicy harissa and rose sauce — serve over rice or couscous",
        "batch": False, "quick": True,
        "veg_side": "Roasted courgettes with olive oil, lemon zest & fresh herbs",
        "carb_side": "Warm pitta bread or steamed basmati rice",
        "ingredients": [
            "4 sea bass fillets (~450g), skinned", "3 tbsp harissa paste",
            "1 tsp ground cumin", "Plain flour for dusting",
            "2 tbsp olive oil", "2 medium onions, finely chopped",
            "6½ tbsp / 100ml red wine vinegar", "1 tsp ground cinnamon",
            "scant 1 cup / 200ml water", "1½ tbsp honey",
            "1 tbsp rose water", "scant ½ cup / 60g currants (optional)",
            "2 tsp dried edible rose petals", "Salt & black pepper",
            "Rice or couscous, to serve"
        ],
        "method": [
            "Mix half the harissa with cumin and ½ tsp salt. Rub over fish. Marinate 30 min (or up to 2 hrs in the fridge).",
            "Dust fillets with flour. Heat oil over medium-high and fry 2 min per side. Set fish aside, keep oil in pan.",
            "Cook onions in same pan ~8 min until golden. Add remaining harissa, vinegar, cinnamon, ½ tsp salt, pepper. Pour in water and simmer 10–15 min until thick. Add honey, rose water, and currants.",
            "Return fish to pan, spoon sauce over, warm 3 min. Serve over rice or couscous, scattered with rose petals."
        ],
        "tip": "Marinate in the morning — dinner is then just 20 min of cooking. Stunning dish. Air fryer: air fry the dusted fillets at 200°C for 6–8 min instead of pan-frying.",
        "shopping": ["sea bass fillets (x4)", "harissa paste", "red wine vinegar", "honey",
                     "rose water", "dried edible rose petals", "currants", "onions (x2)", "rice or couscous"]
    },
    "mackerel": {
        "name": "Mackerel with Golden Beet & Orange Salsa",
        "type": "fish",
        "kcal": 520, "protein": 30, "cook_mins": 30,
        "desc": "Crispy mackerel fillets with a vibrant citrus and beet relish — serve over basmati rice",
        "batch": False, "quick": True,
        "veg_side": "Steamed tenderstem broccoli with a squeeze of lemon",
        "carb_side": "Basmati rice",
        "ingredients": [
            "4 mackerel fillets (~260g), skin on", "1 tbsp harissa paste",
            "1 tsp ground cumin", "1 medium golden beet",
            "1 medium orange", "1 small lemon",
            "¼ cup / 30g Kalamata olives, quartered", "½ small red onion, finely chopped",
            "¼ cup / 15g flat-leaf parsley, chopped",
            "½ tsp coriander seeds, toasted & crushed",
            "¾ tsp cumin seeds, toasted & crushed",
            "½ tsp sweet paprika", "½ tsp chilli flakes",
            "1 tbsp hazelnut or walnut oil", "Salt",
            "Basmati rice, to serve"
        ],
        "method": [
            "Mix harissa, ground cumin, and a pinch of salt. Rub over mackerel and refrigerate until needed. Cook basmati rice according to packet instructions.",
            "Boil golden beet ~20 min until tender. Cool, peel, dice to ¼ inch. Mix with orange segments, lemon juice, olives, red onion, parsley, all crushed seeds, paprika, chilli, and both oils. Toss gently.",
            "Cook mackerel skin-side down in a hot dry frying pan 2–3 min until the skin is crispy, then flip for 1 min.",
            "Serve mackerel over the rice with the salsa spooned alongside and on top."
        ],
        "tip": "The salsa can be made a day ahead. Rice cooks while the beet boils — everything aligns perfectly. Air fryer: air fry mackerel skin-side up at 200°C for 6–8 min — the skin crisps well without added oil.",
        "shopping": ["mackerel fillets (x4)", "golden beet (x1)", "orange (x1)", "Kalamata olives",
                     "red onion", "flat-leaf parsley", "hazelnut or walnut oil", "coriander seeds", "basmati rice"]
    },
    "fish_kebabs": {
        "name": "Fish & Caper Kebabs with Burnt Eggplant",
        "type": "fish",
        "kcal": 520, "protein": 35, "cook_mins": 45,
        "desc": "Herbed white fish patties on smoky aubergine — serve with pitta or flatbread",
        "batch": False, "quick": False,
        "veg_side": "Sliced tomato & cucumber salad with olive oil, sumac & mint",
        "carb_side": "Warm pitta bread",
        "ingredients": [
            "400g haddock or white fish fillets, skinned", "½ cup / 30g fresh breadcrumbs",
            "½ large egg, beaten", "2½ tbsp / 20g capers, chopped",
            "20g dill, chopped", "2 spring onions, finely chopped",
            "Zest of 1 lemon + 1 tbsp lemon juice",
            "¾ tsp ground cumin", "½ tsp ground turmeric",
            "2 medium aubergines (~750g)", "2 tbsp Greek yogurt",
            "1 garlic clove, crushed", "2 tbsp flat-leaf parsley, chopped",
            "2 tbsp sunflower oil", "2 tsp pickled lemon",
            "Pitta or flatbread, to serve", "Salt & black pepper"
        ],
        "method": [
            "Char aubergines directly over a gas flame or under a hot grill, turning, until completely blackened (~20 min). Peel, drain 20 min in a colander, chop. Mix with yogurt, garlic, parsley, 1 tsp salt, black pepper.",
            "Slice fish very thin (~2mm) then dice finely. Mix with breadcrumbs, egg, capers, dill, spring onions, lemon zest and juice, cumin, turmeric, ½ tsp salt, white pepper.",
            "Dampen hands and shape into 12 patties. Refrigerate 20 min if time allows.",
            "Fry in sunflower oil over medium-high, 2–3 min per side until golden. Serve on the smoky aubergine with pickled lemon and warm pitta."
        ],
        "tip": "Shape patties the night before and refrigerate — frying takes just 10 min when you get home. Air fryer: spray patties with oil and air fry at 190°C for 8–10 min, flipping once.",
        "shopping": ["haddock or white fish (400g)", "fresh breadcrumbs", "capers", "fresh dill",
                     "spring onions", "aubergines (x2)", "pickled lemon", "pitta breads"]
    },
    "salmon_quick": {
        "name": "Grilled Salmon with Zhoug & Tabbouleh",
        "type": "fish",
        "kcal": 680, "protein": 48, "cook_mins": 20,
        "desc": "Simply grilled salmon with fiery Yemeni herb sauce alongside a quick bulgur tabbouleh",
        "batch": False, "quick": True,
        "veg_side": "None",
        "carb_side": None,
        "ingredients": [
            "4 salmon fillets (~600g), skin on",
            "2 tbsp olive oil", "1 tsp ground cumin", "½ tsp sweet paprika",
            "1 lemon, cut into wedges", "Salt & black pepper",
            "ZHOUG: 3 green chillies, roughly chopped", "4 cloves garlic",
            "1 tsp ground cumin", "½ tsp ground coriander", "½ tsp ground cardamom",
            "40g fresh coriander (leaves & stems)", "40g flat-leaf parsley",
            "4 tbsp olive oil", "2 tbsp lemon juice",
            "QUICK TABBOULEH: 150g fine bulgur", "boiling water to cover",
            "3 tomatoes, diced", "½ cucumber, diced",
            "large handful flat-leaf parsley, chopped", "juice of 1 lemon", "2 tbsp olive oil"
        ],
        "method": [
            "Make zhoug: blitz chillies, garlic, spices, herbs, oil, and lemon juice in a food processor to a vivid green sauce. Season and set aside.",
            "Pour boiling water over bulgur, cover and leave 10 min. Fluff with a fork, mix through tomatoes, cucumber, parsley, lemon juice, olive oil, salt and pepper.",
            "Rub salmon with olive oil, cumin, paprika, salt, and pepper. Heat a griddle or frying pan over high heat. Cook skin-side down 3–4 min until crispy. Flip and cook 2 min more.",
            "Serve salmon over the tabbouleh with a generous spoonful of zhoug and lemon wedges."
        ],
        "tip": "Zhoug keeps refrigerated for a week — make a big batch. The whole meal is ready in 20 min.",
        "shopping": ["salmon fillets (x4, ~600g)", "green chillies (x3)", "fresh coriander (80g)",
                     "flat-leaf parsley (large bunch)", "ground cardamom", "fine bulgur (150g)",
                     "tomatoes (x3)", "cucumber", "lemons (x2)"]
    },
    # ── MEAT ─────────────────────────────────────────────────────────────────────
    "cannellini_lamb": {
        "name": "Cannellini Bean & Lamb Soup",
        "type": "meat",
        "kcal": 720, "protein": 42, "cook_mins": 90,
        "desc": "Hearty one-pot with white beans, tender lamb, whole garlic cloves and potato — serve with bread",
        "batch": True, "quick": False,
        "veg_side": "Steamed cavolo nero or kale with olive oil & garlic",
        "carb_side": "Crusty bread or flatbread",
        "ingredients": [
            "1 tbsp sunflower oil", "1 small onion, finely chopped",
            "¼ celery root, ¼-inch dice (~170g)", "20 large garlic cloves, peeled and whole",
            "1 tsp ground cumin", "500g lamb stew meat, 2cm cubes",
            "7 cups / 1.75 litres water",
            "½ cup / 100g dried cannellini beans (soaked overnight)",
            "7 cardamom pods, lightly crushed", "½ tsp ground turmeric",
            "2 tbsp tomato paste", "1 tsp sugar",
            "250g yellow potato, cubed", "Salt & black pepper",
            "Lemon wedges, fresh coriander, crusty bread to serve"
        ],
        "method": [
            "Fry onion and celery root in oil over medium-high heat 5 min until starting to colour. Add whole garlic cloves and cumin, cook 2 min more. Set aside.",
            "Place lamb and water in a large pot. Boil, then skim frequently for 10 min until you have a clear broth.",
            "Add onion mixture, drained beans, cardamom, turmeric, tomato paste, and sugar. Boil, cover, simmer 1 hour until lamb is tender.",
            "Add potatoes, season with 1 tsp salt and ½ tsp pepper. Simmer uncovered 20 min until beans and potatoes are soft. Serve with bread, lemon juice, fresh coriander."
        ],
        "tip": "Soak beans the night before. Makes a huge pot — Wednesday dinner becomes Thursday lunch.",
        "shopping": ["lamb stew meat (500g)", "dried cannellini beans (100g, soak overnight)",
                     "celery root", "garlic (20 cloves)", "cardamom pods", "turmeric",
                     "yellow potatoes (250g)", "fresh coriander", "crusty bread"]
    },
    "lamb_meatballs": {
        "name": "Lamb Meatballs with Barberries, Yogurt & Herbs",
        "type": "meat",
        "kcal": 750, "protein": 44, "cook_mins": 100,
        "desc": "Spiced lamb kofta braised in a rich shallot sauce with tart barberries — serve over rice or couscous",
        "batch": True, "quick": False,
        "veg_side": "Roasted carrots or root vegetables with cumin & olive oil",
        "carb_side": "Basmati rice or couscous",
        "ingredients": [
            "750g ground lamb", "2 medium onions, finely chopped",
            "20g flat-leaf parsley, finely chopped", "3 cloves garlic, crushed",
            "¾ tsp ground allspice", "¾ tsp ground cinnamon",
            "6 tbsp / 60g barberries (or cranberries)", "1 large egg",
            "6½ tbsp / 100ml sunflower oil", "700g banana shallots, peeled",
            "¾ cup + 2 tbsp / 200ml white wine", "2 cups / 500ml chicken stock",
            "2 bay leaves", "2 thyme sprigs", "2 tsp sugar", "150g dried figs",
            "200g Greek yogurt",
            "3 tbsp mixed mint, coriander, dill & tarragon",
            "Salt & black pepper", "Rice or couscous, to serve"
        ],
        "method": [
            "Combine lamb, onions, parsley, garlic, allspice, cinnamon, barberries, egg, 1 tsp salt and ½ tsp pepper. Mix by hand and roll into golf-ball-sized meatballs.",
            "Brown meatballs in batches in ⅓ of the oil. Remove and set aside. Wipe pot clean.",
            "Cook shallots in remaining oil 10 min until golden. Add wine, bubble 2 min. Add stock, bay leaves, thyme, sugar, salt and pepper. Nestle figs and meatballs in the shallots.",
            "Boil, cover, simmer very low 30 min. Uncover, simmer 1 hour more until sauce is rich and reduced. Whisk yogurt, pour over. Scatter with fresh herbs. Serve over rice."
        ],
        "tip": "Make a double batch and freeze half the raw meatballs. Barberries available online or Middle Eastern shops.",
        "shopping": ["ground lamb (750g)", "barberries or dried cranberries", "banana shallots (700g)",
                     "white wine", "chicken stock", "dried figs", "fresh mixed herbs",
                     "rice or couscous"]
    },
    "turkey_burgers": {
        "name": "Turkey & Courgette Burgers with Sumac Yogurt",
        "type": "meat",
        "kcal": 440, "protein": 36, "cook_mins": 30,
        "desc": "Herbed turkey and courgette patties with a sharp, creamy sumac dipping sauce — brilliant for lunch boxes",
        "batch": True, "quick": True,
        "veg_side": "Simple tomato & cucumber chopped salad with za'atar & lemon",
        "carb_side": "Pitta bread",
        "ingredients": [
            "500g ground turkey", "1 large courgette, coarsely grated",
            "3 spring onions, thinly sliced", "1 large egg",
            "2 tbsp chopped fresh mint", "2 tbsp chopped fresh coriander",
            "2 cloves garlic, crushed", "1 tsp ground cumin",
            "½ tsp cayenne pepper", "1 tsp salt", "½ tsp black pepper",
            "~6 tbsp sunflower oil, for frying",
            "SUMAC SAUCE: 100g sour cream", "150g Greek yogurt",
            "1 tsp lemon zest", "1 tbsp lemon juice",
            "1 small garlic clove, crushed", "1½ tbsp olive oil",
            "1 tbsp sumac", "½ tsp salt",
            "Pitta bread or flatbread, to serve"
        ],
        "method": [
            "Mix all sumac sauce ingredients in a bowl. Refrigerate until needed.",
            "Combine turkey, courgette, spring onions, egg, herbs, garlic, cumin, cayenne, salt and pepper. Mix well and shape into 12–15 small patties.",
            "Heat a thin layer of sunflower oil in a large frying pan over medium heat. Sear patties in batches on all sides, ~4 min, until golden brown.",
            "Transfer to a baking tray and finish in a 220°C oven for 5–7 min. Serve in or alongside pitta with sumac sauce."
        ],
        "tip": "Make a big batch — they keep refrigerated for 3 days and are ideal cold in a lunch box. Freeze raw patties for later. Air fryer: cook patties at 190°C for 10–12 min, flipping once — no oil needed.",
        "shopping": ["ground turkey (500g)", "courgette (x1)", "spring onions", "fresh mint",
                     "fresh coriander", "sumac", "sour cream", "pitta breads"]
    },
    # ── CHICKEN ──────────────────────────────────────────────────────────────────
    "chicken_cardamom": {
        "name": "Chicken with Caramelised Onion & Cardamom Rice",
        "type": "meat",
        "kcal": 780, "protein": 52, "cook_mins": 60,
        "desc": "One-pot chicken and spiced basmati rice with deep golden onions and barberries",
        "batch": True, "quick": False,
        "ingredients": [
            "3 tbsp sugar", "3 tbsp water", "2½ tbsp barberries or currants",
            "4 tbsp olive oil", "2 medium onions, thinly sliced",
            "1kg skin-on bone-in chicken thighs",
            "10 cardamom pods", "¼ tsp whole cloves",
            "2 long cinnamon sticks, broken in two",
            "300g basmati rice", "550ml boiling water",
            "Flat-leaf parsley, dill and coriander leaves, chopped",
            "Greek yogurt mixed with olive oil, to serve", "Salt & black pepper"
        ],
        "method": [
            "Dissolve sugar in water over heat, add barberries and set aside to soak.",
            "Heat half the oil in a large lidded sauté pan. Fry onion 10–15 min until deep golden brown. Transfer to a bowl. Wipe pan.",
            "Season chicken with 1½ tsp each salt and pepper. Add remaining oil, cardamom, cloves and cinnamon to chicken. Sear in pan 5 min per side. Remove (spices stay in).",
            "Add rice to pan, stir to coat in spiced oil. Sit chicken on top. Pour in boiling water. Scatter caramelised onion and drained barberries over. Cover tightly, cook over very low heat 30 min. Rest 10 min off heat. Scatter herbs and serve with yogurt."
        ],
        "tip": "Very low heat for the final 30 min — don't lift the lid. Everything cooks together in one pot.",
        "shopping": ["chicken thighs (x6–8, ~1kg)", "barberries or currants", "cardamom pods",
                     "basmati rice (300g)", "fresh dill", "fresh coriander", "Greek yogurt"]
    },
    "chicken_clementines": {
        "name": "Roasted Chicken with Clementines & Arak",
        "type": "meat",
        "kcal": 720, "protein": 55, "cook_mins": 55,
        "desc": "Chicken marinated in arak, mustard and brown sugar, roasted with fennel and clementines",
        "batch": False, "quick": False,
        "ingredients": [
            "1 large free-range chicken (~1.3kg) cut into 8 pieces, or same weight chicken thighs",
            "100ml arak, ouzo, or Pernod", "4 tbsp olive oil",
            "3 tbsp orange juice", "3 tbsp lemon juice",
            "2 tbsp grain mustard", "3 tbsp light brown sugar",
            "2 medium fennel bulbs (500g), cut into wedges",
            "4 clementines, unpeeled, sliced ¼-inch thick",
            "1 tbsp thyme leaves", "2½ tsp fennel seeds, lightly crushed",
            "Flat-leaf parsley to garnish", "Salt & black pepper"
        ],
        "method": [
            "Whisk together arak, oil, orange juice, lemon juice, mustard, brown sugar, 2½ tsp salt and 1½ tsp pepper in a large bowl.",
            "Add fennel, chicken, clementines, thyme and fennel seeds. Mix well. Marinate in the fridge a few hours or overnight.",
            "Preheat oven to 240°C. Spread everything in a single layer on a large baking sheet, chicken skin-side up. Roast 35–45 min until chicken is golden and cooked through.",
            "Transfer chicken, fennel and clementines to a serving plate. Reduce cooking juices until saucy. Pour over. Garnish with parsley. Serve with plain rice or bulgur."
        ],
        "tip": "Overnight marinating transforms this dish — though skipping it still works. One of the book's most loved recipes.",
        "shopping": ["whole chicken or thighs (~1.3kg)", "arak or ouzo or Pernod", "clementines (x4)",
                     "fennel bulbs (x2)", "grain mustard", "light brown sugar", "fennel seeds", "oranges"]
    },
    "chicken_freekeh": {
        "name": "Poached Chicken with Sweet Spiced Freekeh",
        "type": "meat",
        "kcal": 750, "protein": 58, "cook_mins": 100,
        "desc": "Whole chicken poached in spiced broth, served over smoky freekeh pilaf with toasted almonds",
        "batch": True, "quick": False,
        "ingredients": [
            "1 small free-range chicken (~1.5kg)",
            "2 long cinnamon sticks", "2 medium carrots, sliced",
            "2 bay leaves", "2 bunches flat-leaf parsley (~70g total)",
            "2 large onions", "2 tbsp olive oil",
            "300g cracked freekeh",
            "½ tsp ground allspice", "½ tsp ground coriander",
            "40g unsalted butter", "60g sliced almonds",
            "Salt & black pepper", "Greek yogurt with cucumber, to serve"
        ],
        "method": [
            "Place chicken in a large pot with cinnamon, carrots, bay leaves, 1 bunch parsley, 1 quartered onion and 1 tsp salt. Cover with cold water. Bring to boil, simmer covered 1 hour, skimming occasionally.",
            "Thinly slice remaining onion. Fry in olive oil 12–15 min until deep golden. Add freekeh, allspice, coriander, ½ tsp salt and pepper. Add 600ml hot chicken broth. Boil, cover, simmer gently 20 min. Rest covered 20 min off heat.",
            "Remove chicken from broth. Pull meat off the bone in large pieces.",
            "Toast almonds in butter until golden. Pile freekeh on a platter, top with chicken. Scatter almonds and remaining parsley. Serve with yogurt."
        ],
        "tip": "Use leftover broth for soup the next day. Freekeh from Middle Eastern shops — bulgur can substitute.",
        "shopping": ["whole chicken (~1.5kg)", "cracked freekeh (300g)", "sliced almonds (60g)",
                     "carrots (x2)", "flat-leaf parsley (2 bunches)", "ground allspice"]
    },
    "maqluba": {
        "name": "Maqluba — Upside-Down Chicken & Rice",
        "type": "meat",
        "kcal": 700, "protein": 55, "cook_mins": 90,
        "desc": "The great Palestinian celebration dish — layered fried aubergine, cauliflower, chicken and spiced rice, inverted at the table",
        "batch": True, "quick": False,
        "ingredients": [
            "6–8 boneless chicken thighs, skin on (~800g)",
            "2 medium aubergines (650g), sliced ¼-inch thick",
            "1 medium cauliflower (500g), broken into large florets",
            "320g basmati rice, soaked 30 min in salted water then drained",
            "1 large onion quartered, 10 black peppercorns, 2 bay leaves",
            "Sunflower oil for frying",
            "3–4 medium tomatoes (350g), sliced",
            "4 large cloves garlic, halved",
            "1 tsp each: ground turmeric, cinnamon, allspice, baharat",
            "30g pine nuts, fried in butter until golden",
            "Salt", "Yogurt with cucumber, to serve"
        ],
        "method": [
            "Salt aubergine slices on both sides, leave 20 min, pat dry. Sear chicken 3–4 min per side until golden. Add onion, peppercorns, bay leaves and water to cover. Boil, cover, cook low heat 20 min. Remove chicken, reserve and skim stock.",
            "Fry cauliflower in 2cm sunflower oil until golden, ~3 min per batch. Drain and salt. Fry aubergine slices similarly. Drain.",
            "Grease a 24cm deep non-stick pan. Layer tomatoes on base, then aubergine, then cauliflower. Sit chicken on top. Mix spices with drained rice and spread over. Pour over 900ml hot stock. Bring to boil, cover tightly, cook over very low heat 30 min. Rest 10 min.",
            "Invert onto a large platter — place both hands on the pot base and flip confidently. Scatter golden pine nuts over. Serve with yogurt."
        ],
        "tip": "The inversion is the drama — commit to it. The tradition is everyone places their palms on the inverted pot and waits 3 min. Air fryer: toss aubergine and cauliflower with 1 tbsp oil each and air fry at 200°C for 10–12 min until golden — cuts oil dramatically.",
        "shopping": ["chicken thighs (x8, ~800g)", "aubergines (x2)", "cauliflower (x1 medium)",
                     "basmati rice (320g)", "pine nuts (30g)", "baharat spice mix", "tomatoes (x4)"]
    },
    "kofta_bsiniyah": {
        "name": "Kofta B'siniyah",
        "type": "meat",
        "kcal": 680, "protein": 46, "cook_mins": 35,
        "desc": "Spiced lamb and beef torpedo kofta, seared then baked in a creamy tahini sauce with toasted pine nuts",
        "batch": True, "quick": False,
        "ingredients": [
            "400g ground lamb", "400g ground veal or beef",
            "1 small onion (~150g), finely chopped",
            "2 large cloves garlic, crushed",
            "50g toasted pine nuts, coarsely chopped",
            "30g flat-leaf parsley, finely chopped",
            "1 large red chilli, seeded and finely chopped",
            "1½ tsp ground cinnamon", "1½ tsp ground allspice",
            "¾ tsp grated nutmeg", "1½ tsp salt", "1½ tsp black pepper",
            "2 tbsp sunflower oil",
            "TAHINI SAUCE:", "150g light tahini paste",
            "3 tbsp lemon juice", "120ml water", "1 clove garlic, crushed",
            "Pine nuts and chopped parsley to garnish",
            "Pitta and tomato-cucumber salad to serve"
        ],
        "method": [
            "Mix all kofta ingredients well with your hands. Shape into 18 torpedo fingers (~8cm long). Press firmly. Chill until ready, up to 1 day.",
            "Whisk tahini, lemon juice, water, garlic and ¼ tsp salt to a smooth sauce slightly runnier than honey.",
            "Preheat oven to 220°C. Heat oil in a large frying pan over high heat. Sear kofta in batches on all sides until golden, ~6 min per batch.",
            "Arrange in a baking dish, pour tahini sauce over. Bake 10 min until sauce is bubbling. Garnish with pine nuts and parsley. Serve with pitta."
        ],
        "tip": "Chill the shaped kofta for up to a day — they firm up and hold their shape better when searing. Air fryer: cook kofta at 200°C for 8–10 min instead of pan-searing — brush lightly with oil, then pour tahini sauce over and oven-bake as normal.",
        "shopping": ["ground lamb (400g)", "ground beef or veal (400g)", "pine nuts (50g)",
                     "light tahini paste (150g)", "flat-leaf parsley", "red chilli", "lemons"]
    },
    "braised_eggs_lamb": {
        "name": "Braised Eggs with Lamb, Tahini & Sumac",
        "type": "meat",
        "kcal": 650, "protein": 44, "cook_mins": 35,
        "desc": "Spiced ground lamb with cherry tomatoes, pistachios, baked eggs and tahini yogurt — Jerusalem fusion at its finest",
        "batch": False, "quick": False,
        "ingredients": [
            "1 tbsp olive oil", "1 large onion, finely chopped",
            "6 cloves garlic, thinly sliced", "300g ground lamb",
            "2 tsp sumac, plus extra to finish", "1 tsp ground cumin",
            "50g toasted unsalted pistachios, crushed",
            "50g toasted pine nuts", "2 tsp harissa paste",
            "1 tbsp preserved lemon peel, finely chopped",
            "200g cherry tomatoes", "120ml chicken stock",
            "4 large eggs", "Salt & black pepper",
            "TAHINI YOGURT:", "50g light tahini", "50g Greek yogurt",
            "2 tbsp lemon juice", "1 clove garlic, crushed", "2 tbsp water",
            "Coriander leaves to garnish", "Good bread to serve"
        ],
        "method": [
            "Make tahini yogurt: stir together tahini, yogurt, lemon juice, garlic, water and a pinch of salt until smooth. Set aside.",
            "Heat olive oil over medium. Cook onion and garlic 8 min until soft. Add lamb, sumac and cumin. Cook 5 min breaking up. Season well.",
            "Add pistachios, pine nuts, harissa, preserved lemon, cherry tomatoes and stock. Simmer 5 min until slightly reduced.",
            "Make 4 wells in the mixture. Crack an egg into each. Cover and cook over low heat 5–8 min until whites set but yolks still runny. Drizzle tahini yogurt over, scatter extra sumac and coriander. Eat from the pan with good bread."
        ],
        "tip": "Everything can be prepped in advance up to the egg stage. Serve directly from the pan — no plating needed.",
        "shopping": ["ground lamb (300g)", "cherry tomatoes (200g)", "pistachios (50g)",
                     "pine nuts (50g)", "harissa paste", "preserved lemon", "light tahini", "sumac"]
    },
    "freekeh_soup_meatballs": {
        "name": "Spicy Freekeh Soup with Meatballs",
        "type": "meat",
        "kcal": 720, "protein": 42, "cook_mins": 55,
        "desc": "Hearty Palestinian smoky freekeh soup with spiced beef meatballs, vegetables and lemon",
        "batch": True, "quick": False,
        "ingredients": [
            "MEATBALLS:", "400g ground beef, lamb, or a mix",
            "1 small onion finely diced", "2 tbsp flat-leaf parsley chopped",
            "½ tsp ground allspice", "¼ tsp ground cinnamon",
            "3 tbsp plain flour", "2 tbsp olive oil",
            "SOUP:", "2 tbsp olive oil", "1 large onion chopped",
            "3 cloves garlic crushed",
            "2 carrots cut into 1cm cubes",
            "2 celery stalks cut into 1cm cubes",
            "3 large tomatoes chopped", "2½ tbsp tomato paste",
            "1 tbsp baharat spice mix", "1 tbsp ground coriander",
            "1 cinnamon stick", "1 tbsp sugar",
            "150g cracked freekeh",
            "500ml beef stock", "500ml chicken stock", "800ml hot water",
            "Fresh coriander and lemon wedges to serve", "Salt & black pepper"
        ],
        "method": [
            "Mix meatball ingredients (except flour and oil) with ½ tsp salt. Roll into ping-pong-sized balls and coat in flour. Fry in oil in a large Dutch oven until golden. Remove and set aside.",
            "In same pot heat 2 tbsp oil. Fry onion, garlic, carrots and celery 8 min. Add tomatoes, tomato paste, baharat, coriander, cinnamon and sugar. Cook 5 min.",
            "Add freekeh, both stocks and hot water. Bring to boil, return meatballs. Cover and simmer 25 min until freekeh is cooked through.",
            "Taste and season. Ladle into bowls, scatter coriander. Serve with lemon wedges."
        ],
        "tip": "Even better the next day when freekeh absorbs more broth. Bulgur substitutes well if freekeh is unavailable. Air fryer: air fry the floured meatballs at 200°C for 8–10 min instead of pan-frying, then add directly to the soup.",
        "shopping": ["ground beef or lamb (400g)", "cracked freekeh (150g)", "beef stock (500ml)",
                     "chicken stock (500ml)", "baharat spice mix", "carrots (x2)",
                     "celery (x2 stalks)", "tomatoes (x3)", "fresh coriander"]
    },
    "hummus_kawarma": {
        "name": "Hummus Kawarma with Lemon Sauce",
        "type": "meat",
        "kcal": 680, "protein": 38, "cook_mins": 30,
        "desc": "Warm homemade hummus topped with spiced fried lamb, pine nuts and a sharp lemon sauce — one of Jerusalem's greatest dishes",
        "batch": False, "quick": False,
        "ingredients": [
            "HUMMUS:", "1 tin (400g) chickpeas drained (reserve liquid)",
            "4 tbsp light tahini", "2 tbsp lemon juice",
            "1 clove garlic crushed", "3 tbsp ice-cold water", "Salt",
            "KAWARMA:", "300g lamb neck fillet finely chopped (or ground lamb)",
            "¼ tsp each black and white pepper",
            "1 tsp ground allspice", "½ tsp ground cinnamon",
            "pinch grated nutmeg", "1 tsp dried za'atar or oregano",
            "1 tbsp white wine vinegar",
            "1 tbsp each fresh mint and parsley chopped",
            "1 tsp salt", "1 tbsp butter or ghee", "1 tsp olive oil",
            "2 tbsp pine nuts toasted",
            "LEMON SAUCE:", "10g parsley finely chopped",
            "1 green chilli finely chopped",
            "4 tbsp lemon juice", "2 tbsp white wine vinegar",
            "2 cloves garlic crushed", "Warm pitta to serve"
        ],
        "method": [
            "Blend chickpeas, tahini, lemon juice, garlic, ice water and ½ tsp salt until very smooth and creamy. Taste and adjust.",
            "Mix all kawarma ingredients except butter and oil. Marinate 30 min in the fridge.",
            "Mix all lemon sauce ingredients in a small bowl. Set aside.",
            "Heat butter and oil in a frying pan over high heat. Fry lamb 3–5 min until just cooked and slightly caramelised. Spoon warm hummus into bowls, top with lamb, scatter pine nuts, drizzle lemon sauce over. Serve with warm pitta."
        ],
        "tip": "Use the best quality tahini you can find — it transforms the hummus. Al Wadi or Jaffa brands are excellent.",
        "shopping": ["tinned chickpeas (x1)", "light tahini (best quality)", "lamb neck or ground lamb (300g)",
                     "pine nuts", "fresh mint", "white wine vinegar", "green chilli", "pitta breads"]
    },
    # ── MORE FISH ─────────────────────────────────────────────────────────────────
    "cod_cakes": {
        "name": "Cod Cakes in Tomato Sauce",
        "type": "fish",
        "kcal": 500, "protein": 42, "cook_mins": 45,
        "desc": "Delicate Syrian-Jewish fish cakes simmered in a sweet-sharp spiced tomato sauce",
        "batch": True, "quick": False,
        "ingredients": [
            "600g cod, halibut, hake or pollock fillet skinned",
            "3 slices white bread crusts removed (~60g)",
            "1 medium onion finely chopped", "4 cloves garlic crushed",
            "30g flat-leaf parsley finely chopped",
            "30g fresh coriander finely chopped",
            "1 tbsp ground cumin", "1½ tsp salt",
            "2 large eggs beaten", "4 tbsp olive oil",
            "TOMATO SAUCE:", "2½ tbsp olive oil",
            "1½ tsp ground cumin", "½ tsp sweet paprika",
            "1 tsp ground coriander", "1 medium onion chopped",
            "125ml dry white wine", "1 tin (400g) chopped tomatoes",
            "1 red chilli finely chopped", "1 clove garlic crushed",
            "2 tsp sugar", "2 tbsp fresh mint chopped",
            "Salt & black pepper", "Bulgur or rice to serve"
        ],
        "method": [
            "Make sauce: heat olive oil, add spices and onion, cook 8–10 min until very soft. Add wine, simmer 3 min. Add tomatoes, chilli, garlic, sugar, ½ tsp salt and pepper. Simmer 15 min until thick. Set aside.",
            "Blitz bread to crumbs. Chop fish very finely and mix with breadcrumbs, onion, garlic, herbs, cumin, salt and beaten eggs. Shape into ~12 patties with damp hands.",
            "Fry fish cakes in olive oil in batches until golden on both sides, ~8 min total.",
            "Return all cakes to pan, pour tomato sauce over, cover and simmer gently 10–12 min. Scatter mint over. Serve with bulgur or rice."
        ],
        "tip": "Even better the day after — cakes firm up and absorb the sauce. Reheat gently covered. Air fryer: air fry the fish cakes at 190°C for 10–12 min (spray with oil) before adding to the tomato sauce.",
        "shopping": ["cod or white fish fillet (600g)", "tinned chopped tomatoes", "dry white wine",
                     "fresh coriander (30g)", "flat-leaf parsley (30g)", "red chilli", "fresh mint"]
    },
    "grilled_fish_skewers": {
        "name": "Grilled Fish Skewers with Hawayej & Parsley",
        "type": "fish",
        "kcal": 560, "protein": 48, "cook_mins": 20,
        "desc": "Firm white fish marinated in Yemeni hawayej spice mix, grilled on skewers",
        "batch": False, "quick": True,
        "ingredients": [
            "1kg firm white fish fillets (monkfish, halibut or cod) cut into 2.5cm cubes",
            "50g flat-leaf parsley finely chopped",
            "2 large cloves garlic crushed",
            "½ tsp chilli flakes", "1 tbsp lemon juice",
            "2 tbsp olive oil", "Salt", "Lemon wedges to serve",
            "HAWAYEJ SPICE MIX:",
            "1 tsp black peppercorns", "1 tsp coriander seeds",
            "1½ tsp cumin seeds", "4 whole cloves",
            "½ tsp ground cardamom", "1½ tsp ground turmeric"
        ],
        "method": [
            "Toast peppercorns, coriander seeds, cumin and cloves in a dry pan until fragrant. Grind finely. Mix with cardamom and turmeric.",
            "Combine fish, parsley, garlic, chilli, lemon juice, olive oil, 1 tsp salt and all the hawayej. Mix well. Marinate in the fridge 1–12 hours.",
            "Thread fish onto soaked skewers (5–6 pieces each), leaving small gaps. Brush lightly with olive oil.",
            "Heat a ridged griddle pan over high heat 4 min until very hot. Grill skewers in batches, 1½ min per side until just cooked through. Serve immediately with lemon wedges."
        ],
        "tip": "Longer marinating gives deeper spice flavour. Brilliant on a BBQ — the smoky char complements the hawayej perfectly.",
        "shopping": ["firm white fish fillets (1kg)", "coriander seeds", "cumin seeds",
                     "whole cloves", "ground cardamom", "ground turmeric",
                     "flat-leaf parsley (50g)", "bamboo skewers (soak 1 hr in water)"]
    },
    # ── MORE PLANT ────────────────────────────────────────────────────────────────
    "musabaha": {
        "name": "Musabaha — Warm Chickpeas with Hummus",
        "type": "plant",
        "kcal": 620, "protein": 26, "cook_mins": 20,
        "desc": "Warm whole chickpeas ladled over smooth hummus with olive oil and cumin — one of the quickest and best meals in the book",
        "batch": False, "quick": True,
        "ingredients": [
            "2 tins (800g) chickpeas drained (reserve liquid from 1 tin)",
            "HUMMUS:",
            "4 tbsp light tahini", "2 tbsp lemon juice",
            "1 clove garlic crushed", "3 tbsp ice-cold water or chickpea liquid",
            "Salt",
            "To serve:",
            "4 tbsp best-quality olive oil",
            "1½ tsp ground cumin", "1 tsp sweet paprika",
            "Fresh flat-leaf parsley chopped",
            "Warm pitta breads"
        ],
        "method": [
            "Blend one tin of chickpeas with tahini, lemon juice, garlic, ice water and ½ tsp salt until very smooth and creamy. Taste and adjust.",
            "Warm the second tin of chickpeas gently in a small pan with a splash of their liquid. Drain, keeping hot.",
            "Spread hummus in wide shallow bowls. Ladle warm whole chickpeas over the top.",
            "Drizzle generously with olive oil. Scatter cumin, paprika and parsley over. Serve immediately with warm pitta."
        ],
        "tip": "Use the best olive oil you have — it's front and centre. Toast pitta directly over a flame for 30 seconds per side.",
        "shopping": ["tinned chickpeas (x2)", "light tahini", "lemons", "sweet paprika",
                     "ground cumin", "fresh flat-leaf parsley", "pitta breads", "best-quality olive oil"]
    },
    "falafel": {
        "name": "Falafel",
        "type": "plant",
        "kcal": 460, "protein": 24, "cook_mins": 30,
        "desc": "Crispy Jerusalem-style falafel from soaked dried chickpeas — served in pitta with tahini and salad",
        "batch": True, "quick": False,
        "ingredients": [
            "250g dried chickpeas (NOT tinned) — soak 24 hours in cold water",
            "1 medium onion roughly chopped", "4 cloves garlic",
            "1 tsp ground cumin", "1 tsp ground coriander",
            "½ tsp chilli flakes",
            "40g flat-leaf parsley", "40g fresh coriander",
            "1 tsp baking powder", "1 tsp salt",
            "Sunflower oil for deep-frying",
            "Pitta breads tahini sauce pickled vegetables and tomato-cucumber salad to serve"
        ],
        "method": [
            "Drain soaked chickpeas thoroughly. Blitz in a food processor with onion, garlic, spices, herbs, baking powder and salt to a coarse paste that just holds when pressed — don't over-blend.",
            "Refrigerate mixture 30 min. Shape into small balls or patties (~30g each) with damp hands.",
            "Heat at least 5cm sunflower oil in a deep saucepan to 180°C. Fry falafel in batches of 5–6 for 4–5 min, turning, until deep golden brown. Drain on paper towels.",
            "Serve immediately in warm pitta with tahini sauce, tomato and cucumber salad and pickled vegetables."
        ],
        "tip": "Must use dried soaked chickpeas — tinned chickpeas make soggy falafel that fall apart. Soak for a full 24 hours. Air fryer: spray with oil and cook at 190°C for 12–14 min, turning halfway — no deep-frying needed.",
        "shopping": ["dried chickpeas (250g — soak 24 hrs)", "flat-leaf parsley (40g)",
                     "fresh coriander (40g)", "sunflower oil (for deep frying)",
                     "pitta breads", "light tahini"]
    },
    # ── more plant ───────────────────────────────────────────────────────────────
    "sabih": {
        "name": "Sabih",
        "type": "plant",
        "kcal": 590, "protein": 22, "cook_mins": 35,
        "desc": "Iraqi-Israeli street food — fried aubergine, hard-boiled eggs, tahini, zhoug and chopped salad in pitta",
        "batch": False, "quick": False,
        "ingredients": [
            "2 large aubergines (~750g)",
            "~300ml sunflower oil (for frying)",
            "4 slices good white bread toasted, or fresh mini pittas",
            "240ml tahini sauce (4 tbsp tahini, 2 tbsp lemon juice, 1 clove garlic, water to thin)",
            "4 large eggs, hard-boiled, peeled and sliced",
            "4 tbsp zhoug (or harissa)",
            "Savory mango pickle (amba) — optional but authentic",
            "CHOPPED SALAD:",
            "2 medium tomatoes, diced", "2 mini cucumbers, diced",
            "2 spring onions, thinly sliced",
            "1½ tbsp flat-leaf parsley, chopped",
            "2 tsp lemon juice", "1½ tbsp olive oil",
            "Salt & black pepper"
        ],
        "method": [
            "Peel aubergines in alternating strips (zebralike). Cut widthwise into 2.5cm slices. Sprinkle both sides with salt and leave on a baking sheet 30 min. Pat dry with paper towels.",
            "Heat sunflower oil in a wide frying pan. Fry aubergine slices in batches until dark and completely tender, 6–8 min total per batch, turning once. Drain on paper towels.",
            "Mix all chopped salad ingredients together. Season well.",
            "Place a slice of bread or pitta on each plate. Spoon tahini over, layer aubergine on top, season. Place egg slices over, add more tahini, spoon over zhoug and mango pickle if using. Serve salad on the side."
        ],
        "tip": "The combination of textures is the point — don't rush the aubergine frying. Mango pickle (amba) from Middle Eastern shops makes it authentic. Air fryer: brush aubergine slices with 1 tbsp oil and air fry at 200°C for 10–12 min, flipping halfway — cuts oil from ~300ml to a drizzle.",
        "shopping": ["aubergines (x2, ~750g)", "sunflower oil", "eggs (x4)",
                     "light tahini", "mini pittas or good bread", "tomatoes (x2)",
                     "mini cucumbers (x2)", "zhoug or harissa"]
    },
    "open_kibbeh": {
        "name": "Open Kibbeh",
        "type": "meat",
        "kcal": 680, "protein": 36, "cook_mins": 55,
        "desc": "Layered bulgur and spiced lamb cake baked in a springform tin, topped with tahini — serve with tabbouleh",
        "batch": True, "quick": False,
        "ingredients": [
            "125g fine bulgur wheat",
            "200ml water",
            "6 tbsp / 90ml olive oil",
            "2 cloves garlic, crushed",
            "2 medium onions, finely chopped",
            "1 green chilli, finely chopped",
            "350g ground lamb",
            "1 tsp ground allspice",
            "1 tsp ground cinnamon",
            "1 tsp ground coriander",
            "2 tbsp coriander leaves, chopped",
            "60g pine nuts",
            "3 tbsp flat-leaf parsley, chopped",
            "2 tbsp self-raising flour",
            "50g light tahini paste",
            "2 tsp lemon juice",
            "1 tsp sumac",
            "Salt & black pepper"
        ],
        "method": [
            "Preheat oven to 200°C. Line a 20cm springform pan with baking paper. Cover bulgur with the water and leave 30 min to absorb.",
            "Heat 4 tbsp oil in a large frying pan over medium-high. Sauté garlic, onion and chilli until completely soft. Remove. Return pan to high heat, add lamb and cook 5 min, stirring, until brown. Return onion mix, add spices, coriander, ½ tsp salt and black pepper. Cook 2 min. Stir in pine nuts and parsley.",
            "Squeeze the soaked bulgur dry. Mix with 1 tbsp oil, flour, and ½ tsp salt to form a dough. Press half the bulgur mixture over the base of the lined tin. Spread the lamb filling over evenly. Press the remaining bulgur over the top.",
            "Drizzle with remaining 1 tbsp oil. Bake 25 min until a crust forms. Whisk tahini with lemon juice, water, and a pinch of salt to a pourable sauce. Cut the kibbeh into wedges, drizzle tahini over, sprinkle sumac. Serve warm or at room temperature."
        ],
        "tip": "Makes excellent leftovers — even better at room temperature the next day. Serves 6 generously.",
        "shopping": ["fine bulgur wheat (125g)", "ground lamb (350g)", "pine nuts (60g)",
                     "light tahini paste (50g)", "self-raising flour", "sumac"]
    },
    # ── more fish ────────────────────────────────────────────────────────────────
    "sweet_sour_fish": {
        "name": "Marinated Sweet & Sour Fish",
        "type": "fish",
        "kcal": 420, "protein": 30, "cook_mins": 40,
        "desc": "Fried white fish fillets in a curry-spiced sweet and sour sauce with peppers, tomatoes and coriander — best served at room temperature",
        "batch": True, "quick": False,
        "ingredients": [
            "500g pollock, cod, halibut or haddock fillets, cut into 4 pieces",
            "3 tbsp olive oil",
            "2 medium onions, cut into 1cm slices",
            "1 tbsp coriander seeds",
            "2 peppers (1 red, 1 yellow), cut into strips",
            "2 cloves garlic, crushed",
            "3 bay leaves",
            "1½ tbsp curry powder",
            "3 tomatoes, chopped",
            "2½ tbsp sugar",
            "5 tbsp cider vinegar",
            "Seasoned plain flour, for dusting",
            "2 large eggs, beaten",
            "20g fresh coriander, chopped",
            "Salt & black pepper",
            "Crusty bread to serve"
        ],
        "method": [
            "Preheat oven to 190°C. Heat 2 tbsp oil in a large ovenproof frying pan over medium heat. Cook onions and coriander seeds 5 min. Add peppers and cook 10 min. Add garlic, bay leaves, curry powder and tomatoes, cook 8 min. Add sugar, vinegar, 1½ tsp salt and pepper. Cook 5 min more.",
            "Heat remaining 1 tbsp oil in a separate frying pan over medium-high heat. Sprinkle fish with salt, dip in flour then egg, and fry 3 min, turning once.",
            "Lay fish on top of the sauce in the ovenproof pan. Transfer to the oven and cook 15 min.",
            "Remove from oven. Scatter coriander over. Leave to cool to room temperature — or refrigerate overnight and bring back to room temp before serving. Eat with good bread."
        ],
        "tip": "This is genuinely better after a day in the fridge — the fish absorbs the sauce. Make it Sunday for Monday's lunch.",
        "shopping": ["white fish fillets (500g)", "red and yellow peppers (1 each)",
                     "curry powder", "cider vinegar", "coriander seeds",
                     "tomatoes (x3)", "fresh coriander"]
    },
    "prawns_feta": {
        "name": "Prawns, Scallops & Clams with Tomato & Feta",
        "type": "fish",
        "kcal": 540, "protein": 46, "cook_mins": 30,
        "desc": "Unexpectedly delicious Ottolenghi catering classic — seafood baked in a tomato and oregano sauce with feta",
        "batch": False, "quick": True,
        "ingredients": [
            "250ml white wine",
            "1kg clams, scrubbed (or omit — see tip)",
            "3 cloves garlic, thinly sliced",
            "3 tbsp olive oil",
            "600g peeled and chopped tomatoes (fresh or canned)",
            "1 tsp sugar",
            "2 tbsp oregano, chopped",
            "1 lemon",
            "200g tiger prawns, peeled and deveined",
            "200g large scallops",
            "120g feta, broken into chunks",
            "3 spring onions, thinly sliced",
            "Salt & black pepper",
            "Rice, couscous or bread to serve"
        ],
        "method": [
            "Boil wine in a medium saucepan until reduced by three-quarters. Add clams, cover and cook over high heat 2 min until they open. Drain through a sieve, catching the liquid. Remove clam meat from shells (keep a few in shell to garnish).",
            "Preheat oven to 240°C. Cook garlic in olive oil in a large ovenproof frying pan 1 min until golden. Add tomatoes, clam liquid, sugar, oregano, 3 strips lemon zest, salt and pepper. Simmer 5 min.",
            "Add prawns and scallops to the sauce, then scatter feta and clam meat over. Transfer to oven and bake 8–10 min until prawns are pink and scallops just cooked.",
            "Squeeze lemon juice over, scatter spring onions. Serve immediately with rice or bread."
        ],
        "tip": "Can be made without clams — just add white wine directly after garlic, reduce, then proceed. The feta-tomato-seafood combo is extraordinary.",
        "shopping": ["clams (1kg)", "tiger prawns (200g)", "large scallops (200g)",
                     "feta (120g)", "white wine (250ml)", "fresh oregano",
                     "spring onions (x3)"]
    },
    # ── more chicken ─────────────────────────────────────────────────────────────
    "chicken_artichoke": {
        "name": "Roasted Chicken with Jerusalem Artichoke & Lemon",
        "type": "meat",
        "kcal": 700, "protein": 52, "cook_mins": 60,
        "desc": "Saffron-scented chicken thighs roasted with Jerusalem artichokes, shallots, garlic and sliced lemon — serve with mejadra",
        "batch": False, "quick": False,
        "ingredients": [
            "8 skin-on bone-in chicken thighs, or 1 medium chicken quartered",
            "450g Jerusalem artichokes, peeled, cut into wedges",
            "3 tbsp lemon juice",
            "12 banana shallots, halved lengthwise",
            "12 large cloves garlic, sliced",
            "1 medium lemon, very thinly sliced",
            "1 tsp saffron threads",
            "50ml olive oil",
            "150ml cold water",
            "1¼ tbsp pink peppercorns, lightly crushed",
            "10g fresh thyme leaves",
            "40g tarragon leaves, chopped",
            "2 tsp salt", "½ tsp black pepper"
        ],
        "method": [
            "Parboil Jerusalem artichokes: cover with water and half the lemon juice, bring to a boil, simmer 10–20 min until just tender but not soft. Drain and cool.",
            "Combine artichokes with all remaining ingredients in a large roasting tin. Mix well so everything is coated. Leave to marinate at least 1 hour, or overnight in the fridge.",
            "Preheat oven to 200°C. Arrange chicken skin-side up on top of the vegetables. Roast 45–55 min until chicken is golden and cooked through, basting halfway.",
            "Rest 5 min before serving. Spoon the roasting juices over as a sauce."
        ],
        "tip": "Marinate overnight for the best flavour. The tarragon and saffron together are extraordinary. Serve with mejadra.",
        "shopping": ["chicken thighs (x8)", "Jerusalem artichokes (450g)", "banana shallots (x12)",
                     "saffron threads", "fresh tarragon (40g)", "pink peppercorns", "lemons (x2)"]
    },
    "lamb_shawarma": {
        "name": "Lamb Shawarma",
        "type": "meat",
        "kcal": 750, "protein": 60, "cook_mins": 270,
        "desc": "Whole leg of lamb marinated overnight in a Lebanese spice blend, slow-roasted until completely tender — shaved and served in flatbread",
        "batch": True, "quick": False,
        "ingredients": [
            "1 leg of lamb, 2.5–3kg",
            "240ml boiling water",
            "SPICE MARINADE:",
            "1 tsp black peppercorns", "1 tsp ground cumin",
            "1 tsp ground coriander", "½ tsp ground cloves",
            "½ tsp ground cardamom", "½ tsp ground nutmeg",
            "1 tsp ground cinnamon", "1 tsp ground allspice",
            "½ tsp ground turmeric", "2 tsp sweet paprika",
            "3 cloves garlic, crushed", "juice of 1 lemon",
            "3 tbsp olive oil", "1 tsp salt",
            "To serve: flatbread, tahini, chopped salad, pickles"
        ],
        "method": [
            "Dry-roast peppercorns, cumin, coriander and cloves until they pop. Grind finely. Mix with remaining spices, garlic, lemon juice, oil and salt to form a paste.",
            "Score the lamb leg in several places, making 1.5cm deep slits. Rub marinade all over and into the slits. Cover and marinate at least 2 hours, or overnight in the fridge.",
            "Preheat oven to 170°C. Place lamb fatty-side up in a large roasting pan. Cover with foil. After 30 min, add boiling water and baste every hour. Roast covered 4 hours total, until meat is completely tender and falling from the bone.",
            "Rest 15 min. Shave/pull meat off the bone. Serve in warm flatbread with tahini, chopped salad and pickles."
        ],
        "tip": "Make on a Sunday — the long slow cook is almost entirely unattended. Leftovers are extraordinary for 3 days. Serves 8 generously.",
        "shopping": ["leg of lamb (2.5–3kg)", "ground cardamom", "ground cloves",
                     "ground nutmeg", "sweet paprika", "flatbreads", "lemons"]
    },
    "beef_fava": {
        "name": "Beef Meatballs with Fava Beans & Lemon",
        "type": "meat",
        "kcal": 680, "protein": 44, "cook_mins": 40,
        "desc": "Herbed beef and lamb meatballs braised with fresh fava beans, green onions and lemon in chicken stock",
        "batch": True, "quick": False,
        "ingredients": [
            "MEATBALLS: 300g ground beef", "150g ground lamb",
            "1 medium onion, finely chopped",
            "120g breadcrumbs",
            "2 tbsp each chopped parsley, mint, dill and coriander",
            "2 large cloves garlic, crushed",
            "4 tsp baharat spice mix", "4 tsp ground cumin",
            "2 tsp capers, chopped", "1 egg, beaten",
            "¾ tsp salt", "black pepper",
            "4½ tbsp olive oil",
            "350g fava beans (fresh or frozen)",
            "4 thyme sprigs", "6 cloves garlic, sliced",
            "8 spring onions, cut into 2cm segments",
            "2½ tbsp lemon juice",
            "500ml chicken stock",
            "Fresh parsley, mint, dill and coriander to finish",
            "Basmati rice & orzo, to serve"
        ],
        "method": [
            "Mix all meatball ingredients together. Roll into ping-pong-sized balls. Sear in 1 tbsp oil in a large lidded frying pan until brown all over, ~5 min per batch. Remove and wipe pan.",
            "Blanch fava beans in boiling salted water 2 min. Drain, refresh under cold water. Peel skins from half the beans.",
            "Heat remaining oil in the same pan over medium heat. Add thyme, garlic and spring onions. Sauté 3 min. Add unpeeled fava beans, 1½ tbsp lemon juice, 80ml stock, ¼ tsp salt and plenty of pepper. The beans should be almost covered. Cover and cook over low heat 10 min.",
            "Return meatballs to the pan along with peeled fava beans and remaining stock. Cover and cook 15 min more. Add remaining lemon juice. Scatter herbs over. Serve with basmati rice and orzo."
        ],
        "tip": "Serve them with Basmati rice and orzo — the book says you don't need much else. Use frozen fava beans if fresh aren't available. Air fryer: air fry the meatballs at 200°C for 8–10 min (spray with oil) instead of searing — then add to the pot as normal.",
        "shopping": ["ground beef (300g)", "ground lamb (150g)", "baharat spice mix",
                     "fava beans frozen (350g)", "spring onions (x8)",
                     "chicken stock (500ml)", "fresh herbs (parsley, mint, dill, coriander)"]
    }
}


# ─── SIDES DATABASE ────────────────────────────────────────────────────────────
# Full recipes from Jerusalem — used as veg and carb sides

SIDES = {
    # ── VEG SIDES ────────────────────────────────────────────────────────────────
    "tabbouleh": {
        "name": "Tabbouleh",
        "kcal": 120, "slot_label": "Vegetable side",
        "cook_mins": 15,
        "ingredients": [
            "½ cup / 30g fine bulgur wheat",
            "2 large ripe tomatoes (~300g)",
            "1 shallot, finely chopped",
            "3 tbsp freshly squeezed lemon juice",
            "4 large bunches flat-leaf parsley (160g total)",
            "2 bunches fresh mint (30g total)",
            "2 tsp ground allspice",
            "1 tsp baharat spice mix",
            "½ cup / 80ml top-quality olive oil",
            "Seeds of ½ pomegranate (optional)",
            "Salt & black pepper"
        ],
        "method": [
            "Rinse bulgur in a fine sieve under cold water until water runs clear. Transfer to a large bowl.",
            "Slice tomatoes ¼ inch thick, then cut into small dice. Add to bulgur with lemon juice and shallot. Leave 10 min for bulgur to absorb the tomato juices.",
            "Finely chop parsley and mint leaves by hand — don't use a food processor or it will bruise them. Add to the bowl.",
            "Add allspice, baharat, olive oil, ½ tsp salt and plenty of black pepper. Toss well. Taste — it should be sharp and herby. Scatter over pomegranate seeds if using. Serve immediately."
        ],
        "tip": "The key: far more parsley than bulgur. It's a parsley salad, not a grain salad."
    },
    "spicy_carrot": {
        "name": "Spicy Carrot Salad",
        "kcal": 140, "slot_label": "Vegetable side",
        "cook_mins": 35,
        "ingredients": [
            "6 large carrots, peeled (~700g)",
            "3 tbsp sunflower oil",
            "1 large onion, finely chopped",
            "1 tbsp pilpelchuma or 2 tbsp harissa",
            "½ tsp ground cumin",
            "½ tsp caraway seeds, freshly ground",
            "½ tsp sugar",
            "3 tbsp cider vinegar",
            "1½ cups / 30g rocket leaves",
            "Salt"
        ],
        "method": [
            "Place carrots in a saucepan, cover with water, boil then simmer covered ~20 min until just tender. Drain and slice into ¼-inch rounds when cool enough to handle.",
            "Meanwhile, heat half the oil in a large frying pan over medium heat. Fry onion 10 min until golden brown.",
            "Tip fried onion into a large bowl. Add pilpelchuma or harissa, cumin, caraway, sugar, vinegar, and ½ tsp salt. Add warm carrot slices and remaining oil. Toss well.",
            "Leave at least 30 min for flavours to come together. Serve at room temperature with rocket scattered over."
        ],
        "tip": "Make this ahead — it improves significantly after 30 min. Good cold from the fridge too."
    },
    "roasted_cauliflower": {
        "name": "Roasted Cauliflower & Hazelnut Salad",
        "kcal": 180, "slot_label": "Vegetable side",
        "cook_mins": 40,
        "ingredients": [
            "1 head cauliflower, broken into small florets (~660g)",
            "5 tbsp olive oil",
            "1 large celery stalk, sliced on an angle",
            "5 tbsp / 30g hazelnuts, with skins",
            "⅓ cup / 10g small flat-leaf parsley leaves",
            "⅓ cup / 50g pomegranate seeds",
            "Generous ¼ tsp ground cinnamon",
            "Generous ¼ tsp ground allspice",
            "1 tbsp sherry vinegar",
            "1½ tsp maple syrup",
            "Salt & black pepper"
        ],
        "method": [
            "Preheat oven to 220°C. Toss cauliflower with 3 tbsp olive oil, ½ tsp salt, and black pepper. Spread in a roasting tin and roast on the top rack 25–35 min until crisp and golden in places. Transfer to a large bowl to cool.",
            "Reduce oven to 170°C. Spread hazelnuts on a lined baking sheet and roast 17 min. Cool slightly then coarsely chop.",
            "Add hazelnuts, celery, parsley, pomegranate seeds, cinnamon, allspice, remaining 2 tbsp olive oil, sherry vinegar, and maple syrup to the cauliflower.",
            "Toss well. Taste and adjust seasoning. Serve at room temperature."
        ],
        "tip": "Works warm or at room temperature — ideal to make while the main is resting."
    },
    "charred_okra": {
        "name": "Charred Okra with Tomato, Garlic & Preserved Lemon",
        "kcal": 100, "slot_label": "Vegetable side",
        "cook_mins": 20,
        "ingredients": [
            "300g baby or small okra",
            "2 tbsp olive oil",
            "4 cloves garlic, thinly sliced",
            "20g preserved lemon peel, cut into wedges",
            "3 small tomatoes (~200g), cut into wedges",
            "1½ tsp flat-leaf parsley, chopped",
            "1½ tsp fresh coriander, chopped",
            "1 tbsp freshly squeezed lemon juice",
            "Salt & black pepper"
        ],
        "method": [
            "Trim the okra pods, removing the stem just above the pod so as not to expose the seeds.",
            "Place a large heavy-bottomed frying pan over high heat for a few minutes until almost red hot. Add okra in two batches and dry-cook, shaking the pan, for 4 min per batch until lightly blistered.",
            "Return all okra to the pan. Add olive oil, garlic, and preserved lemon. Stir-fry 2 min. Reduce heat to medium, add tomatoes, 2 tbsp water, herbs, lemon juice, ½ tsp salt and pepper.",
            "Stir gently and cook 2–3 min until tomatoes are warmed through. Serve immediately."
        ],
        "tip": "The dry-charring is the key step — don't add oil until after. Frozen small okra from Middle Eastern shops works perfectly."
    },
    "swiss_chard_tahini": {
        "name": "Swiss Chard with Tahini, Yogurt & Buttered Pine Nuts",
        "kcal": 200, "slot_label": "Vegetable side",
        "cook_mins": 20,
        "ingredients": [
            "1.3kg Swiss chard",
            "2½ tbsp / 40g unsalted butter",
            "2 tbsp olive oil, plus extra to finish",
            "40g pine nuts",
            "2 small cloves garlic, very thinly sliced",
            "60ml dry white wine",
            "Sweet paprika, to garnish (optional)",
            "Salt & black pepper",
            "TAHINI & YOGURT SAUCE:",
            "50g light tahini paste",
            "50g Greek yogurt",
            "2 tbsp lemon juice",
            "1 clove garlic, crushed",
            "2 tbsp water"
        ],
        "method": [
            "Make the sauce: stir together tahini, yogurt, lemon juice, garlic, water, and a pinch of salt until smooth. Set aside.",
            "Separate chard stalks from leaves, cut both into 2cm slices keeping separate. Boil stalks in salted water 2 min, add leaves, cook 1 more min. Drain, rinse under cold water, and squeeze completely dry.",
            "Melt half the butter with the oil in a large frying pan. Fry pine nuts until golden, ~2 min. Remove with a slotted spoon. Add garlic, cook 1 min. Add wine, reduce to one-third. Add chard and remaining butter, cook 2–3 min.",
            "Spread tahini sauce on a serving plate. Pile chard on top. Scatter pine nuts, drizzle with olive oil and a pinch of paprika."
        ],
        "tip": "Squeezing the chard completely dry is essential — any water left will dilute the sauce."
    },
    # ── CARB SIDES ────────────────────────────────────────────────────────────────
    "couscous_tomato": {
        "name": "Couscous with Tomato & Onion",
        "kcal": 280, "slot_label": "Carb side",
        "cook_mins": 25,
        "ingredients": [
            "3 tbsp olive oil",
            "1 medium onion, finely chopped",
            "1 tbsp tomato paste",
            "½ tsp sugar",
            "2 very ripe tomatoes, finely diced",
            "150g couscous",
            "220ml boiling chicken or vegetable stock",
            "2½ tbsp / 40g unsalted butter",
            "Salt & black pepper"
        ],
        "method": [
            "Heat 2 tbsp oil in a non-stick pan (~22cm diameter) over medium heat. Fry onion 5 min until soft but not coloured. Add tomato paste and sugar, cook 1 min. Add tomatoes, ½ tsp salt, and pepper. Cook 3 min.",
            "Put couscous in a bowl, pour over boiling stock, cover with cling film. Leave 10 min, then fluff with a fork. Stir tomato sauce through the couscous.",
            "Wipe pan clean. Heat butter and remaining 1 tbsp oil over medium heat. Spoon couscous in and pat down gently.",
            "Cover, reduce heat to lowest, and steam 10–12 min until a golden crust forms at the base. Invert onto a plate. Serve warm or at room temperature."
        ],
        "tip": "The crispy bottom crust is the best bit — don't rush the steaming stage."
    },
    "basmati_wild_rice": {
        "name": "Basmati & Wild Rice with Chickpeas, Currants & Herbs",
        "kcal": 320, "slot_label": "Carb side",
        "cook_mins": 50,
        "ingredients": [
            "50g wild rice",
            "220g basmati rice",
            "330ml boiling water",
            "2½ tbsp olive oil",
            "2 tsp cumin seeds",
            "1½ tsp curry powder",
            "240g cooked chickpeas (1 tin, drained)",
            "180ml sunflower oil",
            "1 medium onion, thinly sliced",
            "1½ tsp plain flour",
            "100g currants",
            "2 tbsp flat-leaf parsley, chopped",
            "1 tbsp fresh coriander, chopped",
            "1 tbsp fresh dill, chopped",
            "Salt & black pepper"
        ],
        "method": [
            "Simmer wild rice in plenty of water ~40 min until cooked but still firm. Drain. Cook basmati rice: heat 1 tbsp olive oil in a lidded saucepan, add rice and ¼ tsp salt. Add boiling water, reduce heat to very low, cover and cook 15 min. Remove from heat, cover with a tea towel then lid, rest 10 min.",
            "Heat remaining 1½ tbsp olive oil in a small saucepan over high heat. Add cumin seeds, curry powder, then quickly add chickpeas and ¼ tsp salt. Stir over heat 1–2 min to heat through. Transfer to a large bowl.",
            "Heat sunflower oil in the same pan over high heat. Toss onion with flour, fry in batches 2–3 min until golden brown. Drain on paper towels and salt.",
            "Add both rices, currants, parsley, coriander, and dill to the chickpeas. Toss gently. Top with fried onion and serve."
        ],
        "tip": "Cook wild rice first as it takes 40 min — everything else is quick once it's done."
    },
    "pitta_side": {
        "name": "Warm Pitta Bread",
        "kcal": 160, "slot_label": "Carb side",
        "cook_mins": 5,
        "ingredients": [
            "4 pitta breads",
            "Olive oil (optional)",
            "Za'atar or dried herbs (optional)"
        ],
        "method": [
            "Heat pittas directly over a gas flame for 30 seconds per side until lightly charred and puffed, or wrap in foil and warm in a 180°C oven for 5 min.",
            "Optionally brush with olive oil and sprinkle with za'atar while warm."
        ],
        "tip": "Charring directly over a flame takes 1 minute and makes a huge difference to flavour."
    },
    "plain_rice": {
        "name": "Plain Basmati Rice",
        "kcal": 240, "slot_label": "Carb side",
        "cook_mins": 20,
        "ingredients": [
            "300g basmati rice",
            "450ml boiling water",
            "1 tbsp olive oil or butter",
            "½ tsp salt"
        ],
        "method": [
            "Rinse rice in cold water until water runs clear. Drain well.",
            "Heat oil or butter in a lidded saucepan over high heat. Add rice and salt, stir to coat. Add boiling water, reduce heat to very low, cover tightly and cook 15 min.",
            "Remove from heat. Cover with a clean tea towel, replace lid, and rest 10 min — this steams the rice perfectly.",
            "Fluff with a fork and serve."
        ],
        "tip": "The tea towel step is the Jerusalem method — it absorbs excess steam and gives fluffy, separate grains."
    }
}

# Map each dinner recipe to its veg side and carb side keys
DINNER_SIDES = {
    # Principle:
    #   couscous_tomato/basmati_wild_rice contain veg already -> no veg_side
    #   tabbouleh as carb_side covers veg+herb already -> no separate veg_side
    #   plain_rice/pitta have no veg -> keep veg_side where it makes sense
    #   dishes with veg already cooked in -> no extra veg_side

    #                             veg_side              carb_side
    # ── plant-based ──────────────────────────────────────────────────
    "mejadra":                   (None,                 None),
    "shakshuka":                 (None,                 "tabbouleh"),
    "chermoula_eggplant":        (None,                 None),
    "conchiglie":                (None,                 None),
    "barley_risotto":            (None,                 None),
    "musabaha":                  (None,                 "pitta_side"),
    "falafel":                   (None,                 None),
    "sabih":                     (None,                 None),         # salad already in dish
    "open_kibbeh":               (None,                 "tabbouleh"),  # tabbouleh recommended in book
    # ── fish ─────────────────────────────────────────────────────────
    "salmon_chraimeh":           ("charred_okra",       "plain_rice"),
    "sea_bass":                  (None,                 "couscous_tomato"),
    "mackerel":                  ("charred_okra",       "plain_rice"),
    "fish_kebabs":               (None,                 "tabbouleh"),
    "salmon_quick":              (None,                 None),
    "cod_cakes":                 ("spicy_carrot",       "plain_rice"),
    "grilled_fish_skewers":      (None,                 "tabbouleh"),
    "sweet_sour_fish":           (None,                 None),         # peppers/tomatoes in dish
    "prawns_feta":               (None,                 "plain_rice"),
    # ── meat ─────────────────────────────────────────────────────────
    "cannellini_lamb":           ("swiss_chard_tahini", "pitta_side"),
    "lamb_meatballs":            ("spicy_carrot",       "plain_rice"),
    "turkey_burgers":            (None,                 "tabbouleh"),
    "chicken_cardamom":          ("spicy_carrot",       "pitta_side"),
    "chicken_clementines":       (None,                 "couscous_tomato"),
    "chicken_freekeh":           (None,                 None),
    "maqluba":                   (None,                 None),
    "kofta_bsiniyah":            (None,                 "tabbouleh"),
    "braised_eggs_lamb":         (None,                 "tabbouleh"),
    "freekeh_soup_meatballs":    (None,                 None),
    "hummus_kawarma":            (None,                 "tabbouleh"),
    "chicken_artichoke":         (None,                 None),         # book says serve with mejadra
    "lamb_shawarma":             (None,                 "pitta_side"),
    "beef_fava":                 (None,                 None),         # fava beans are the veg, rice in dish
    "open_kibbeh":               (None,                 "tabbouleh"),
}

# Tue / Wed / Fri = training days — dinner must be quick (≤30 min)
TRAINING_DAYS = {"Tuesday", "Wednesday", "Friday"}
QUICK_THRESHOLD = 30  # minutes

# Full pools — all recipes by type
LUNCH_POOL = {
    "plant": ["mejadra", "chermoula_eggplant", "barley_risotto", "conchiglie",
              "musabaha", "falafel", "sabih"],
    "fish":  ["mackerel", "fish_kebabs", "sea_bass", "salmon_quick",
              "cod_cakes", "grilled_fish_skewers", "sweet_sour_fish"],
    "meat":  ["cannellini_lamb", "lamb_meatballs", "turkey_burgers",
              "chicken_cardamom", "hummus_kawarma", "freekeh_soup_meatballs",
              "kofta_bsiniyah", "maqluba",
              "open_kibbeh", "beef_fava", "chicken_artichoke"]
}
DINNER_POOL = {
    "plant": ["shakshuka", "chermoula_eggplant", "barley_risotto", "mejadra",
              "conchiglie", "musabaha", "falafel", "sabih"],
    "fish":  ["salmon_chraimeh", "sea_bass", "mackerel", "fish_kebabs",
              "salmon_quick", "cod_cakes", "grilled_fish_skewers",
              "sweet_sour_fish", "prawns_feta"],
    "meat":  ["cannellini_lamb", "lamb_meatballs", "turkey_burgers",
              "chicken_cardamom", "chicken_clementines", "chicken_freekeh",
              "maqluba", "kofta_bsiniyah", "braised_eggs_lamb",
              "hummus_kawarma", "freekeh_soup_meatballs",
              "chicken_artichoke", "lamb_shawarma", "beef_fava", "open_kibbeh"]
}
# Dinner types:
#   Training days (Tue/Wed/Fri): meat or fish, randomised each week
#   Saturday: meat or fish, randomised each week
#   All other days (Mon/Thu/Sun): plant-based
# Lunch types: 5 plant + 2 meat, randomly distributed across the week
PATTERNS = {
    "Monday":    ["plant", "plant"],
    "Tuesday":   ["plant", "meat"],    # training — dinner randomised meat/fish
    "Wednesday": ["plant", "fish"],    # training — dinner randomised meat/fish
    "Thursday":  ["plant", "plant"],
    "Friday":    ["plant", "meat"],    # training — dinner randomised meat/fish
    "Saturday":  ["plant", "fish"],    # dinner randomised meat/fish
    "Sunday":    ["plant", "plant"],
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def is_quick(key):
    r = RECIPES[key]
    return r.get("quick", False) or r["cook_mins"] <= QUICK_THRESHOLD

def generate_plan():
    plan = []
    used = set()

    # Lunch types: 5 plant, 2 meat, randomly assigned across the 7 days
    lunch_types = ["plant"] * 5 + ["meat"] * 2
    random.shuffle(lunch_types)
    lunch_type_by_day = dict(zip(DAYS, lunch_types))

    # Dinner types for meat/fish days: 2 meat + 2 fish, shuffled across Tue/Wed/Fri/Sat
    meat_fish_days = ["Tuesday", "Wednesday", "Friday", "Saturday"]
    dinner_types_mf = ["meat", "meat", "fish", "fish"]
    random.shuffle(dinner_types_mf)
    dinner_type_by_day = dict(zip(meat_fish_days, dinner_types_mf))

    for day in DAYS:
        lunch_type = lunch_type_by_day[day]
        dinner_type = dinner_type_by_day.get(day, PATTERNS[day][1])
        training = day in TRAINING_DAYS

        # Lunch: on training days prefer batch/quick (carried from yesterday)
        # — no cook_mins restriction on lunch since it's prepped the night before
        lunch_candidates = [k for k in LUNCH_POOL[lunch_type] if k not in used]
        if not lunch_candidates:
            lunch_candidates = list(LUNCH_POOL[lunch_type])  # allow repeats as fallback
        lunch_key = random.choice(lunch_candidates)
        used.add(lunch_key)

        # Dinner: on training days MUST be quick (≤30 min)
        dinner_candidates = [
            k for k in DINNER_POOL[dinner_type]
            if k not in used and k != lunch_key
            and (not training or is_quick(k))
        ]
        if not dinner_candidates:
            # Fallback: allow any quick recipe across types
            dinner_candidates = [
                k for k, r in RECIPES.items()
                if k not in used and k != lunch_key and is_quick(k)
            ]
        if not dinner_candidates:
            dinner_candidates = [k for k in DINNER_POOL[dinner_type] if k != lunch_key]
        dinner_key = random.choice(dinner_candidates)
        used.add(dinner_key)

        plan.append({
            "day": day,
            "lunch": lunch_key,
            "dinner": dinner_key,
            "training": training
        })
    return plan

MEAT_FISH_W = ["lamb","salmon","mackerel","sea bass","haddock","fish","chicken","turkey"]
DAIRY_W     = ["egg","yogurt","feta","labneh","butter","milk","cream","sour cream","mascarpone"]
VEG_W       = ["onion","garlic","aubergine","tomato","pepper","celery","potato","beet","okra",
               "parsley","coriander","dill","mint","thyme","oregano","spring","shallot","lemon",
               "courgette","cauliflower","carrot","chard","kale","rocket","watercress","kohlrabi",
               "cucumber","radish","pomegranate","chilli","green bean","spinach","basil"]
TINS_W      = ["lentil","bean","barley","bulgur","rice","passata","stock","tin","dried","raisin",
               "fig","currant","breadcrumb","flour","sugar","couscous","pasta","chickpea","wild rice",
               "pitta","flatbread","bread","pine nut","almond","hazelnut","cashew","walnut"]
SPICES_W    = ["cumin","paprika","turmeric","allspice","cinnamon","cayenne","chilli flake","cardamom",
               "caraway","harissa","tomato paste","vinegar","honey","rose water","olive oil",
               "sunflower oil","walnut oil","hazelnut oil","preserved lemon","capers","olive",
               "barberr","sumac","za'atar","baharat","tahini","pomegranate mol","maple syrup"]

def categorise_items(all_items):
    categories = {"Meat & Fish":[],"Dairy & Eggs":[],"Vegetables & Herbs":[],
                  "Tins, Grains & Bread":[],"Spices & Condiments":[],"Other":[]}
    for key, display in all_items.items():
        placed = False
        for word in MEAT_FISH_W:
            if word in key: categories["Meat & Fish"].append(display); placed=True; break
        if not placed:
            for word in DAIRY_W:
                if word in key: categories["Dairy & Eggs"].append(display); placed=True; break
        if not placed:
            for word in VEG_W:
                if word in key: categories["Vegetables & Herbs"].append(display); placed=True; break
        if not placed:
            for word in SPICES_W:
                if word in key: categories["Spices & Condiments"].append(display); placed=True; break
        if not placed:
            for word in TINS_W:
                if word in key: categories["Tins, Grains & Bread"].append(display); placed=True; break
        if not placed:
            categories["Other"].append(display)
    return {k: sorted(set(v)) for k, v in categories.items() if v}

def collect_day_items(day_plan):
    """Gather all shopping items for one day's meals + sides, scaled to 1 serving."""
    items = {}
    for slot in ["lunch", "dinner"]:
        recipe = RECIPES[day_plan[slot]]
        for item in recipe["shopping"]:
            scaled = scale_shopping_item(item, servings=4)
            k = scaled.lower().split("(")[0].split("/")[-1].strip()
            items[k] = scaled
    dinner_key = day_plan["dinner"]
    veg_key, carb_key = DINNER_SIDES.get(dinner_key, (None, None))
    sides_to_add = [veg_key]
    if day_plan.get("training") and carb_key:
        sides_to_add.append(carb_key)
    for side_key in sides_to_add:
        if side_key and side_key in SIDES:
            for item in SIDES[side_key]["ingredients"]:
                if item.endswith(":") or not any(c.isalpha() for c in item):
                    continue
                scaled = scale_shopping_item(item, servings=4)
                k = scaled.lower().split("(")[0].split("/")[-1].strip()
                items[k] = scaled
    return items

def build_shopping_list(plan):
    """Returns a per-day shopping list dict."""
    daily = {}
    for day_plan in plan:
        items = collect_day_items(day_plan)
        daily[day_plan["day"]] = categorise_items(items)
    return daily

# ─── GOOGLE CALENDAR ───────────────────────────────────────────────────────────

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        try: creds.refresh(Request())
        except: creds = None
    return creds

def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }


# ─── SERVING SCALER ────────────────────────────────────────────────────────────
# All recipes serve 4. Scale ingredients and macros down to 1 serving.

from fractions import Fraction
import re as _re

_UNICODE_FRACS = {
    '½': Fraction(1,2), '¼': Fraction(1,4), '¾': Fraction(3,4),
    '⅓': Fraction(1,3), '⅔': Fraction(2,3),
    '⅛': Fraction(1,8), '⅜': Fraction(3,8), '⅝': Fraction(5,8), '⅞': Fraction(7,8),
}

def _parse_quantity(token):
    """Parse a leading quantity token like '1½', '2', '¾', '3½' into a Fraction."""
    token = token.strip()
    result = Fraction(0)
    # Extract whole number part
    m = _re.match(r'^(\d+)', token)
    if m:
        result += Fraction(int(m.group(1)))
        token = token[m.end():]
    # Extract unicode fraction
    for uf, fv in _UNICODE_FRACS.items():
        if token.startswith(uf):
            result += fv
            token = token[len(uf):]
            break
    else:
        # Try ASCII fraction like 1/2
        m = _re.match(r'^(\d+)/(\d+)', token)
        if m:
            result += Fraction(int(m.group(1)), int(m.group(2)))
    return result if result > 0 else None

def _format_fraction(f):
    """Format a Fraction as a readable string, preferring unicode fractions."""
    if f == 0:
        return "0"
    whole = int(f)
    frac = f - whole
    frac_str = ""
    for uf, fv in _UNICODE_FRACS.items():
        if frac == fv:
            frac_str = uf
            break
    else:
        if frac != 0:
            dec = round(float(frac), 2)
            frac_str = (f"{dec:.2f}".rstrip('0').rstrip('.') or "0").lstrip('0') or "0"
            if not frac_str or frac_str == '.': frac_str = str(round(float(frac), 2))
    if whole and frac_str:
        return f"{whole}{frac_str}"
    elif whole:
        return str(whole)
    else:
        return frac_str or "0"

def scale_ingredient(ingredient, servings=4):
    """
    Scale an ingredient string down from `servings` to 1.
    Handles leading quantities like "2 tbsp", "1½ cups / 300g", "3 large eggs".
    Leaves non-quantified lines and weight-only strings (e.g. "750g lamb") unchanged.
    """
    s = ingredient.strip()
    if not s:
        return s
    # Skip "750g lamb", "500ml water" — digit immediately followed by a unit letter
    if _re.match(r'^\d+[a-zA-Z]', s):
        return s
    # Skip lines with no leading number or fraction
    if not _re.match(r'^[\d½¼¾⅓⅔⅛⅜⅝⅞]', s):
        return s

    # Match leading quantity (whole + optional unicode frac, or just unicode frac)
    qty_pat = _re.compile(r'^(\d+[½¼¾⅓⅔⅛⅜⅝⅞]?|[½¼¾⅓⅔⅛⅜⅝⅞])')
    m = qty_pat.match(s)
    if not m:
        return s

    raw_qty = m.group(1)
    qty = _parse_quantity(raw_qty)
    if qty is None or qty == 0:
        return s

    scaled = qty / servings
    new_qty = _format_fraction(scaled)
    return new_qty + s[m.end():]

def scale_shopping_item(item, servings=4):
    """Scale a shopping list item like 'eggs (x6)' -> 'eggs (x1½)' for 1 serving."""
    import re as _re2
    # Match (xN) or (xN, extra) but NOT (xN or ...) which are alternatives not counts
    m = _re2.match(r'^(.+?)\s*\(x(\d+(?:[\u2013\-]\d+)?)(,\s*[^)]+)?\)(.*)$', item)
    if m:
        prefix = m.group(1)
        qty_str = m.group(2)
        extra = (m.group(3) or "").lstrip(',').strip()
        suffix = m.group(4) or ""
        # Skip if the item inside parens looks like alternatives ("x5 or 1 tin")
        if ' or ' in item[item.find('('):item.find(')')+1]:
            return item
        qty_str_clean = qty_str.split('\u2013')[0].split('-')[0]
        try:
            qty = int(qty_str_clean)
            scaled = Fraction(qty, servings)
            qty_out = _format_fraction(scaled)
            extra_str = f", {extra}" if extra else ""
            return f"{prefix} (x{qty_out}{extra_str}){suffix}"
        except Exception:
            return item
    # Fall back to standard ingredient scaling
    return scale_ingredient(item, servings)

def scale_recipe(recipe, servings=4):
    """Return a copy of a recipe dict with ingredients scaled to 1 serving.
    kcal and protein are already per-serving in the database — do not divide."""
    r = dict(recipe)
    r["ingredients"] = [scale_ingredient(i, servings) for i in r.get("ingredients", [])]
    return r


# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    creds = get_credentials()
    authed = creds is not None and creds.valid
    return render_template('index.html', authed=authed, local_ip=get_local_ip())

@app.route('/api/generate', methods=['POST'])
def api_generate():
    plan = generate_plan()
    shopping = build_shopping_list(plan)
    session['shopping'] = shopping  # store for /shopping page
    # Attach recipe details
    detailed = []
    for d in plan:
        dinner_key = d["dinner"]
        veg_key, carb_key = DINNER_SIDES.get(dinner_key, (None, None))
        detailed.append({
            "day": d["day"],
            "training": d.get("training", False),
            "lunch": {**scale_recipe(RECIPES[d["lunch"]]), "key": d["lunch"]},
            "dinner": {**scale_recipe(RECIPES[dinner_key]), "key": dinner_key},
            "veg_side": {**scale_recipe(SIDES[veg_key]), "key": veg_key} if veg_key else None,
            "carb_side": {**scale_recipe(SIDES[carb_key]), "key": carb_key} if (carb_key and d.get("training")) else None,
        })
    return jsonify({"plan": detailed, "shopping": shopping})

@app.route('/api/recipes', methods=['GET'])
def api_recipes():
    return jsonify(RECIPES)

@app.route('/auth/google')
def auth_google():
    if not os.path.exists(CREDENTIALS_FILE):
        return "<h2>credentials.json not found</h2><p>See the README for setup instructions.</p>", 400

    with open(CREDENTIALS_FILE) as f:
        client_cfg = json.load(f)['web']

    import secrets, urllib.parse
    state = secrets.token_urlsafe(24)
    session['oauth_state'] = state
    session['client_id'] = client_cfg['client_id']
    session['client_secret'] = client_cfg['client_secret']
    session['token_uri'] = client_cfg['token_uri']

    redirect_uri = url_for('auth_callback', _external=True)
    session['redirect_uri'] = redirect_uri

    params = {
        'client_id': client_cfg['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent',
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)

@app.route('/auth/callback')
def auth_callback():
    # Verify state to prevent CSRF
    if request.args.get('state') != session.get('oauth_state'):
        return "State mismatch — possible CSRF. Please try again.", 400

    code = request.args.get('code')
    if not code:
        error = request.args.get('error', 'Unknown error')
        return f"<h2>Auth failed</h2><p>{error}</p>", 400

    # Exchange code for tokens directly — no PKCE, no library wrapping
    token_data = {
        'code': code,
        'client_id': session['client_id'],
        'client_secret': session['client_secret'],
        'redirect_uri': session['redirect_uri'],
        'grant_type': 'authorization_code',
    }
    resp = req_lib.post(session['token_uri'], data=token_data)
    if not resp.ok:
        return f"<h2>Token exchange failed</h2><pre>{resp.text}</pre>", 400

    tokens = resp.json()

    creds = Credentials(
        token=tokens['access_token'],
        refresh_token=tokens.get('refresh_token'),
        token_uri=session['token_uri'],
        client_id=session['client_id'],
        client_secret=session['client_secret'],
        scopes=SCOPES,
    )
    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(creds, f)

    return redirect('/?authed=1')

@app.route('/auth/logout')
def auth_logout():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    return redirect('/')

@app.route('/api/sync_calendar', methods=['POST'])
def sync_calendar():
    creds = get_credentials()
    if not creds or not creds.valid:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    plan = data.get('plan', [])
    start_date_str = data.get('start_date')  # YYYY-MM-DD

    try:
        start_date = datetime.date.fromisoformat(start_date_str)
    except:
        start_date = datetime.date.today()
        # Advance to next Monday
        days_ahead = 0 - start_date.weekday()
        if days_ahead <= 0: days_ahead += 7
        start_date += datetime.timedelta(days=days_ahead)

    import traceback, sys

    print(f"[sync] plan days received: {[d.get('day') for d in plan]}", flush=True)
    print(f"[sync] start_date: {start_date_str!r} -> {start_date}", flush=True)
    print(f"[sync] creds valid: {creds.valid}, expired: {creds.expired}", flush=True)

    # Refresh credentials if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Persist refreshed token
            with open(TOKEN_FILE, 'wb') as f:
                pickle.dump(creds, f)
            print("[sync] credentials refreshed", flush=True)
        except Exception as e:
            print(f"[sync] credential refresh failed: {e}", flush=True)
            return jsonify({"error": f"Could not refresh credentials — please reconnect Google Calendar: {e}"}), 401

    try:
        service = build('calendar', 'v3', credentials=creds)
        print("[sync] calendar service built OK", flush=True)
        # List available calendars so we can confirm which one we're writing to
        cal_list = service.calendarList().list().execute()
        for cal in cal_list.get('items', []):
            print(f"[sync]   calendar: {cal['id']!r} — {cal.get('summary')!r} (primary={cal.get('primary', False)})", flush=True)
    except Exception as e:
        print(f"[sync] FAILED to build service: {e}", flush=True)
        return jsonify({"error": f"Failed to connect to Google Calendar: {e}"}), 500

    created = []
    deleted = 0
    errors  = []
    shopping = data.get('shopping', {})

    day_map = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}

    # ── Delete existing Jerusalem Meal Planner events for this week ─────────────
    week_start = datetime.datetime.combine(start_date, datetime.time(0, 0))
    week_end   = week_start + datetime.timedelta(days=7)
    print(f"[sync] checking for existing events {week_start.date()} to {week_end.date()}", flush=True)
    try:
        page_token = None
        while True:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=week_start.isoformat() + 'Z',
                timeMax=week_end.isoformat() + 'Z',
                singleEvents=True,
                pageToken=page_token,
                maxResults=250
            ).execute()
            for event in events_result.get('items', []):
                summary = event.get('summary', '')
                desc    = event.get('description', '')
                # Match events created by this app
                if ('Jerusalem' in summary or 'Jerusalem' in desc or
                    summary.startswith('Lunch:') or summary.startswith('Dinner:') or
                    '🛒' in summary):
                    service.events().delete(calendarId='primary', eventId=event['id']).execute()
                    deleted += 1
                    print(f"[sync] deleted: {summary!r}", flush=True)
            page_token = events_result.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"[sync] WARNING: could not delete existing events: {e}", flush=True)

    print(f"[sync] deleted {deleted} existing events", flush=True)

    for day_idx, day_plan in enumerate(plan):
        day_offset = day_map[day_plan["day"]]
        event_date = start_date + datetime.timedelta(days=day_offset)

        # Work out what needs prepping tonight for tomorrow
        tomorrow_plan = plan[day_idx + 1] if day_idx + 1 < len(plan) else None

        # ── Daily shopping event at 08:00 ──────────────────────────────────────
        day_shop = shopping.get(day_plan["day"], {})
        if day_shop:
            shop_lines = [f"🛒 Shopping for {day_plan['day']}\n"]
            for cat, items in day_shop.items():
                if items:
                    shop_lines.append(f"{cat.upper()}")
                    for item in items:
                        shop_lines.append(f"• {item}")
                    shop_lines.append("")
            shop_dt_start = datetime.datetime.combine(event_date, datetime.time(8, 0))
            shop_dt_end   = shop_dt_start + datetime.timedelta(minutes=30)
            daily_shop_event = {
                'summary': f"🛒 {day_plan['day']} shopping — Jerusalem",
                'description': "\n".join(shop_lines),
                'start': {'dateTime': shop_dt_start.isoformat(), 'timeZone': 'Europe/London'},
                'end':   {'dateTime': shop_dt_end.isoformat(),   'timeZone': 'Europe/London'},
                'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 30}]},
                'colorId': '5'
            }
            try:
                result = service.events().insert(calendarId='primary', body=daily_shop_event).execute()
                created.append(result.get('htmlLink'))
                print(f"[sync] created shopping event for {day_plan['day']}", flush=True)
            except Exception as e:
                errors.append(f"Shopping {day_plan['day']}: {e}")
                print(f"[sync] ERROR shopping {day_plan['day']}: {e}", flush=True)

        for slot, hour, label in [("lunch", 12, "Lunch"), ("dinner", 19, "Dinner")]:
            recipe = day_plan[slot]
            cook_mins = recipe["cook_mins"]
            start_dt = datetime.datetime.combine(event_date, datetime.time(hour, 0))
            end_dt = start_dt + datetime.timedelta(minutes=max(30, cook_mins))

            ing_text = "\n".join(f"• {i}" for i in recipe["ingredients"])
            method_text = "\n".join(f"{n+1}. {s}" for n, s in enumerate(recipe["method"]))

            # Build tonight's to-do note (shown on dinner event and lunch event)
            todo_lines = []

            # On dinner events: remind about tomorrow's lunch if it needs batch/prep
            if slot == "dinner" and tomorrow_plan:
                tmr_lunch = tomorrow_plan["lunch"]
                tmr_dinner = tomorrow_plan["dinner"]
                todo_lines.append("─── TONIGHT'S TO-DO LIST ───")
                todo_lines.append(f"🍱 Cook tonight's dinner: {recipe['name']} (~{recipe['cook_mins']} min)")
                if tmr_lunch.get("batch"):
                    todo_lines.append(f"📦 Batch cook for tomorrow's lunch: {tmr_lunch['name']} — make extra now if possible")
                else:
                    todo_lines.append(f"📋 Tomorrow's lunch: {tmr_lunch['name']} (~{tmr_lunch['cook_mins']} min to cook tomorrow)")
                # Flag any overnight prep needed (e.g. soaking beans)
                for ing in tmr_lunch.get("ingredients", []) + tmr_dinner.get("ingredients", []):
                    if "soaked overnight" in ing.lower() or "overnight" in ing.lower():
                        todo_lines.append(f"💧 Soak overnight: {ing.split('(')[0].strip()}")
                        break

            # On lunch events: remind what dinner is tonight
            if slot == "lunch":
                dinner_recipe = day_plan["dinner"]
                todo_lines.append("─── TONIGHT ───")
                todo_lines.append(f"🍽 Dinner: {dinner_recipe['name']} (~{dinner_recipe['cook_mins']} min)")
                if dinner_recipe['cook_mins'] > 45:
                    todo_lines.append(f"⏰ Long cook — start by {(19 - dinner_recipe['cook_mins'] // 60)}:{str(dinner_recipe['cook_mins'] % 60 or '00').zfill(2)} at latest")

            todo_block = ("\n\n📌 " + "\n".join(todo_lines)) if todo_lines else ""

            training_note = "\n🏋️ Training day — quick meal" if day_plan.get("training") and slot == "dinner" else ""
            description = (
                f"🫒 Jerusalem Meal Planner{training_note}\n\n"
                f"📋 {recipe['kcal']} kcal · {recipe['protein']}g protein · ~{cook_mins} min\n"
                f"{todo_block}\n\n"
                f"──────────────────\n"
                f"INGREDIENTS\n{ing_text}\n\n"
                f"METHOD\n{method_text}\n\n"
                f"TIP: {recipe['tip']}"
            )

            event = {
                'summary': f"{label}: {recipe['name']}",
                'description': description,
                'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/London'},
                'end':   {'dateTime': end_dt.isoformat(),   'timeZone': 'Europe/London'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': cook_mins + 30},  # start prep reminder
                        {'method': 'popup', 'minutes': 10},              # 10 min before eat
                    ]
                },
                'colorId': '2' if recipe['type'] == 'plant' else ('7' if recipe['type'] == 'fish' else '6')
            }
            try:
                result = service.events().insert(calendarId='primary', body=event).execute()
                created.append(result.get('htmlLink'))
                print(f"[sync] created {label} event for {day_plan['day']}", flush=True)
            except Exception as e:
                msg = f"{label} {day_plan['day']}: {e}"
                print(f"[sync] ERROR: {msg}", flush=True)
                traceback.print_exc()
                errors.append(msg)

    # Shopping reminder — Sunday before the week
    sunday_before = start_date - datetime.timedelta(days=1)
    shop_start = datetime.datetime.combine(sunday_before, datetime.time(10, 0))
    shop_end   = shop_start + datetime.timedelta(hours=1)

    # Flatten daily shopping into combined weekly list for Sunday reminder
    shopping_lines = []
    all_weekly = {}
    for day, day_cats in data.get('shopping', {}).items():
        for cat, items in day_cats.items():
            for item in items:
                k = item.lower().split("(")[0].strip()
                all_weekly.setdefault(cat, {})[k] = item
    for cat, items_dict in all_weekly.items():
        shopping_lines.append(f"\n{cat.upper()}")
        for item in sorted(items_dict.values()):
            shopping_lines.append(f"• {item}")

    # Sunday evening prep note for Monday
    monday_plan = plan[0] if plan else None
    sunday_prep = []
    if monday_plan:
        mon_lunch = monday_plan["lunch"]
        mon_dinner = monday_plan["dinner"]
        sunday_prep.append("\n─── SUNDAY EVENING PREP ───")
        sunday_prep.append(f"🍱 Monday lunch: {mon_lunch['name']}")
        if mon_lunch.get("batch"):
            sunday_prep.append("   → Batch cook tonight to save time tomorrow")
        sunday_prep.append(f"🍽 Monday dinner: {mon_dinner['name']} (~{mon_dinner['cook_mins']} min)")
        for ing in mon_lunch.get("ingredients", []) + mon_dinner.get("ingredients", []):
            if "soaked overnight" in ing.lower():
                sunday_prep.append(f"💧 Soak tonight: {ing.split('(')[0].strip()}")
                break

    shop_event = {
        'summary': '🛒 Weekly shop — Jerusalem Meal Planner',
        'description': "Shopping list for the week:\n" + "\n".join(shopping_lines) + "\n" + "\n".join(sunday_prep),
        'start': {'dateTime': shop_start.isoformat(), 'timeZone': 'Europe/London'},
        'end':   {'dateTime': shop_end.isoformat(),   'timeZone': 'Europe/London'},
        'reminders': {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': 60}]
        },
        'colorId': '5'
    }
    try:
        result = service.events().insert(calendarId='primary', body=shop_event).execute()
        created.append(result.get('htmlLink'))
        print("[sync] created weekly shopping event", flush=True)
    except Exception as e:
        msg = f"Weekly shopping event: {e}"
        print(f"[sync] ERROR: {msg}", flush=True)
        traceback.print_exc()
        errors.append(msg)

    print(f"[sync] done — created {len(created)}, errors {len(errors)}", flush=True)
    response = {"created": len(created), "deleted": deleted, "links": created}
    if errors:
        response["warnings"] = errors
    return jsonify(response)

# ─── ICLOUD REMINDERS SYNC ─────────────────────────────────────────────────────

@app.route('/api/sync_reminders', methods=['POST'])
def sync_reminders():
    if not ICLOUD_USER or not ICLOUD_PASSWORD:
        return jsonify({"error": "iCloud credentials not configured in app.py."}), 400

    data = request.json
    shopping = data.get('shopping', {})
    if not shopping:
        return jsonify({"error": "No shopping list to sync."}), 400

    try:
        import caldav
        from urllib.parse import urlparse

        # Connect directly to the known per-account iCloud CalDAV server.
        # ICLOUD_SERVER is discovered once and stored — Apple's generic gateway
        # (caldav.icloud.com) blocks writes, so we must use the real server.
        client = caldav.DAVClient(
            url=ICLOUD_SERVER,
            username=ICLOUD_USER,
            password=ICLOUD_PASSWORD,
        )
        print(f"[reminders] connecting to {ICLOUD_SERVER}...", flush=True)
        principal = client.principal()
        print(f"[reminders] principal ok", flush=True)

        # Find the target list
        calendars = principal.calendars()
        target = None
        print(f"[reminders] calendars found:", flush=True)
        for cal in calendars:
            name = cal.get_display_name()
            print(f"[reminders]   {name!r} — {cal.url}", flush=True)
            if name == REMINDERS_LIST:
                target = cal
                break

        if target is None:
            return jsonify({"error": f"Reminders list '{REMINDERS_LIST}' not found on iCloud. Create it manually in the Reminders app first."}), 400

        print(f"[reminders] found list: {REMINDERS_LIST} at {target.url}", flush=True)

    except Exception as e:
        print(f"[reminders] connection failed: {e}", flush=True)
        return jsonify({"error": f"Could not connect to iCloud: {e}"}), 500

    import uuid, datetime as _dt
    created = 0
    errors  = []
    DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for day in DAY_ORDER:
        day_cats = shopping.get(day, {})
        if not day_cats:
            continue
        for cat, items in day_cats.items():
            for item in items:
                uid = uuid.uuid4().hex
                now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                safe_item = item.replace("\n", " ").replace(",", "\\,")
                vtodo = (
                    "BEGIN:VCALENDAR\r\n"
                    "VERSION:2.0\r\n"
                    "PRODID:-//Jerusalem Meal Planner//EN\r\n"
                    "CALSCALE:GREGORIAN\r\n"
                    "BEGIN:VTODO\r\n"
                    f"UID:{uid}@jerusalem-planner\r\n"
                    f"DTSTAMP:{now}\r\n"
                    f"CREATED:{now}\r\n"
                    f"SUMMARY:{safe_item}\r\n"
                    f"DESCRIPTION:{day} - {cat}\r\n"
                    "STATUS:NEEDS-ACTION\r\n"
                    "END:VTODO\r\n"
                    "END:VCALENDAR\r\n"
                )
                try:
                    target.add_todo(vtodo)
                    created += 1
                except Exception as e:
                    errors.append(f"{day}/{item}: {e}")
                    print(f"[reminders] ERROR {day}/{item}: {e}", flush=True)

    print(f"[reminders] done — {created} items created, {len(errors)} errors", flush=True)
    response = {"created": created}
    if errors:
        response["warnings"] = errors
    return jsonify(response)


@app.route('/shopping')
def shopping_page():
    """Mobile-optimised shopping list page — open on iPhone, Share → Add to Notes."""
    shopping = session.get('shopping', {})
    DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    days = [(d, shopping.get(d, {})) for d in DAY_ORDER if shopping.get(d)]

    rows = []
    for day, cats in days:
        rows.append(f'<h2>{day}</h2>')
        for cat, items in cats.items():
            if not items: continue
            rows.append(f'<p class="cat">{cat}</p><ul>')
            for item in items:
                rows.append(f'<li><input type="checkbox"> {item}</li>')
            rows.append('</ul>')

    body = "\n".join(rows) if rows else "<p>No shopping list — generate a plan first.</p>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jerusalem Shopping List</title>
<style>
  body{{font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:16px;background:#f6f1e9;color:#1c1710}}
  h1{{font-family:Georgia,serif;font-size:24px;margin-bottom:4px;color:#1c1710}}
  .sub{{font-size:13px;color:#8a7a66;margin-bottom:20px}}
  h2{{font-size:17px;font-weight:600;margin:24px 0 6px;border-bottom:1px solid #e4d8c0;padding-bottom:4px;color:#1c1710}}
  .cat{{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#8a7a66;margin:12px 0 4px}}
  ul{{list-style:none;padding:0;margin:0}}
  li{{display:flex;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px solid #e4d8c0;font-size:15px}}
  li:last-child{{border-bottom:none}}
  input[type=checkbox]{{width:18px;height:18px;margin-top:2px;flex-shrink:0;accent-color:#6b7c4a}}
</style>
</head>
<body>
<h1>🫒 Jerusalem</h1>
<div class="sub">Weekly shopping list · Tap Share → Add to Notes to save offline</div>
{body}
</body>
</html>"""
    from flask import Response
    return Response(html, mimetype='text/html')


# ─── LAUNCH ────────────────────────────────────────────────────────────────────

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "localhost"
    finally:
        s.close()

if __name__ == '__main__':
    import socket
    ip = get_local_ip()
    print("\n🫒  Jerusalem Meal Planner")
    print("━" * 40)
    print(f"   PC:     http://localhost:5000")
    print(f"   iPhone: http://{ip}:5000")
    print("━" * 40)
    print("   Both must be on the same WiFi")
    print("   Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
