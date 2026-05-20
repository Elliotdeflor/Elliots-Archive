# 🫒 Jerusalem Meal Planner

A local web app that generates weekly meal plans from **Jerusalem** by Yotam Ottolenghi & Sami Tamimi, syncs events to Google Calendar, and produces a daily shopping list — all scaled for **1 person**.

---

## What it does

- **Generates a full week of meals** at the click of a button — lunch and dinner every day, drawn from 41 recipes in the Jerusalem cookbook
- **Matches your diet pattern**: 3–4 plant-based days, 2–3 fish days, 1 meat day per week
- **Respects your training schedule**: Tuesday, Wednesday and Friday are training days — dinners on those days are always ≤30 min, and a carb side is added
- **Every dinner includes a veg side** from the book (always shorter to cook than the main)
- **All recipes scaled to 1 serving** — ingredients, quantities and shopping list are all for one person
- **Full recipes on tap** — click any meal card to expand the complete ingredients list and method
- **Syncs to Google Calendar** — creates lunch and dinner events with the full recipe in the description, plus a Sunday shopping reminder
- **Per-day shopping list** — Monday to Sunday tabs, quantities scaled for 1, tick items off as you shop
- **Works on iPhone** — open the local IP address on your phone while on the same WiFi

---

## Nutrition targets

| | Amount |
|---|---|
| Daily calories | ~2000 kcal |
| Daily protein | ~150g |
| Cottage cheese (5% fat, 1 tub/day) | ~270 kcal · 28g protein |
| Egg whites (15/day) | ~255 kcal · 53g protein |
| From meals | remaining ~1475 kcal · ~70g protein |

---

## Setup

### 1. Install Python dependencies

```bash
cd jerusalem-app
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

You'll see:

```
🫒  Jerusalem Meal Planner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   PC:     http://localhost:5000
   iPhone: http://192.168.x.x:5000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Open the PC URL in your browser. Open the iPhone URL on your phone (both must be on the same WiFi).

### 3. Set up Google Calendar (one-time, ~5 minutes)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g. "Meal Planner")
3. **APIs & Services → Library** → search **Google Calendar API** → Enable
4. **APIs & Services → OAuth consent screen**
   - Choose **External** → Create
   - Fill in app name and your email → Save
   - On Test Users, add your Gmail address
5. **APIs & Services → Credentials**
   - **+ Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Under **Authorised redirect URIs**, add: `http://localhost:5000/auth/callback`
   - Click Create → Download JSON
6. Rename the downloaded file to **`credentials.json`**
7. Move it into the `jerusalem-app/` folder (same folder as `app.py`)

Then click **Connect Google Calendar** in the app and sign in. A `token.pickle` file saves your login — you won't need to sign in again.

---

## Using the app

### Generate a week
Click **✦ Generate week** — a full 7-day plan is created instantly from the recipe pool.

### Browse meals
Use the **Mon → Sun** tabs to browse each day. Each day shows:

| Card | Shown when? |
|---|---|
| Lunch | Always |
| Dinner — main | Always |
| Vegetable side | Always |
| Carb side | Training days only (Tue/Wed/Fri) |

Click any card to expand the **full recipe** — ingredients scaled to 1 serving, step-by-step method, and a tip from the book.

### Shopping list
Click the **🛒 Shopping** tab. Use the day tabs (Mon→Sun) to see what to buy each day, quantities scaled for 1 person. Tick items off as you shop.

### Sync to Google Calendar
1. Pick your week's start date (defaults to next Monday)
2. Click **📅 Sync to Google Calendar**

What gets created:
- **14 meal events** — lunch at 12:00, dinner at 19:00, colour-coded by type
  - 🟢 Green = plant-based · 🔵 Blue = fish · 🔴 Red = meat
- **Full recipe in each event description** — open the event on your phone for the complete recipe
- **Cook-time reminders** on every event
- **Tonight's to-do list** in each dinner event — what to cook, whether to prep tomorrow's lunch, overnight soaks if needed
- **🏋️ Training day note** on Tue/Wed/Fri dinner events
- **Sunday shopping reminder** at 10:00am with the full weekly shopping list

---

## Recipe list

