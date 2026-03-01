import streamlit as st
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt

st.set_page_config(page_title="Plant Health Checker", layout="centered")

def apply_global_styles(): 
 st.markdown(
    """
    <style>
  /* App Background */
    .stApp {
        background: linear-gradient(135deg, #2F4F3E, #6B8F71);
        background-attachment: fixed;
    }

    /* Main content card */
    .block-container {
        background-color: rgba(255, 253, 247, 0.92);
        border-radius: 18px;
        padding: 2rem;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.18);
    }

    /* Title */
    h1 {
        color: #2F4F3E;
        text-align: center;
        font-weight: 700;
    }

    /* Section headers */
    h2, h3 {
        color: #556B2F;
    }

    /* Normal text */
    p, li, span {
        color: #2F4F3E;
    }

    /* Buttons */
    .stButton>button {
        background-color: #E3B23C;
        color: #2F4F3E;
        border-radius: 10px;
        border: none;
        font-weight: bold;
        padding: 0.5rem 1.2rem;
    }

    .stButton>button:hover {
        background-color: #F1C453;
        color: #2F4F3E;
    }

    /* File uploader */
    .stFileUploader {
        background-color: #FFF7E6;
        border-radius: 12px;
        padding: 1rem;
        border: #E3B23C;
    }

    /* Info / warning boxes */
    .stAlert {
        border-radius: 12px;
    }

    footer {
        visibility: hidden;
    }
    
    unsafe_allow_html=True

    </style>
    """,
    unsafe_allow_html=True
)

apply_global_styles()
st.title("The Gardner") 


col1, col2 = st.columns(2)

with col1:
    if st.button("Plant List"):
        st.write("Navigate to Plant List")  

with col2:
    if st.button("Plant Health Checker"):
        st.write("Navigate to Plant Health Checker")  
    
st.title("Plant Health Checker")
st.write(
    "Upload a leaf photo. This app estimates **Green / Yellow / Brown** areas, adds **spot + edge-damage** cues, "
    "and gives a more detailed analysis with suggestions."
)



def to_bgr(pil_img: Image.Image) -> np.ndarray:
    """Convert PIL RGB image to OpenCV BGR numpy array."""
    rgb = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def segment_leaf_hsv(bgr: np.ndarray) -> np.ndarray:
    
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Green range
    green = cv2.inRange(hsv, np.array([25, 30, 30]), np.array([95, 255, 255]))

    # Yellow range (chlorosis)
    yellow = cv2.inRange(hsv, np.array([10, 25, 40]), np.array([35, 255, 255]))

    # Brown/dry range (lower value, lower saturation sometimes)
    # Brown can be tricky: this is a broad heuristic.
    brown1 = cv2.inRange(hsv, np.array([0, 20, 10]),  np.array([25, 255, 140]))
    brown2 = cv2.inRange(hsv, np.array([160, 20, 10]), np.array([179, 255, 140]))  # catch reddish-brown edge cases

    mask = cv2.bitwise_or(green, yellow)
    mask = cv2.bitwise_or(mask, brown1)
    mask = cv2.bitwise_or(mask, brown2)

    # Clean up noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    sv_mask = ((s > 25) & (v > 25)).astype(np.uint8) * 255

    mask = cv2.bitwise_or(mask, sv_mask)


    return mask



def color_scores(bgr: np.ndarray, leaf_mask: np.ndarray) -> dict:
    
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    leaf_pixels = leaf_mask > 0
    total = int(np.sum(leaf_pixels))

    if total < 500:  # too few pixels -> probably bad segmentation
        return {"green": 0.0, "yellow": 0.0, "brown": 0.0, "total_leaf_pixels": total}

    # Green
    green_mask = cv2.inRange(hsv, np.array([35, 40, 40]), np.array([85, 255, 255])) > 0

    # Yellow
    yellow_mask = cv2.inRange(hsv, np.array([15, 40, 60]), np.array([35, 255, 255])) > 0

    # Brown
    brown_mask = cv2.inRange(hsv, np.array([5, 40, 20]), np.array([25, 255, 120])) > 0

    
    green = int(np.sum(green_mask & leaf_pixels))
    yellow = int(np.sum(yellow_mask & leaf_pixels))
    brown = int(np.sum(brown_mask & leaf_pixels))

    return {
        "green": 100.0 * green / total,
        "yellow": 100.0 * yellow / total,
        "brown": 100.0 * brown / total,
        "total_leaf_pixels": total,
    }


