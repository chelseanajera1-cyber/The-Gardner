import streamlit as st
from PIL import Image
from styles import apply_global_styles 

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

Plantpics = [
    "pothos.webp",
    "snakeplant.webp",
    "peacelily.jpg",
    "spiderplant.webp",
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

        # Plant image
        if i < len(Plantpics):
            img = Image.open(Plantpics[i])
            st.image(img, use_container_width=True)

        # Button to view care guide
        if st.button(f"View {plant['name']} Care Guide", key=f"btn_{plant['id']}"):
            st.session_state.page = plant["name"].lower().replace(" ", "_")

# ---------------------------
# Pothos Care Guide Page
# ---------------------------
def pothos_page():
    st.title("Pothos")
    st.write("This is the Pothos plant page.")
    
    img = Image.open("assets/8fea0a31af9f6992501385a62e8e1675.jpg.webp")
    st.image(img, use_container_width=True)

    st.header("Pothos Care Guide")
    st.markdown("""
**Light Best:** Bright, indirect light Tolerates: Low light (growth will
          slow) Avoid: Direct afternoon sun (can scorch leaves) Oregon tip:
          Place near an east- or north-facing window, or a few feet back from
          south-facing windows, especially in winter
**Light Levels:** 500 to 2,000 lux ideal 200 to 500 lux survives,
          slower growth less than 200 lux leggy growth Direct sun leaf burn  
**Water:** Water when the top 1 to 2 inches of soil are dry Typically:
          Spring/Summer: Every 7 to 10 days Fall/Winter: Every 10 to 14 days
          Always let excess water drain out Oregon tip: Cooler temps = slower
          drying → dont overwater, especially in winter.  Soil Moisture Reading Soil Condition Typical Reading Completely dry
          800 to 950 Dry (needs water) 650 to 800 Well-watered (ideal) 350 to
          550 (Target: ~400 to 500) Very wet / soggy 250 to 350
**Temperature:** Ideal 65 to 85°F (18 to 29°C) Minimum: 55°F (13°C) Keep
          away from cold drafts and windows in winter Temperature Reading
          Condition Ideal Range Daytime 65 to 80 °F (18 to 27 °C) Nighttime 60
          to 70 °F (16 to 21 °C) Stress below less than 55 °F (13 °C)
**Humidity** refers moderate humidity Oregon homes are usually fine If
          air is dry (heated homes in winter), mist occasionally or use a pebble
          tray  Humidity Reading Level Effect on Pothos 40 to 60 % RH Healthy (ideal)
          60 to 70 % RH Excellent growth less than 40 % RH Brown tips may appear
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
# Page Routing
# ---------------------------
if st.session_state.page == "plant_list":
    plant_list_page()
elif st.session_state.page == "pothos":
    pothos_page()