### Plant-based (8)
| Recipe | Time |
|---|---|
| Mejadra | 45 min |
| Shakshuka | 25 min ⚡ |
| Chermoula Eggplant with Bulgur & Yogurt | 50 min |
| Conchiglie with Yogurt, Peas & Chilli | 25 min ⚡ |
| Barley Risotto with Marinated Feta | 55 min |
| Musabaha — Warm Chickpeas with Hummus | 20 min ⚡ |
| Falafel | 30 min |
| Sabih | 35 min |

### Fish (9)
| Recipe | Time |
|---|---|
| Salmon in Chraimeh Sauce | 35 min |
| Panfried Sea Bass with Harissa & Rose | 30 min ⚡ |
| Mackerel with Golden Beet & Orange Salsa | 30 min ⚡ |
| Fish & Caper Kebabs with Burnt Eggplant | 45 min |
| Grilled Salmon with Zhoug & Tabbouleh | 20 min ⚡ |
| Cod Cakes in Tomato Sauce | 45 min |
| Grilled Fish Skewers with Hawayej | 20 min ⚡ |
| Marinated Sweet & Sour Fish | 40 min |
| Prawns, Scallops & Clams with Tomato & Feta | 30 min ⚡ |

### Meat & Chicken (15)
| Recipe | Time |
|---|---|
| Cannellini Bean & Lamb Soup | 90 min |
| Lamb Meatballs with Barberries, Yogurt & Herbs | 100 min |
| Turkey & Courgette Burgers with Sumac Yogurt | 30 min ⚡ |
| Chicken with Caramelised Onion & Cardamom Rice | 60 min |
| Roasted Chicken with Clementines & Arak | 55 min |
| Poached Chicken with Sweet Spiced Freekeh | 100 min |
| Maqluba — Upside-Down Chicken & Rice | 90 min |
| Kofta B'siniyah | 35 min |
| Braised Eggs with Lamb, Tahini & Sumac | 35 min |
| Spicy Freekeh Soup with Meatballs | 55 min |
| Hummus Kawarma with Lemon Sauce | 30 min ⚡ |
| Roasted Chicken with Jerusalem Artichoke & Lemon | 60 min |
| Lamb Shawarma | 270 min (slow roast) |
| Beef Meatballs with Fava Beans & Lemon | 40 min |
| Open Kibbeh | 55 min |

### Vegetable sides (always served with dinner)
| Side | Time |
|---|---|
| Tabbouleh | 15 min |
| Charred Okra with Tomato & Preserved Lemon | 20 min |
| Swiss Chard with Tahini, Yogurt & Pine Nuts | 20 min |
| Spicy Carrot Salad | 35 min |
| Roasted Cauliflower & Hazelnut Salad | 40 min |

### Carb sides (training days only: Tue/Wed/Fri)
| Side | Time |
|---|---|
| Warm Pitta Bread | 5 min |
| Plain Basmati Rice | 20 min |
| Couscous with Tomato & Onion | 25 min |
| Basmati & Wild Rice with Chickpeas & Herbs | 50 min |

---

## Troubleshooting

**"credentials.json not found"**
Make sure the file is in the `jerusalem-app/` folder alongside `app.py`.

**Google sign-in says "app not verified"**
Click **Advanced** then **Go to Meal Planner (unsafe)**. Normal for personal apps not submitted for Google review.

**`invalid_grant` error during Google sign-in**
Delete `token.pickle` if it exists and try connecting again. The app uses a direct HTTP token exchange to avoid PKCE errors.

**iPhone can't connect**
Make sure PC and iPhone are on the same WiFi. Try allowing Python through your PC firewall, or temporarily disabling it.

**Events showing wrong timezone**
Open `app.py`, search for `'timeZone': 'Europe/London'` and change both instances to your timezone, e.g. `'Europe/Manchester'`.

---

## Project structure

```
jerusalem-app/
├── app.py              # Flask server — recipes, meal generation, Google Calendar sync
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── credentials.json    # Google OAuth credentials (you create this — not in repo)
├── token.pickle        # Saved Google login (auto-created after first sign-in)
└── templates/
    └── index.html      # Full frontend — UI, recipe cards, shopping list
```

---

## Notes

- The app runs entirely locally — no data leaves your machine except to Google Calendar when you click Sync
- `token.pickle` stores your Google login token — keep it private
- All recipes are from **Jerusalem** by Yotam Ottolenghi & Sami Tamimi (Ten Speed Press, 2012)
- Ingredient quantities are scaled to 1 serving; methods describe the full recipe as written in the book