def health_label(scores: dict) -> tuple[str, str]:
    
    g, y, b = scores["green"], scores["yellow"], scores["brown"]
    stress = y + b

    if scores["total_leaf_pixels"] < 500:
        return ("Unknown", "Couldn’t detect enough leaf area. Try a closer photo with a plain background.")

    if g >= 45 and stress <= 12:
        return ("Healthy", f"High green ({g:.1f}%) and low yellow/brown ({stress:.1f}%).")
    if g >= 30 and stress <= 25:
        return ("Mild Stress", f"Moderate green ({g:.1f}%) and some yellow/brown ({stress:.1f}%).")
    return ("Stressed", f"Low green ({g:.1f}%) and/or high yellow/brown ({stress:.1f}%).")


def overlay_mask(bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
    overlay = bgr.copy()
    color = (0, 255, 0)  # green overlay
    overlay[mask > 0] = (0.6 * overlay[mask > 0] + 0.4 * np.array(color)).astype(np.uint8)
    return overlay


def spot_score(bgr: np.ndarray, leaf_mask: np.ndarray) -> float:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    leaf = cv2.bitwise_and(gray, gray, mask=leaf_mask)

    blur = cv2.GaussianBlur(leaf, (5, 5), 0)
    lap = cv2.Laplacian(blur, cv2.CV_64F)
    lap_abs = np.abs(lap)

    vals = lap_abs[leaf_mask > 0]
    if vals.size < 500:
        return 0.0

    thr = np.percentile(vals, 90)  # adaptive threshold
    spotty = np.mean(vals > thr)
    return float(np.clip(spotty * 100.0, 0, 100))


def edge_damage_score(leaf_mask: np.ndarray) -> float:
    
    mask = (leaf_mask > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perim = cv2.arcLength(c, True)
    if area < 500:
        return 0.0

    ratio = perim / (area ** 0.5)  # scale-ish invariant
    score = (ratio - 12) * 8       # map to 0-100-ish
    return float(np.clip(score, 0, 100))


def confidence_score(scores: dict) -> str:
    
    total = scores["total_leaf_pixels"]
    if total >= 60000:
        return "High"
    if total >= 15000:
        return "Medium"
    return "Low"


def detailed_report(scores: dict, spot: float, edge: float, label: str, conf: str) -> tuple[str, list]:
    """
    Returns (analysis_text, suggestions_list)
    """
    g, y, b = scores["green"], scores["yellow"], scores["brown"]
    stress = y + b

    analysis_bits = []
    analysis_bits.append(f"**Confidence:** {conf} (detected leaf pixels: {scores['total_leaf_pixels']})")
    analysis_bits.append(f"**Color breakdown:** Green {g:.1f}%, Yellow {y:.1f}%, Brown {b:.1f}%")
    analysis_bits.append(f"**Texture cues:** Spot score {spot:.0f}/100, Edge damage {edge:.0f}/100")

    if y > 18 and b < 8:
        analysis_bits.append(
            "**Pattern:** Mostly yellowing (chlorosis) with low browning - often early stress "
            "(watering/light) or nutrient imbalance."
        )
    if b > 12:
        analysis_bits.append(
            "**Pattern:** Noticeable browning/necrosis - tissue damage (over/under-watering, sun scorch, or infection)."
        )
    if spot > 35:
        analysis_bits.append(
            "**Pattern:** High spotty texture - could indicate leaf-spotting, mildew patterns, or pest speckling "
            "(needs a close visual check)."
        )
    if edge > 35:
        analysis_bits.append("**Pattern:** Irregular edge signal - could be chewing/tearing (pests or physical damage).")

    analysis_text = "\n\n".join(analysis_bits)

    tips = []

    if conf == "Low":
        tips.append(
            "Retake photo: place a single leaf on plain white paper, in daylight, fill the frame, avoid shadows, "
            "and include the underside if possible."
        )

    if "Healthy" in label:
        tips.append("Keep routine consistent: stable watering and steady light (avoid sudden changes).")
        tips.append("Preventative check: look under leaves weekly for pests; wipe dust so leaves can photosynthesize well.")
        if spot > 35:
            tips.append("Even if color looks good, the spot score is high—zoom in to confirm if it’s just texture/veins.")
    else:
        if y > b and y > 15:
            tips.append(
                "Yellowing is high: check watering first. If soil stays wet for days → water less / improve drainage. "
                "If soil becomes bone-dry - water more consistently."
            )
            tips.append(
                "Light check: too little light can cause yellowing. Move closer to a window gradually "
                "(avoid sudden direct sun)."
            )

        if b > 12:
            tips.append(
                "Browning/necrosis: trim severely damaged leaves (sterilize scissors) and avoid wetting leaves at night."
            )
            tips.append(
                "If browning is crispy near edges → underwatering/low humidity. If browning is dark/mushy - overwatering/root stress."
            )

        if spot > 35:
            tips.append(
                "Spotty pattern: isolate the plant and improve airflow. Avoid overhead watering; remove the worst leaves if spots spread."
            )
            tips.append(
                "Close-up check: powdery film - mildew; tiny moving dots/webbing - mites; raised bumps - scale/aphids."
            )

        if edge > 35:
            tips.append(
                "Edge damage signal: inspect underside and nearby soil/pot rim for chewing pests (caterpillars/snails). "
                "Check at night if possible."
            )
            tips.append("Quick action: rinse leaves, wipe undersides, and use insecticidal soap if pests are confirmed (test 1 leaf first).")

        if y > 18 and conf != "Low":
            tips.append(
                "If watering and light seem fine, consider nutrients: a balanced fertilizer at half-strength every 2–4 weeks (during growing season)."
            )

        
        tips.append("Priority order: **1) Watering**, **2) Light**, **3) Pests**, **4) Nutrients**.")

    return analysis_text, tips


# ----------------------------
# UI
# ----------------------------
uploaded = st.file_uploader("Upload a leaf image (JPG/PNG)", type=["jpg", "jpeg", "png"])
st.caption("Use daylight, fill the frame with the leaf, and place it on a plain white/black background.")

if uploaded:
    pil_img = Image.open(uploaded)
    bgr = to_bgr(pil_img)

    # Resize huge images for speed
    h, w = bgr.shape[:2]
    if max(h, w) > 1200:
        scale = 1200 / max(h, w)
        bgr = cv2.resize(bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    leaf_mask = segment_leaf_hsv(bgr)
    scores = color_scores(bgr, leaf_mask)
    label, explanation = health_label(scores)

    
    spot = spot_score(bgr, leaf_mask)
    edge = edge_damage_score(leaf_mask)
    conf = confidence_score(scores)
    analysis_text, tips = detailed_report(scores, spot, edge, label, conf)

    st.subheader("Result")
    st.write(f"**{label}**")
    st.caption(explanation)

    col1, col2 = st.columns(2)
    with col1:
        st.image(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), caption="Original", use_container_width=True)
    with col2:
        ov = overlay_mask(bgr, leaf_mask)
        st.image(cv2.cvtColor(ov, cv2.COLOR_BGR2RGB), caption="Detected leaf area in the uploded image", use_container_width=True)

    st.subheader("Scores")
    st.write(f"- Green: **{scores['green']:.1f}%**")
    st.write(f"- Yellow: **{scores['yellow']:.1f}%**")
    st.write(f"- Brown: **{scores['brown']:.1f}%**")
    st.write(f"- Spot score: **{spot:.0f}/100**")
    st.write(f"- Edge damage: **{edge:.0f}/100**")
    st.write(f"- Confidence: **{conf}**")

    
    fig = plt.figure()
    labels_ = ["Green", "Yellow", "Brown"]
    values_ = [scores["green"], scores["yellow"], scores["brown"]]
    plt.bar(labels_, values_, color="#6B8F71")
    plt.ylim(0, 100)
    plt.ylabel("Percent of detected leaf area")
    st.pyplot(fig)

    
    fig2 = plt.figure()
    plt.bar(["Spot score", "Edge damage"], [spot, edge], color="#6B8F71")
    plt.ylim(0, 100)
    plt.ylabel("Score (0–100)")
    st.pyplot(fig2)

    st.subheader("Detailed analysis")
    st.markdown(analysis_text)

    st.subheader("Suggestions")
    for i, t in enumerate(tips, 1):
        st.write(f"{i}. {t}")

else:
    st.info("Upload an image")


apply_global_styles()

# Initialize page state
if "page" not in st.session_state:
    st.session_state.page = "plant_list"

# ---------------------------
# Data
# ---------------------------
PlantFriends = [
    {"id": 1, "name": "Pothos", "funfact": "Nicknamed the 'Money Plant' in some cultures"},
    {"id": 2, "name": "Snake Plant", "funfact": "Produces oxygen at night"},
    {"id": 3, "name": "Peace Lily", "funfact": "Those white flowers are actually leaves"},
    {"id": 4, "name": "Spider Plant", "funfact": "Test subject in NASA's clean air studies"},
]


# ---------------------------
# Plant List Page
# ---------------------------
def plant_list_page():
    st.title("Plant List")

    if st.button("Home"):
        st.write("Navigate to Home screen")  # Replace with your actual navigation

    for i, plant in enumerate(PlantFriends):
        st.markdown("---")  # Separator

        # Plant info
        st.subheader(plant["name"])
        st.write(plant["funfact"])

        # Button to view care guide
        if st.button(f"View {plant['name']} Care Guide", key=f"btn_{plant['id']}"):
            st.session_state.page = plant["name"].lower().replace(" ", "_")

# ---------------------------
# Pothos Care Guide Page
# ---------------------------
def pothos_page():
    st.title("Pothos")
    st.write("This is the Pothos plant page.")
    

    st.header("Pothos Care Guide")
    st.markdown("""
**Light Best:** Bright, indirect light Tolerates: Low light (growth will slow) 
                Avoid: Direct afternoon sun (can scorch leaves) 
                Oregon tip: Place near an east- or north-facing window, or a few feet back from south-facing windows, especially in winter
                
**Light Levels:** 500 to 2,000 lux ideal 
                
                200 to 500 lux survives,

          slower growth less than 200 lux leggy growth Direct sun leaf burn  
                
**Water:** Water when the top 1 to 2 inches of soil are dry Typically:
          Spring/Summer: Every 7 to 10 days 
                
                Fall/Winter: Every 10 to 14 days

          Always let excess water drain out 
                
                Oregon tip: Cooler temps = slower

          drying → dont overwater, especially in winter.  
                
                Soil Moisture Reading Soil Condition Typical Reading 

                Completely dry 800 to 950 

                Dry (needs water) 650 to 800 

                Well-watered (ideal) 350 to 550 (Target: ~400 to 500) 

                Very wet / soggy 250 to 350
                
**Temperature:** Ideal 65 to 85°F (18 to 29°C) 
                
            Minimum: 55°F (13°C) Keep away from cold drafts and windows in winter 
                
        Temperature Reading Condition Ideal Range 
                
            Daytime 65 to 80 °F (18 to 27 °C) 
                
            Nighttime 60 to 70 °F (16 to 21 °C) 
                
            Stress below less than 55 °F (13 °C)
                
**Humidity** refers moderate humidity Oregon homes are usually fine If
          air is dry (heated homes in winter), mist occasionally or use a pebble
          tray  
        Humidity Reading Level Effect on Pothos 
                
        40 to 60 % RH Healthy (ideal)
                
          60 to 70 % RH Excellent growth 
                
        less than 40 % RH Brown tips may appear
                
          greater than 75 % RH OK, but watch airflow
                
**Soil** Well-draining indoor potting mix Optional improvement: Add
          perlite or orchid bark for drainage  Pot & Drainage Use a pot with drainage holes Repot every 1 to 2 years
          or when root-bound Fertilizer Feed monthly in spring and summer Use a balanced houseplant
          fertilizer at ½ strength Skip fertilizing in fall and winter  Pruning & Maintenance Trim leggy vines to encourage bushier growth
          Remove yellow or damaged leaves Wipe leaves occasionally to remove
          dust 
                
**Pests* (Rare but possible) Watch for spider mites, mealybugs, fungus
          gnats Treat with neem oil or insecticidal soap if needed  Pet Safety Toxic to cats and dogs if ingested Keep out of reach of
          pets 
""")
    if st.button("Back to Plant List"):
        st.session_state.page = "plant_list"
     
 # ---------------------------
# Snake Plant Care Guide Page
# ---------------------------
    if st.button("Back to Plant List"):
        st.session_state.page = "plant_list"

def snakeplant_page():
    st.title("Snake Plant")
    st.write("This is the Snake Plant page.")

    st.header("Snake Plant Care Guide")
    st.markdown("""
**Light Best:** Bright, indirect light Tolerates: Low light (very adaptable)
Avoid: Intense direct afternoon sun (can scorch leaves)
Oregon tip: Does well near east-, north-, or even south-facing windows. In darker winter months, place closer to windows for stronger growth.
                
**Light Levels**
Ideal: 500 to 2,000 lux
                
Survives: 200 to 500 lux (very slow growth)
                
Less than 200 lux: May survive but growth nearly stops
                
Direct sun: Leaf scorch or yellowing
                
**Water**
Water only when soil is completely dry (Snake plants prefer drought over excess moisture).
Typically:
Spring/Summer: Every 2 to 3 weeks
Fall/Winter: Every 3 to 5 weeks
Always let excess water drain out. Never let sit in standing water.
Oregon tip: Cooler temps + low light = very slow drying. Overwatering is the #1 cause of root rot, especially in winter.
                
**Soil Moisture Reading**
Soil Condition	Typical Reading
                
Completely dry	800 to 950
                
Dry (ready to water)	750 to 900
                
Lightly moist (acceptable)	500 to 700
                
Wet / too moist	250 to 450
                
(Target before watering: 750+)
                
**Temperature**
Ideal: 65 to 85°F (18 to 29°C)
                
Minimum: 50°F (10°C)
                
Keep away from cold drafts and freezing windows.
                
**Temperature Reading Condition**
Daytime Ideal: 65 to 80°F (18 to 27°C)
                
Nighttime Ideal: 60 to 70°F (16 to 21°C)
                
Stress: Below 50°F (10°C)
                
**Humidity**
Prefers low to moderate humidity. Very tolerant of dry indoor air.
Oregon homes are usually perfect — no extra humidity needed.
                
**Humidity Reading Level**
30 to 60% RH: Ideal
                
Less than 30% RH: Still tolerates well
                
Greater than 70% RH: OK, but ensure good airflow to prevent fungal issues
                
**Soil**
Well-draining indoor potting mix.
Best option: Cactus or succulent mix.
Optional improvement: Add extra perlite or pumice for faster drainage.
                
**Pot & Drainage**
Always use a pot with drainage holes.
Terracotta pots are excellent (help soil dry faster).
Repot every 2 to 3 years or when root-bound.
                
**Fertilizer**
Feed lightly once a month in spring and summer.
Use a balanced houseplant fertilizer at ½ strength.
Do not fertilize in fall and winter.
Overfertilizing can cause leaf burn.
                
**Pruning & Maintenance**
Remove damaged or yellowing leaves at the base.
Wipe leaves occasionally to remove dust.
Rotate plant every few months for even growth.
                
**Pests (Uncommon)**
Watch for:
Spider mites
Mealybugs
Fungus gnats (usually from overwatering)
Treat with neem oil or insecticidal soap if needed.
                
**Pet Safety**
Toxic to cats and dogs if ingested.
Keep out of reach of pets.
""")
    if st.button("Back to Plant List"):
        st.session_state.page = "plant_list"


# ---------------------------
# Page Routing
# ---------------------------
if st.session_state.page == "plant_list":
    plant_list_page()
elif st.session_state.page == "pothos":
    pothos_page()
elif st.session_state.page == "snakeplant":
    snakeplant_page() 
